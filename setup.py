import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="spswarehouse_airflow",
    version="0.0.1.14",
    author="Harry Li Consulting, LLC",
    author_email="hcli.consulting@gmail.com",
    description="Summit Public Schools Snowflake warehouse for use in Airflow",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SummitPublicSchools/spswarehouse_airflow",
    packages=setuptools.find_packages(),
    # This needs to be set so you get the files included by MANIFEST.in
    # when you run "pip install"
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
)
