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
    info = debuginfo.as_dict()
"""

from __future__ import print_function, absolute_import

import sys
import platform
import ctypes

import zhmcclient

__all__ = ['as_dict']


def version_string(version_info):
    """
    Return the 5-tuple version_info as a version string, as follows:

        "1.2.3"  # if version_info[3] == 'final'
        "1.2.3.alpha.42"  # if version_info[3] != 'final'
    """
    major, minor, micro, releaselevel, serial = version_info
    version_str = '{}.{}.{}'.format(major, minor, micro)
    if releaselevel != 'final':
        version_str = '{}.{}.{}'.format(version_str, releaselevel, serial)
    return version_str


def as_dict():
    """
    Return debug information as a dictionary.
    """

    debug_info = dict()

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
    debug_info['impl'] = impl

    if impl == 'CPython':
        impl_version = version_string(sys.version_info)
    elif impl == 'PyPy':
        # pylint: disable=no-member
        impl_version = version_string(sys.pypy_version_info)
    elif impl == 'Jython':
        impl_version = version_string(sys.version_info)  # TODO: Verify
    elif impl == 'IronPython':
        impl_version = version_string(sys.version_info)  # TODO: Verify
    else:
        impl_version = 'unknown'
    debug_info['impl_version'] = impl_version

    debug_info['python_version'] = platform.python_version()

    # pylint: disable=no-member
    debug_info['zhmcclient_version'] = zhmcclient.__version__

    return debug_info


def main():
    """
    Print debug information.
    """

    d = as_dict()

    # pylint: disable=invalid-format-index
    print("Operating system: {d[os_name]} {d[os_version]} "
          "on {d[cpu_arch]}".format(d=d))
    print("Python implementation: {d[impl]} {d[impl_version]} "
          "({d[bit_size]} bit, {d[unicode_size]} unicode)".format(d=d))
    print("Python version: {d[python_version]}".format(d=d))
    print("zhmcclient version: {d[zhmcclient_version]}".format(d=d))
    # pylint: enable=invalid-format-index


if __name__ == '__main__':
    main()
