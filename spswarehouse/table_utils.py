import pandas as pd
import numpy as np

from .credentials import snowflake_config
from .warehouse import Warehouse

ENCODING='utf-8'
DEFAULT_BATCH_SIZE=200

def sanitize_string(name):
    return name.translate(
        {ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+ "}
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
    schema=snowflake_config['schema'],
    comment='',
    # We'll use "columns" as-is
    columns=None, # {column name: column type}
    # We'll try to guess what the column types are if you pass in one of the rest
    dataframe=None, # pandas.DataFrame
    csv_filename=None, # string
    google_sheet=None, # gspread.models.Worksheet
):
    # Column names and types explicitly specified, use them as-is
    if columns is not None:
        return _create_table_stmt(table_name, schema, columns, comment)

    # Convert everything to a dataframe and try to guess column types
    df = None
    if dataframe is not None:
        df = dataframe
    elif google_sheet is not None:
        df = pd.DataFrame(google_sheet.get_all_records())
    elif csv_filename is not None:
        df = pd.read_csv(csv_filename, encoding=ENCODING)
    else:
        raise

    df = _sanitize_columns_for_upload(df)

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

def _sanitize_columns_for_upload(dataframe):
    '''
    sanitize_df_for_upload: pandas.DataFrame -> pandas.DataFrame

    Creates a dataframe from a CSV file and sanitizes column names.
    '''
    # Overwrite column names with sanitized versions, by substituting _ for
    # special characters
    dataframe.columns = list(map(sanitize_string, list(dataframe.columns)))
    return dataframe

def upload_to_warehouse(
    reflected_table,
    # Data
    dataframe=None,
    csv_filename=None,
    google_sheet=None,
    # Range
    start_index=0,
    end_index=None,
    batch_size=DEFAULT_BATCH_SIZE,
):
    df = None
    if dataframe is not None:
        df = dataframe
    elif google_sheet is not None:
        df = pd.DataFrame(google_sheet.get_all_records())
    elif csv_filename is not None:
        df = pd.read_csv(csv_filename, encoding=ENCODING)
    else:
        raise

    _upload_df(reflected_table, df, start_index, end_index, batch_size)

def _upload_df(
    reflected_table,
    df,
    start_index,
    end_index,
    batch_size,
):
    '''
    upload_df: SqlAlchemy Table, pandas Dataframe -> void

    Uploads a pandas.DataFrame to specified table.
    If specified, uploads the range [start_index, end_index).

    Assumes that the table you're uploading to exists.
    '''
    if end_index is None:
        end_index = len(df)

    df = _sanitize_columns_for_upload(df)

    print(str(end_index - start_index) + ' rows to insert')

    while start_index < end_index:
        end = min(start_index + batch_size, end_index)
        df_insert = df[start_index:end]
        values_to_insert = [
            _build_dict_for_insert(row)
            for _, row in df_insert.iterrows()
        ]

        Warehouse.engine.execute(reflected_table.insert(), values_to_insert)
        print("Inserted {count} rows to {schema}.{table}".format(
            count=len(df_insert),
            schema=reflected_table.schema,
            table=reflected_table.name,
        ))

        start_index = end

def _build_dict_for_insert(row):
    ret = {}
    for col_name in list(row.index):
        val = row[col_name]

        is_numeric = isinstance(val, float)
        if is_numeric and np.isnan(val):
            val = None

        ret[col_name.lower()] = val
    return ret
