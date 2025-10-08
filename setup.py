# setup.py — minimal compatibility shim for editable installs
from setuptools import setup, find_packages

setup(
    name="mymap",
    version="0.1.0",
    description="MyMap — A Nusantaran Mind Mapping App",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
