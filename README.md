# spswarehouse

## Prerequisites

- Anaconda & Python 3
- Jupyter Notebook

## Installation

- To install, run: `pip install spswarehouse`
    - This can be done from `Anaconda Prompt` from the Start Menu.
- Locate the install directory by running: `pip show pip | grep "Location:" | cut -d " " -f2`
    - If this doesn't work, run `pip show pip`, then look at the line "Location:".

The files referred to in this `README` are in `<install-directory>/spswarehouse/`.

### Set up dependencies

- Change to the `spswarehouse` directory
    - `cd <install-directory>\spswarehouse`
    - The default for Anaconda3 is `cd Anaconda3\Lib\site-packages\spswarehouse`
- Run: `pip install -r requirements.txt`

You can `exit` the Anaconda Prompt; the next step is more easily done in the File Explorer.

### Set up credentials

To access the Snowflake data warehouse, you'll need to set up your credentials first. This file is in the
`spswarehouse` directory.

- Default directory: `Users\<your name>\Anaconda3\Lib\site-packages\spswarehouse`
- Copy the `credentials.py.template` file to `credentials.py`.
- Fill in your Snowflake `user` and `password`  credentials between quotation marks.

# Usage

## Snowflake

Your Snowflake connection is configured in `credentials.py` (see above).

Snowflake access is implemented in by `Warehouse`. You can:
- Read data using `read_sql()`
- Reflect a table using `reflect_table()`
- Run a SQL command using `execute()`

## Table & column name tab-completion

When you run `import spswarehouse`, some tab-completion for table and column names is automatically set up.

The format is:

```
spswarehouse.<schema_name>.<table name>.c_<column name>
```

To reduce load time, tab-completion is automatically set up for only a few schemas when `spswarehouse`is imported.

If the schema you're using isn't tab-completing you can manually import it.

For example, to enable tab-competion for the schema `schoolmint`, run:

```
from spswarehouse.table_names import *

initialize_schema_object(SchoolMint)
schoolmint = SchoolMint()
```

## CSV file upload

CSV uploading is implemented by the `table_utils` module.

If the table you want to upload your CSV to already exists:

```
from spswarehouse.table_utils import *
from spswarehouse.warehouse import Warehouse

reflected_table = Warehouse.reflect(<table name>)
upload_csv(reflected_table, <csv_file>)
```

If you want to upload to a *new* table, you'll have to create the table first:

```
sql = create_table_stmt_from_csv(<csv_file>, <table name>, <schema>)
Warehouse.execute(sql)
```

 Now you can call `reflect()` and `upload_csv()`.

 ## GoogleSheet upload

TODO
