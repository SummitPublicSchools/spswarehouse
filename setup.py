import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="spswarehouse",
    version="0.0.7.3",
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
)
