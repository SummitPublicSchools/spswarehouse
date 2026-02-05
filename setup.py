import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="spswarehouse",
    version="1.0.1",
    author="Summit Public Schools; Harry Li Consulting, LLC",
    author_email="warehouse@summitps.org",
    description="Summit Public Schools Snowflake warehouse",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SummitPublicSchools/spswarehouse",
    packages=setuptools.find_packages(),
    # This needs to be set so you get the files included by MANIFEST.in
    # when you run "pip install"
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    install_requires=[
        'pandas==2.3.3',
        'snowflake-sqlalchemy==1.8.2',
        'snowflake-connector-python==4.0.0',
        'sqlalchemy==2.0.43',
        'google-api-python-client==2.188.0',
        'google-auth-oauthlib==1.2.4',
        'gspread==6.2.1',
        'gspread-dataframe==4.0.0',
        'gspread-formatting==1.2.1',
        'PyDrive2==1.21.3',
        'duct-tape==0.26.6',
        'requests==2.32.5',
        'selenium==4.40.0',
    ],
)
