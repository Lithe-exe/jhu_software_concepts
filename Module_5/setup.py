"""
Setup Module
============
You use this file to make your project installable and distributable.
"""
from setuptools import setup, find_packages

setup(
    name="module_5",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "psycopg",
        "beautifulsoup4",
        "urllib3"
    ],
)