import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="spswarehouse",
    version="1.0.0",
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
        'pandas>=2.3.3,<3.0.0',
        # These three packages are frozen on specific versions, because they
        # have a particular tendency to break things when updated
        'snowflake-sqlalchemy==1.8.2',
        'snowflake-connector-python==4.0.0',
        'sqlalchemy==2.0.43',
        'google-api-python-client>=2.188.0,<3.0.0',
        'google-auth-oauthlib>=1.2.4,<2.0.0',
        'gspread>=6.2.1,<7.0.0',
        'gspread-dataframe>=4.0.0,<5.0.0',
        'gspread-formatting>=1.2.1,<2.0.0',
        'PyDrive2>=1.21.3,<2.0.0',
        'duct-tape>=0.26.6,<1.0.0',
        'requests>=2.32.5,<3.0.0',
        'selenium>=4.40.0,<5.0.0',
    ],
)
