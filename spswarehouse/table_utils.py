import pandas as pd
from pandas.api.extensions import no_default

import numpy as np
import os
import random
import string

from .warehouse import Warehouse
from .googledrive import GoogleDrive
from config import DEFAULT_ENCODING


# Copied from https://stackoverflow.com/questions/40774787/renaming-columns-in-a-pandas-dataframe-with-duplicate-column-names
# guess_col_types will break if you have duplicate column names
class renamer():
    def __init__(self):
        self.d = dict()

    def __call__(self, x):
        if x not in self.d:
            self.d[x] = 0
            return x
        else:
            self.d[x] += 1
            return "%s_%d" % (x, self.d[x])

def sanitize_string(name):
    if name == '':
        name = 'no_col_name_or_merged_column_header'
    elif name[0].isdigit():
        name = '_' + name
    return name.translate(
        {ord(c): "_" for c in "'""→!@#$%^&*()[]{};:,./<>?\|`~-=_+ \n"}
    )

def guess_col_types(df):
    """
    guess_col_types: pandas.DataFrame -> {column name: column type}

    You should use only these types (without exceptions!)
        BOOLEAN
        DATE
        FLOAT (this is a double precision floating point number)
        INTEGER (this is a 64-bit int)
        VARCHAR (this covers all strings up to 16MB)
        TIMESTAMP WITHOUT TIME ZONE
        VARIANT (json type)
        ARRAY
        NUMERIC(precision, scale) (you MUST provide both arguments if you use this type)
    """
    data_types = {
        np.dtype('int64'): 'INTEGER',
        np.dtype('O'): 'VARCHAR',
        np.dtype('float64'): 'FLOAT',
        np.dtype('bool'): 'BOOLEAN',
        np.dtype('<M8[ns]'): 'DATE',
    }

    col_types = {}

    for col_name in df.columns:
        guess = 'unknown'
        if col_name.lower() == 'as_of':
            guess = 'DATE'
        elif df.dtypes[col_name] in data_types:
            guess = data_types[df.dtypes[col_name]]
        col_types[col_name.lower()] = guess

    return col_types

def create_table_stmt(
    table_name,
    schema,
    comment='',
    # We'll use "columns" as-is
    columns=None, # {column name: column type}
    encoding=DEFAULT_ENCODING, # text encoding, e.g. 'utf-8' or 'latin-1'
    # We'll try to guess what the column types are if you pass in one of the rest
    dataframe=None, # pandas.DataFrame
    csv_filename=None, # string
    google_sheet=None, # gspread.models.Worksheet
    google_drive_id=None, #string
    force_string=False, # boolean
    sep=no_default, # string - if not using comma as separator
):
    # Column names and types explicitly specified, use them as-is
    if columns is not None:
        return _create_table_stmt(table_name, schema, columns, comment)

    # Convert everything to a dataframe and try to guess column types
    df = None
    if dataframe is not None:
        if force_string:
            df = dataframe.astype(str)
        else:
            df = dataframe
    elif google_sheet is not None:
        if force_string:
            google_sheet_values = google_sheet.get_all_values()
            df = pd.DataFrame(google_sheet_values[1:],columns=google_sheet_values[0], dtype=str)
        else:
            df = pd.DataFrame(google_sheet.get_all_records())
    elif csv_filename is not None:
        if force_string:
            df = pd.read_csv(csv_filename, encoding=encoding, dtype=str, sep=sep)
        else:
            df = pd.read_csv(csv_filename, encoding=encoding, sep=sep)
    elif google_drive_id is not None:
        letters = string.ascii_letters
        filename = ''.join(random.choice(letters) for i in range(10)) + '.csv'
        tempFile = GoogleDrive.CreateFile({'id': google_drive_id})
        tempFile.GetContentFile(filename)
        try:
            if force_string:
                df = pd.read_csv(filename, encoding=encoding, dtype=str, sep=sep)
            else:
                df = pd.read_csv(filename, encoding=encoding, sep=sep)
        except Exception as error:
            raise error
        finally:
            os.remove(filename)
    else:
        raise

    df = sanitize_columns_for_upload(df)
    df = df.rename(columns=renamer())
    
    return _create_table_stmt(
        table_name,
        schema,
        guess_col_types(df),
        comment,
    )

def _create_table_stmt(table_name, schema, col_types, comment):
    return "CREATE TABLE {schema}.{table_name} ({cols}) COMMENT = '{comment}'".format(
        schema=schema,
        table_name=table_name,
        cols=', '.join([(name + ' ' + tipe) for name, tipe in col_types.items()]),
        comment=comment,
    )

def sanitize_columns_for_upload(dataframe):
    '''
    sanitize_df_for_upload: pandas.DataFrame -> pandas.DataFrame

    Creates a dataframe from a CSV file and sanitizes column names.
    '''
    # Overwrite column names with sanitized versions, by substituting _ for
    # special characters
    dataframe.columns = list(map(sanitize_string, list(dataframe.columns)))
    return dataframe