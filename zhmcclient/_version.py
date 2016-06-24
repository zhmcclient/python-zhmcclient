#!/usr/bin/env python

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

