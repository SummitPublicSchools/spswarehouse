# spswarehouse

# 1.X Changes
## Major Changes
- `table_utils.upload_to_warehouse` has been deprecated. Instead the Warehouse class now has a varietey of native `upload_<data>` functions that do not require reflecting the target table.
- The available Warehouse upload functions are
    - `Warehouse.upload_df`
    - `Warehouse.upload_google_drive_csv`
    - `Warehouse.upload_google_sheet`
    - `Warehouse.upload_local_csv`
- Differencces between the new upload functions and the old `upload_to_warehouse`
    - These functions take `table` and `schema` as two separate arguments instead of `reflected_table`.
    - `upload_df` does not acccept the `sep` argument (since the `sep` argument didn't do anything with dataframes anyways)
    - Each function only accepts its listed data type (e.g., `upload_df` only accepts `dataframe`, and does not acceept `csv_filename`)
    - All other argumenets are the same (`batch_size`, `encoding`, etc.)
- When using `table_utils.create_table_stmt` and the `Warehouse.upload_<data>` functions, first, symbols are sanitized to underscores. Then consecutive underscores are collapsed into a single underscore.
    - Additionally, it now uses `re.compile('[\W_]+')` as the basis for replacement, rather than a custom list of symbols (making it consistent with how Summit's Airflow server behaves)
- Upgrade to gspread 6.X. The 6.X update of gspread reversed the default argument order of severala functions. It's advised that you name arguments instead of relying on position.
- The update to SQLAlchemy 2.X significanatly changes how the Warehouse class queries things. The Warehouse class abstracts most of this, but if you were calling `Warehouse.engine` or `Warehouse.conn` directly, your code may break.
- The `helper_` functions were removed from `selenium.py`. Simply remove the `helper_` prefix from the function name to fix.

## Minor changes
- Most likely, you were upgraded to `numpy>=2.0.0` as part of the package update, which may break some minor things.
- You know longer have to manually install requirements; the requirements install is built into the `spswarehouse` install

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

### Uploading data

From Jupyter Notebook, open `snowflake-upload-example.ipynb` for a basic example.

### Column types

`create_table_stmt()` will try to guess column types when given a DataFrame, CSV file, or Google Sheet.  

If you want to explicitly name and type your columns, you can pass in the `columns` argument instead.

Alternatively, if you want to force all columns to be strings, pass `force_string=True`. This works for both `create_table_stmt()` and `Warehouse.upload_<data_type>`. This does not work if you pass a dataframe.

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
- Install on local machine to test: `pip install spswarehouse==<insert version number> --no-build-isolation -i https://test.pypi.org/simple/`
- TODO: Figure out how to do this without needing the `--no-build-isolation` flag

### Pushing a new package

Make sure all of your changes are checked into the GitHub repository and your local repository is up-to-date before you do this.

The steps are the same as in the above section, omitting the `test.pypi` URLs.
