# Copyright 2016-2021 IBM Corp. All Rights Reserved.
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
Definition of the package version, and check for supported Python versions.
"""

import sys

__all__ = ['__version__']

#: The full version of this package including any development levels, as a
#: :term:`string`.
#:
#: Possible formats for this version string are:
#:
#: * "M.N.P.dev1": A not yet released version M.N.P
#: * "M.N.P": A released version M.N.P
__version__ = '1.0.3'

# Check supported Python versions
# Keep these Python versions in sync with:
# - python_requires and classifiers in setup.py
# - Section "Supported environments" in docs/intro.rst
_PYTHON_M = sys.version_info[0]
_PYTHON_N = sys.version_info[1]
if _PYTHON_M == 2 and _PYTHON_N < 7:
    raise RuntimeError('On Python 2, zhcmclient requires Python 2.7')
if _PYTHON_M == 3 and _PYTHON_N < 5:
    raise RuntimeError('On Python 3, zhmcclient requires Python 3.5 or higher')
