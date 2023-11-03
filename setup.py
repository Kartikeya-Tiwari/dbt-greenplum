#!/usr/bin/env python
#!/usr/bin/env python
import os
import re
import sys

# sys.version_info variable is a named tuple that contains information about the Python interpreter's version
# It has five components of the Python version number: major, minor, micro, releaselevel, and serial.
# for dbt 1.6.0 supports python 3.8 and above
if sys.version_info < (3, 8):
    print("Error: dbt does not support this version of Python.")
    print("Please upgrade to Python 3.7 or higher.")
    sys.exit(1)

print(sys.version_info)

from setuptools import setup

try:
    from setuptools import find_namespace_packages
except ImportError:
    # the user has a downlevel version of setuptools.
    print("Error: dbt requires setuptools v40.1.0 or higher.")
    print('Please upgrade setuptools with "pip install --upgrade setuptools" ' "and try again")
    sys.exit(1)


PSYCOPG2_MESSAGE = """
No package name override was set.
Using 'psycopg2-binary' package to satisfy 'psycopg2'

If you experience segmentation faults, silent crashes, or installation errors,
consider retrying with the 'DBT_PSYCOPG2_NAME' environment variable set to
'psycopg2'. It may require a compiler toolchain and development libraries!
""".strip()

# __file__ variable is a special variable in Python that contains the path to the current file
# os.path.dirname() - this function removes the file name from the path returned by __file__
# os.path.abspath() - this function converts a relative path to an absolute path.
this_directory = os.path.abspath(os.path.dirname(__file__))

# In here we are using the path stored in "this_directory" variable to read the entire "README.md" file and store it in the variable long_description
with open(os.path.join(this_directory, "README.md")) as f:
    long_description = f.read()


###### Defining function _dbt_psycopg2_name ######
# Get the value of the environment variable DBT_PSYCOPG2_NAME. If the environment variable is not null return it, else return "psycopg2-binary"
def _dbt_psycopg2_name():
    # if the user chose something, use that
    package_name = os.getenv("DBT_PSYCOPG2_NAME", "")
    if package_name:
        return package_name

    # default to psycopg2-binary for all OSes/versions
    print(PSYCOPG2_MESSAGE)
    return "psycopg2-binary"

###### Defining function _get_plugin_version_dict ######
# Reads the version from __version__.py file located at /path/to/dbt/adapters/greenplum and returns the major, minor, patch, prekind, pre separated out
def _get_plugin_version_dict():
    # Creating an absolute path for __version__.py file
    # Resulting path example - /path/to/dbt/adapters/greenplum/__version__.py
    _version_path = os.path.join(this_directory, "dbt", "adapters", "greenplum", "__version__.py")

    # regular expression to match a semver string - a string that represents a version number
    _semver = r"""(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"""

    # regular expression to match pre-release version identifier that is appended to a semver string - examples a, b. rc, pre
    _pre = r"""((?P<prekind>a|b|rc)(?P<pre>\d+))?"""

    # regular expression to combine the above two 
    _version_pattern = fr"""version\s*=\s*["']{_semver}{_pre}["']"""

    # read the file at the path stored in "_version_path" variable, strips any leading or trailing whitespace
    # next look up the reg ex stored inside "_version_pattern" in this file
    # If there is no match throw an error else return the version number
    # Example output - {'major': '1', 'minor': '6', 'patch': '0', 'prekind': None, 'pre': None}
    with open(_version_path) as f:
        match = re.search(_version_pattern, f.read().strip())
        if match is None:
            raise ValueError(f"invalid version at {_version_path}")
        return match.groupdict()


###### Defining function _get_package_version ######
# Combines the output of _get_plugin_version_dict() function to create the version number
# version = major + minor + patch + prekind + pre
# This function only takes into account major, minor, prekind
# patch is hard coded as '0' and pre is not taken into account
# Example output 1: parts = {'major': '1', 'minor': '6', 'patch': '0', 'prekind': None, 'pre': None} | Output =  '1.6.0'
# Example output 1: pasts = {'major': '1', 'minor': '6', 'patch': '1', 'prekind': 'rc', 'pre': '5'}  | Output =  '1.6.0rc1' 
def _get_package_version():
    parts = _get_plugin_version_dict()
    minor = "{major}.{minor}.0".format(**parts)
    pre = parts["prekind"] + "1" if parts["prekind"] else ""
    return f"{minor}{pre}"

###### Defining function _get_dbt_core_version ######
# Exact same as the above function
def _get_dbt_core_version():
    parts = _get_plugin_version_dict()
    minor = "{major}.{minor}.0".format(**parts)
    pre = parts["prekind"] + "1" if parts["prekind"] else ""
    return f"{minor}{pre}"

# Defining variables
package_name = "dbt-greenplum"
package_version = _get_package_version() # Calling function _get_package_version, example output =  '1.6.0'
dbt_core_version = _get_dbt_core_version() # Calling function _get_dbt_core_version, example output =  '1.6.0'
description = """The greenplum adapter plugin for dbt (data build tool)"""

DBT_PSYCOPG2_NAME = _dbt_psycopg2_name() # Calling function _dbt_psycopg2_name, example output = 'psycopg2-binary'

setup(
    name=package_name,
    version=package_version,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Mark Poroshin",
    author_email="mark.poroshin@yandex.ru",
    url="https://github.com/markporoshin/dbt-greenplum",
    # part of setuptools python lib - find all namespace packages in the dbt directory and its subdirectories that have a mention of "dbt"
    # Example output - ['dbt', 'dbt.adapters', 'dbt.include', 'dbt.adapters.greenplum', 'dbt.include.greenplum', 'dbt.include.greenplum.macros',
    #                                'dbt.include.greenplum.macros.materializations']
    packages=find_namespace_packages(include=["dbt", "dbt.*"]), 
    # specify data files that should be installed along with the package
    package_data={
        "dbt": [
            "include/greenplum/dbt_project.yml",
            "include/greenplum/sample_profiles.yml",
            "include/greenplum/macros/*.sql",
            "include/greenplum/macros/**/*.sql",
        ]
    },
    # dependencies of this Python package
    # Example output = ['dbt-core~=1.6.0', 'dbt-postgres~=1.6.0', 'psycopg2-binary~=2.8']
    # The ~ operator in the version specifiers indicates that newer versions of the packages are allowed to be installed.
    # This is a good practice because it allows users of your package to install the latest versions of your dependencies without having to explicitly update your package.
    # psycopg2-binary~=2.8 ==> min version of psycopg2 required is 2.8 which is good with python 3.8
    # Example of when this would fail psycopg2-binary~=2.9.9 while using python 3.6 as 2.9.9 needs Python >=3.7
    install_requires=[
        "dbt-core~={}".format(dbt_core_version),
        "dbt-postgres~={}".format(package_version),
        "{}~=2.8".format(DBT_PSYCOPG2_NAME),
    ],
    zip_safe=False,
    # Classifiers are used to categorize packages on PyPI, making it easier for users to find the packages they need
    # Complete list of Classifiers - https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    # Minimum version of python required to install this package - this will gets checked during the pip install phase
    python_requires=">=3.8",
)