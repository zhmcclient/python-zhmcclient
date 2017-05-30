# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
Access to the package version, and check for supported Python versions.

Note: The package version is not defined here, but determined dynamically by
the `pbr` package from Git information.
"""

import sys
import pbr.version

__all__ = ['__version__']

#: The full version of this package including any development levels, as a
#: :term:`string`.
#:
#: Possible formats for this version string are:
#:
#: * "M.N.P.devD": Development level D of a not yet released assumed M.N.P
#:   version
#: * "M.N.P": A released M.N.P version
__version__ = pbr.version.VersionInfo('zhmcclient').release_string()

# Check supported Python versions
_PYTHON_M = sys.version_info[0]
_PYTHON_N = sys.version_info[1]
if _PYTHON_M == 2 and _PYTHON_N < 7:
    raise RuntimeError('On Python 2, zhcmclient requires Python 2.7')
elif _PYTHON_M == 3 and _PYTHON_N < 4:
    raise RuntimeError('On Python 3, zhmcclient requires Python 3.4 or higher')
