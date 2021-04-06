#!/usr/bin/env python
# Copyright 2016-2019 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Setup script for zhmcclient project.
"""

import os
import re
import setuptools


def get_version(version_file):
    """
    Execute the specified version file and return the value of the __version__
    global variable that is set in the version file.

    Note: Make sure the version file does not depend on any packages in the
    requirements list of this package (otherwise it cannot be executed in
    a fresh Python environment).
    """
    with open(version_file, 'r') as fp:
        version_source = fp.read()
    _globals = {}
    exec(version_source, _globals)  # pylint: disable=exec-used
    return _globals['__version__']


def get_requirements(requirements_file):
    """
    Parse the specified requirements file and return a list of its non-empty,
    non-comment lines. The returned lines are without any trailing newline
    characters.
    """
    with open(requirements_file, 'r') as fp:
        lines = fp.readlines()
    reqs = []
    for line in lines:
        line = line.strip('\n')
        if not line.startswith('#') and line != '':
            reqs.append(line)
    return reqs


def read_file(a_file):
    """
    Read the specified file and return its content as one string.
    """
    with open(a_file, 'r') as fp:
        content = fp.read()
    return content


# pylint: disable=invalid-name
requirements = get_requirements('requirements.txt')
install_requires = [req for req in requirements
                    if req and not re.match(r'[^:]+://', req)]
dependency_links = [req for req in requirements
                    if req and re.match(r'[^:]+://', req)]
package_version = get_version(os.path.join('zhmcclient', '_version.py'))

# Docs on setup():
# * https://docs.python.org/2.7/distutils/apiref.html?
#   highlight=setup#distutils.core.setup
# * https://setuptools.readthedocs.io/en/latest/setuptools.html#
#   new-and-changed-setup-keywords
# Explanations for the behavior of package_data, include_package_data, and
# MANIFEST files:
# * https://setuptools.readthedocs.io/en/latest/setuptools.html#
#   including-data-files
# * https://stackoverflow.com/a/11848281/1424462
# * https://stackoverflow.com/a/14159430/1424462
setuptools.setup(
    name='zhmcclient',
    version=package_version,
    packages=[
        'zhmcclient',
        'zhmcclient_mock'
    ],
    include_package_data=True,  # Includes MANIFEST.in files into sdist (only)
    install_requires=install_requires,
    dependency_links=dependency_links,

    description=''
    'A pure Python client library for the IBM Z HMC Web Services API.',
    long_description=read_file('README.rst'),
    long_description_content_type='text/x-rst',
    license='Apache License, Version 2.0',
    author='Juergen Leopold, Andreas Maier',
    author_email='leopoldj@de.ibm.com, maiera@de.ibm.com',
    maintainer='Andreas Maier, Kathir Velusamy',
    maintainer_email='maiera@de.ibm.com, kathir.velu@in.ibm.com',
    url='https://github.com/zhmcclient/python-zhmcclient',
    project_urls={
        'Bug Tracker': 'https://github.com/zhmcclient/python-zhmcclient/issues',
        'Documentation': 'https://python-zhmcclient.readthedocs.io/en/stable/',
        'Change Log':
            'https://python-zhmcclient.readthedocs.io/en/stable/changes.html',
    },

    options={'bdist_wheel': {'universal': True}},
    zip_safe=True,  # This package can safely be installed from a zip file
    platforms='any',

    # Keep these Python versions in sync with:
    # - Section "Supported environments" in docs/intro.rst
    # - Version checking in zhmcclient/_version.py
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
