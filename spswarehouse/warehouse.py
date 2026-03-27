import os
import pandas
import random
import string

try:
    from .credentials import snowflake_config
except ModuleNotFoundError:
    print("No credentials file found in spswarehouse. This could cause issues.")
    
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.engine import reflection
from snowflake.sqlalchemy import VARIANT

from datetime import date

from .config import DEFAULT_BATCH_SIZE, DEFAULT_ENCODING
from .googledrive import GoogleDrive
from .table_utils import renamer, sanitize_columns_for_upload

def describe(table):
    for c in table.columns:
        tipe = c.type
        if isinstance(tipe, VARIANT):
             tipe = 'VARIANT'
        print('{}: {}'.format(c.name, tipe))

class Warehouse:
    """
    This class is an abstraction that allows you to connect to the Snowflake Warehouse.
    It has several methods that allow for easy access to the warehouse.
    -- execute: run some arbitrary SQL in the warehouse. totally safe!
    -- read_sql: execute a SELECT statement and return results as a pandas.DataFrame
    -- reflect: return a SQLAlchemy Table object containing metadata about the table

    This class also has a couple of SQLAlchemy-based instance variables
    - engine: contains information about how to connect to the warehouse
    - insp: a SQLAlchemy inspector object that lets query metadata about the warehouse
            e.g., Snowflake.insp.get_table_names('wild_west')
    """
    def __init__(self, engine):
        self.engine = engine
        self.meta = MetaData()
        self._insp = None
        self._conn = None
        self.loaded_tables = {}   # dictionary of Table objects keyed by "schema.table_name"

    @property
    def insp(self):
        if self._insp is None:
            self._insp = reflection.Inspector.from_engine(self.engine)
        return self._insp

    @property
    def conn(self):
        if self._conn is None:
            self._conn = self.engine.connect()
        return self._conn

    # caller is responsible for closing the connection when done
    def execute(self, sql):
        """
        execute: SQL statement -> (connection, proxy)

        Running the execute method sends the SQL string to the warehouse using
        this object's connection object, and commits the statement.

        No value is returned.
        """
        self.conn.execute(text(sql))
        self.conn.commit()

    def read_sql(self, sql):
        """
        read_sql: 'SELECT ...' -> pandas.DataFrame
        read_sql: SQLAlchemy select object -> pandas.DataFrame

        The warehouse read_sql method is a minimalist wrapper around the pandas.read_sql
        method. The sole argument to this method can either be a string (typically a SELECT statement)
        or an object constructed using SQLAlchemy's select method.
        """
        return pandas.read_sql(sql, self.engine)

    def reflect(self, table_or_view, schema=snowflake_config['schema']):
        """
        reflect: table name, schema name (optional) -> SQLAlchemy Table object
        reflect: view name,  schema name (optional) -> SQLAlchemy Table object

        The reflect method is useful to grab the underlying metadata for a table in the warehouse.
        Using the returned value, you can print out the column names and types using the describe method.

        Note that if the table or view name has a '.' in it, then this method will try to infer the schema name
        and ignore the passed in argument

        t_table = Snowflake.reflect('users', schema='staging_scrapes')
        describe(t_table)
        """
        name_with_schema = '{schema}.{table_or_view}'.format(
            schema=schema,
            table_or_view=table_or_view
        )

        # if it's already been loaded, why bother loading it again? just return it
        table = self.loaded_tables.get(name_with_schema, None)
        if table is not None:
            return table

        table = Table(table_or_view, self.meta, autoload_with=self.engine, schema=schema)

        # sets the column names explicitly on the instance so that tab-completion is easy
        for c in table.columns:
            setattr(table, 'c_{}'.format(c.name), c)

        # save so we don't have to load it again later
        self.loaded_tables[name_with_schema] = table

        return table

    def upload_df(
        self,
        table,
        schema,
        dataframe,
        start_index=0,
        end_index=None,
        batch_size=DEFAULT_BATCH_SIZE,
        force_string=False,
    ):

        if force_string:
            dataframe = dataframe.astype(str)
        
        if end_index is None:
            end_index = len(dataframe)

        dataframe = sanitize_columns_for_upload(dataframe)
        dataframe = dataframe.rename(columns=renamer())
    
        print(str(end_index - start_index) + ' rows to insert')
    
        dataframe[start_index:end_index].to_sql(
            name=table,
            con=self.engine,
            schema=schema,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=batch_size
        )

        print(f"Data inserted to {schema}.{table} successfully")
    
    def upload_google_drive_csv(
        self,
        table,
        schema,
        google_drive_id,
        start_index=0,
        end_index=None,
        batch_size=DEFAULT_BATCH_SIZE,
        encoding=DEFAULT_ENCODING,
        force_string=False,
        sep=",",
    ):
        letters = string.ascii_letters
        filename = ''.join(random.choice(letters) for i in range(10)) + '.csv'
        tempFile = GoogleDrive.CreateFile({'id': google_drive_id})
        tempFile.GetContentFile(filename)
        try:
            if force_string:
                df = pandas.read_csv(filename, encoding=encoding, dtype=str, sep=sep)
            else:
                df = pandas.read_csv(filename, encoding=encoding, sep=sep)
            os.remove(filename)
        except Exception as error:
            raise error

        #  Pass force_string=False, since we've already handled force_string here
        self.upload_df(table, schema, df, start_index, end_index, batch_size, force_string=False)

    
    def upload_google_sheet(
        self,
        table,
        schema,
        google_sheet,
        start_index=0,
        end_index=None,
        batch_size=DEFAULT_BATCH_SIZE,
        encoding=DEFAULT_ENCODING,
        force_string=False,
    ):
        if force_string:
            google_sheet_values = google_sheet.get_all_values()
            df = pandas.DataFrame(google_sheet_values[1:], columns=google_sheet_values[0])
        else:
            df = pandas.DataFrame(google_sheet.get_all_records())

        #  Pass force_string=False, since we've already handled force_string here
        self.upload_df(table, schema, df, start_index, end_index, batch_size, force_string=False)
        
    def upload_local_csv(
        self,
        table,
        schema,
        csv_filename,
        start_index=0,
        end_index=None,
        batch_size=DEFAULT_BATCH_SIZE,
        encoding=DEFAULT_ENCODING,
        force_string=False,
        sep=",",
    ):
        if force_string:
            df = pandas.read_csv(csv_filepath, encoding=encoding, dtype=str, sep=sep)
        else:
            df = pandas.read_csv(csv_filepath, encoding=encoding, sep=sep)

        #  Pass force_string=False, since we've already handled force_string here
        self.upload_df(table, schema, df, start_index, end_index, batch_size, force_string=False)

Warehouse = Warehouse(
    create_engine(
        'snowflake://{user}:{password}@{account}/{db}/{schema}?warehouse={warehouse}'.format(
            user=snowflake_config['user'],
            password=snowflake_config['password'],
            account=snowflake_config['account'],
            db=snowflake_config['db'],
            schema=snowflake_config['schema'],
            warehouse=snowflake_config['warehouse']),
        pool_size=1
    )
)