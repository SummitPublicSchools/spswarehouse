import pandas

try:
    from .credentials import snowflake_config
except ModuleNotFoundError:
    print("No credentials file found in spswarehouse. This could cause issues.")
    
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.engine import reflection
from snowflake.sqlalchemy import VARIANT

from datetime import date

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
        self.meta = MetaData(bind=engine)
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
        this object's connection object. The return value is a tuple of the
        connection object and the SQLAlchemy proxy object returned from executing
        the SQL.
        """
        return self.conn, self.conn.execute(sql)

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

        table = Table(table_or_view, self.meta, autoload=True, schema=schema)

        # sets the column names explicitly on the instance so that tab-completion is easy
        for c in table.columns:
            setattr(table, 'c_{}'.format(c.name), c)

        # save so we don't have to load it again later
        self.loaded_tables[name_with_schema] = table

        return table

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
