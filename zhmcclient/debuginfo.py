# Copyright 2020 IBM Corp. All Rights Reserved.
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
Script for printing debug information.

The debug information can be used when reporting bugs to the zhmcclient issue
tracker.

Command line usage:
    python -m zhmcclient.debuginfo

Programmatic usage:
    from zhmclient import debuginfo
    print(debuginfo.as_dict())
"""

from __future__ import print_function, absolute_import

import sys
import platform
import ctypes

from . import __version__ as zhmcclient_version


__all__ = ['as_dict']


def as_dict():
    """
    Return debug information as a dictionary.
    """

    debug_info = dict()

    debug_info['os_name'] = platform.system()
    debug_info['os_version'] = platform.release()

    debug_info['cpu_arch'] = platform.machine()
    debug_info['bit_size'] = ctypes.sizeof(ctypes.c_void_p) * 8

    s = b'\\U00010142'
    c = s.decode('unicode-escape')
    if len(c) == 1:
        debug_info['unicode_size'] = 'wide'
    elif len(c) == 2:
        debug_info['unicode_size'] = 'narrow'
    else:
        # Should not happen
        debug_info['unicode_size'] = 'unknown'

    impl = platform.python_implementation()
    if impl == 'CPython':
        impl_version = platform.python_version()
    elif impl == 'PyPy':
        impl_version = '{vi.major}.{vi.minor}.{vi.micro}'. \
            format(vi=sys.pypy_version_info)
        if sys.pypy_version_info.releaselevel != 'final':
            impl_version += sys.pypy_version_info.releaselevel
    elif impl == 'Jython':
        impl_version = platform.python_version()
    elif impl == 'IronPython':
        impl_version = platform.python_version()
    else:
        impl_version = 'Unknown'
    debug_info['impl'] = impl
    debug_info['impl_version'] = impl_version

    debug_info['python_version'] = platform.python_version()

    debug_info['zhmcclient_version'] = zhmcclient_version

    return debug_info


def main():
    """
    Print debug information.
    """

    d = as_dict()

    print("OS platform: {d[os_name]} {d[os_version]}".format(d=d))
    print("CPU architecture: {d[cpu_arch]}".format(d=d))
    print("Python implementation: {d[impl]} {d[impl_version]}".format(d=d))
    print("Python bit size: {d[bit_size]} bit".format(d=d))
    print("Python unicode size: {d[unicode_size]}".format(d=d))
    print("Python version: {d[python_version]}".format(d=d))
    print("zhmcclient version: {d[zhmcclient_version]}".format(d=d))


if __name__ == '__main__':
    main()
