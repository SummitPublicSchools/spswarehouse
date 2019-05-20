# spswarehouse

# Prerequisites

- Anaconda & Python 3
- Jupyter Notebook

# Installation

- To install, run: `pip install spswarehouse`
    - This can be done from `Anaconda Prompt` from the Start Menu.
- Locate the install directory by running: `pip show pip | grep "Location:" | cut -d " " -f2`
    - If this doesn't work, run `pip show pip`, then look at the line "Location:".

The files referred to in this `README` are in `<install-directory>/spswarehouse/`.

## Set up dependencies

- Change to the `spswarehouse` directory
    - `cd <install-directory>\spswarehouse`
    - The default for Anaconda3 is `cd Anaconda3\Lib\site-packages\spswarehouse`
- Run: `pip install -r requirements.txt`

You can `exit` the Anaconda Prompt; the next step is more easily done in the File Explorer.

## Set up credentials

The default directory where this module is installed is `Users\<your name>\Anaconda3\Lib\site-packages\spswarehouse`. Your credentials are in the `spswarehouse` subdirectory.

- Copy the `credentials.py.template` file to `credentials.py`.

### Snowflake

This allows you to access the Snowflake data warehouse.

- Fill in your Snowflake `user` and `password`  credentials between quotation marks.

### Google Sheets

This allows you to access your Google spreadsheets.

- Get the `private_key` for the Google Service account from your team.
- In `credentials.py`, under `google_config` and `service-account`, fill in the `private_key` between quotation marks.
- The first time you `import` the `GoogleSheets` module, the service account's email address will be printed, you will share any spreadsheets you want to access with that email address.

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

## Google Sheets

Make sure you've set up `credentials.py` first and shared your spreadsheet with the Google service account email. You can also get the email by running:

```
GoogleSheets.get_google_service_account_email()
```

`GoogleSheets` is really an instance of `gspread.Client`, so you use the entire
[`gspread`](https://gspread.readthedocs.io/en/latest/) Python API.

### Accessing data

From Jupyter Notebook, open and run `googlesheets-example.ipynb` for a basic example on loading a spreadsheet and reading sheet data into `pandas.DataFrame`.

### Uploading to warehouse

Once you have a `DataFrame`, you can download data to a CSV file to your local machine and upload it to the warehouse using `table_utils`.

### Column types

# Developer notes

## Google service account key

This lets us use the Google Sheets API to access sheet data. It only has to be done once and added to `credentials.py.template`.

- Use an existing Google Developer project, or create a new one: https://console.cloud.google.com
- Enable the Google Sheets API
  - Go to **API & Services** for the project, then **Libraries**.
  - Search for "Google Sheets" and select the result.
  - Click **Enable**.
- Create the OAuth client credentials
  - Go to **API & Services** for the project, then **Credentials**.
  - Under **Create credentials**, select **Service account key**
  - Choose an existing service account or create a new one to associate this key with.
  - Create the key and download the key as a JSON file.
- Copy OAuth client credentials to `credentials.py.template` in `google_client` under `service-account`.
- **Delete the private_key** and leave just the quotation marks when you check in `credentials.template.py`.
- You will need to distribute the private key securely so it can be added to `credentials.py`.

## PyPI

We use [PyPI](https://pypi.org/) to distribute the `spswarehouse` module and [Test PyPI](https://test.pypi.org/)  for testing.

The `spswarehouse` project is [here](https://pypi.org/project/spswarehouse/).

### Set up

Create PyPI and Test PyPI accounts to test and upload packages.

### Packaging

See https://packaging.python.org/tutorials/packaging-projects/ for an overview and walk-through of PyPI packaging.

Specifics for `spswarehouse`:

- Only build the `sdist` package. Otherwise, `credentials.py` and potentially passwords will get distributed in the binary distribution.
- If you need to include non-Python files, add them to `MANIFEST.in`.

### Testing

- Update version number in `setup.py`.
- Create the package:
`python setup.py sdist`
- Upload to Test PyPI:
`python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*`
- Install on local machine to test: `pip install -i https://test.pypi.org/simple/`

### Pushing a new package

Make sure all of your changes are checked into the GitHub repository and your local repository is up-to-date before you do this.

The steps are the same as in the above section, omitting the `test.pypi` URLs.
