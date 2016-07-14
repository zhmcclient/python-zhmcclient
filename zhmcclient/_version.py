#!/usr/bin/env python
# Copyright 2016 IBM Corp. All Rights Reserved.
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

import sys
import pbr.version

__all__ = ['__version__']

_version_info = pbr.version.VersionInfo('zhmcclient')
__version__ = _version_info.release_string()

# Check supported Python versions
_python_m = sys.version_info[0]
_python_n = sys.version_info[1]
if _python_m == 2 and _python_n < 7:
    raise RuntimeError('On Python 2, zhcmclient requires Python 2.7')
elif _python_m == 3 and _python_n < 4:
    raise RuntimeError('On Python 3, zhmcclient requires Python 3.4 or higher')

