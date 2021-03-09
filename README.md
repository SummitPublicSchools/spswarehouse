# spswarehouse

# Prerequisites

- Anaconda & Python 3
- Jupyter Notebook

# Installation

- To install, run: `pip install spswarehouse`
    - This can be done from `Anaconda Prompt` from the Start Menu.
- Locate the install directory by running: `pip show pip | grep "Location:" | cut -d " " -f2`
    - If this doesn't work, run `pip show pip`, then look at the line "Location:".
    - Take note of the install directory for the "Set up credentials" step.

The files referred to in this `README` are in `<install-directory>/spswarehouse/`.

## Set up dependencies

- Change to the `spswarehouse` directory
    - `cd <install-directory>\spswarehouse`
    - The default for Anaconda3 is `cd Anaconda3\Lib\site-packages\spswarehouse`
- Run: `pip install -r requirements.txt`

You can `exit` the Anaconda Prompt; the next step is more easily done in the File Explorer.

## Updating to new version

When a new version of spswarehouse is released, there are two steps:

- `pip install --upgrade spswarehouse`
- Redo the "Set up dependencies" section.

## Set up credentials

- Navigate to the install directory.
    - The default directory where this module is installed is `Users\<your name>\Anaconda3\Lib\site-packages\spswarehouse`.
    - If you are using a custom environment, the directory will probably be `Users\<your name>\Anaconda3\envs\<env name>\Lib\site-packages\spswarehouse`.

- Copy the `credentials.py.template` file to `credentials.py`.
- Fill in `credentials.py` with the warehouse information and the Google Service Account information provided by your technical admin.

### Snowflake

This allows you to access the Snowflake data warehouse.

- Fill in your Snowflake `user` and `password`  credentials between quotation marks.

### Google

This allows you to access your Google Apps.

- Fill in all the blank fields in `google_config.service_account`. See Developer Notes below if you need to generate credentials.

# Usage

## Snowflake

Your Snowflake connection is configured in `credentials.py` (see above).

Snowflake access is implemented in by `Warehouse`. You can:
- Read data using `read_sql()`
- Reflect a table using `reflect_table()`
- Run a SQL command using `execute()`

### Table & column name tab-completion

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

### Uploading data

The `table_utils` module implements uploading data to the Snowflake warehouse.

The data sources you can upload from are:

- pandas.DataFrame `dataframe`
- CSV file `csv_filename`
- Google Sheet `google_sheet`
- Google Drive files `google_drive_id`

The two major methods are `create_table_stmt` and `upload_to_warehouse`. Both support the above data sources as optional arguments:

 - `dataframe`
 - `csv_filename`
 - `google_sheet`
 - `google_drive_id`

From Jupyter Notebook, open `snowflake-upload-example.ipynb` for a basic example.

### Column types

`create_table_stmt()` will try to guess column types when given a DataFrame, CSV file, or Google Sheet.  

If you want to explicitly name and type your columns, you can pass in the `columns` argument instead.

Alternatively, if you want to force all columns to be strings, pass `force_string=True`. This works for both `create_table_stmt()` and `upload_to_warehouse()`. This does not work if you pass a dataframe.

See the documentation for `guess_col_types()` for best practices for types.

## Google Functions
### GoogleDrive, GoogleSheets, GoogleSlides

Make sure you've set up `credentials.py` first and shared your spreadsheet with the Google service account email. You can also get the email by running any of the following:

```
GoogleSheets.get_google_service_account_email()
GoogleDrive.get_google_service_account_email()
GoogleSlides..get_google_service_account_email()
```

`GoogleSheets` is really an instance of `gspread.Client`, so you can use the entire
[`gspread`](https://gspread.readthedocs.io/en/latest/) Python API.

`GoogleDrive` is an instance of `pydrive2.GoogleDrive`, so you can use the [`PyDrive2`](https://iterative.github.io/PyDrive2/docs/build/html/index.html) Python API.

`GoogleSlides` builds directly on the Google Slides API (https://developers.google.com/resources/api-libraries/documentation/slides/v1/python/latest/)

### Accessing data

From Jupyter Notebook, open and run `googlesheets-example.ipynb` for a basic example on loading a spreadsheet and reading sheet data into `pandas.DataFrame`.

`googledrive-example.ipynb` contains basic examples of exploring Drive via Jupyter. Note that this class only handles files uploaded to Drive; it's not useful for handling Google Sheets, Google Docs, etc.

### Uploading to warehouse

From Jupyter Notebook open and run `snowflake-upload-example.ipynb` for a basic example on uploading Google Sheet data to the Snowflake warehouse.

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
- Install on local machine to test: `pip install spswarehouse==<insert version number> -i https://test.pypi.org/simple/`

### Pushing a new package

Make sure all of your changes are checked into the GitHub repository and your local repository is up-to-date before you do this.

The steps are the same as in the above section, omitting the `test.pypi` URLs.
