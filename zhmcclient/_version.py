#!/usr/bin/env python

"""
Access to the package version, and check for supported Python versions.

Note: The package version is not defined here, but determined dynamically by
the `pbr` package from Git information.
"""

import sys
import pbr.version

__all__ = ['__version__']

__version__ = pbr.version.VersionInfo('zhmcclient').release_string()

# Check supported Python versions
_PYTHON_M = sys.version_info[0]
_PYTHON_N = sys.version_info[1]
if _PYTHON_M == 2 and _PYTHON_N < 7:
    raise RuntimeError('On Python 2, zhcmclient requires Python 2.7')
elif _PYTHON_M == 3 and _PYTHON_N < 4:
    raise RuntimeError('On Python 3, zhmcclient requires Python 3.4 or higher')
