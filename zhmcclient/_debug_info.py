# Copyright 2020,2021 IBM Corp. All Rights Reserved.
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
Module for obtaining debug information.

The debug information can be used when reporting bugs to the zhmcclient issue
tracker.

Programmatic usage:
    import zhmcclient
    print(zhmcclient.debuginfo())

Command line usage:
    python -c "import zhmcclient; print(zhmcclient.debuginfo())"
"""


import sys
import platform
import ctypes

from ._version import __version__

__all__ = ['debuginfo']


def _version_string(version_info):
    """
    Return the 5-tuple version_info as a version string, as follows:

        "1.2.3"  # if version_info[3] == 'final'
        "1.2.3.alpha.42"  # if version_info[3] != 'final'
    """
    major, minor, micro, releaselevel, serial = version_info
    version_str = f'{major}.{minor}.{micro}'
    if releaselevel != 'final':
        version_str = f'{version_str}.{releaselevel}.{serial}'
    return version_str


def debuginfo():
    """
    Return debug information as a multi-line string.
    """
    di_dict = debuginfo_dict()
    ret = ""
    for k, v in di_dict.items():
        ret += f"{k}: {v}\n"
    return ret


def debuginfo_dict():
    """
    Return debug information as a dictionary.
    """

    debug_info = {}

    debug_info['os_name'] = platform.system()
    debug_info['os_version'] = platform.release()

    debug_info['cpu_arch'] = platform.machine()
    debug_info['bit_size'] = ctypes.sizeof(ctypes.c_void_p) * 8

    char_len = len(b'\\U00010142'.decode('unicode-escape'))
    if char_len == 1:
        debug_info['unicode_size'] = 'wide'
    elif char_len == 2:
        debug_info['unicode_size'] = 'narrow'
    else:
        # Should not happen
        debug_info['unicode_size'] = 'unknown'

    impl = platform.python_implementation()
    debug_info['python_impl'] = impl

    if impl == 'CPython':
        impl_version = _version_string(sys.version_info)
    elif impl == 'PyPy':
        # pylint: disable=no-member
        impl_version = _version_string(sys.pypy_version_info)
    elif impl == 'Jython':
        impl_version = _version_string(sys.version_info)  # TODO: Verify
    elif impl == 'IronPython':
        impl_version = _version_string(sys.version_info)  # TODO: Verify
    else:
        impl_version = 'unknown'
    debug_info['python_impl_version'] = impl_version

    debug_info['python_version'] = platform.python_version()

    debug_info['zhmcclient_version'] = __version__

    return debug_info
