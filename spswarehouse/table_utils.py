import pandas as pd
import numpy as np

from .warehouse import Warehouse

ENCODING='utf-8'
INSERT_BATCH_SIZE=50

def upload_csv(
    reflected_table,
    csv_file,
    start_index=0,
    end_index=None,
):
    '''
    upload_csv: SqlAlchemy Table, string -> void

    Uploads a CSV file to specified table.
    Assumes that the table you're uploading to exists.
    '''
    upload_df(
        reflected_table,
        pd.read_csv(csv_file, encoding=ENCODING),
        start_index=start_index,
        end_index=end_index,
    )

def upload_df(
    reflected_table,
    df,
    start_index=0,
    end_index=None,
):
    '''
    upload_df: SqlAlchemy Table, pandas Dataframe -> void

    Uploads a pandas.DataFrame to specified table.
    Assumes that the table you're uploading to exists.
    '''
    end_index = len(df) if end_index is None else end_index

    df = sanitize_df_for_upload(df)
    
    print(str(end_index - start_index) + ' rows to insert')
    while start_index < end_index:
        df_insert = df[start_index:start_index+INSERT_BATCH_SIZE]
        values_to_insert = [ _build_dict_for_insert(row) for _, row in df_insert.iterrows() ]

        Warehouse.engine.execute(reflected_table.insert(), values_to_insert)
        print("Inserted {count} rows to {schema}.{table}".format(
            count=len(df_insert),
            schema=reflected_table.schema,
            table=reflected_table.name,
        ))
        start_index += INSERT_BATCH_SIZE

def _build_dict_for_insert(row):
    ret = {}
    for col_name in list(row.index):
        val = row[col_name]

        is_numeric = isinstance(val, float)
        if is_numeric and np.isnan(val):
            val = None

        ret[col_name.lower()] = val
    return ret

def create_table_stmt_from_csv(csv_file, table_name, schema_name, comment=''):
    '''
    create_table_stmt_from_csv:

    Get a CREATE TABLE statement from a CSV file
    '''
    return create_table_stmt_from_df(
        pd.read_csv(csv_file, encoding=ENCODING),
        table_name,
        schema_name,
        comment=comment,
    )

def create_table_stmt_from_df(df, table_name, schema_name, comment=''):
    '''
    create_table_stmt_from_df:

    Get a CREATE TABLE statement from a pandas.DataFrame
    '''
    df = sanitize_df_for_upload(df)
    return create_table_stmt(
        guess_col_types(df),
        table_name,
        schema_name,
        comment=comment,
    )

def create_table_stmt(col_types, table_name, schema_name, comment=''):
    '''
    create_table_stmt:

    Get a CREATE TABLE statement from {col name -> col type} dictionary.
    '''
    return "CREATE TABLE {schema}.{table_name} ({cols}) COMMENT = '{comment}'".format(
        schema=schema_name,
        table_name=table_name,
        cols=', '.join([(name + ' ' + tipe) for name, tipe in col_types.items()]),
        comment=comment,
    )

def sanitize_df_for_upload(dataframe):
    '''
    sanitize_df_for_upload: pandas.DataFrame -> pandas.DataFrame

    Creates a dataframe from a CSV file and sanitizes column names.
    '''
    # Overwrite column names with sanitized versions, by substituting _ for
    # special characters
    sanitize = lambda name: name.translate(
        {ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+ "}
    )
    dataframe.columns = list(map(sanitize, list(dataframe.columns)))
    return dataframe

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
