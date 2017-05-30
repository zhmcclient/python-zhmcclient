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
Internal utilities for the zhmcclient implementation.
"""

from __future__ import absolute_import

import pprint
from datetime import datetime


def _indent(text, amount, ch=' '):
    """Return the indent text, where each line is indented by `amount`
    characters `ch`."""
    padding = amount * ch
    return ''.join(padding + line for line in text.splitlines(True))


def repr_text(text, indent):
    """Return a debug representation of a multi-line text (e.g. the result
    of another repr...() function)."""
    ret = _indent(text, amount=indent)
    return ret.lstrip(' ')


def repr_list(_list, indent):
    """Return a debug representation of a list or tuple."""
    ret = pprint.pformat(_list, indent=indent)
    return ret.lstrip(' ')


def repr_dict(_dict, indent):
    """Return a debug representation of a dict or OrderedDict."""
    ret = pprint.pformat(_dict, indent=indent)
    return ret.lstrip(' ')


def repr_timestamp(timestamp):
    """Return a debug representation of a timestamp (as defined for HMC
    properties, i.e. an integer number indicating seconds since the epoch)."""
    dt = datetime.fromtimestamp(timestamp)
    ret = "%d (%s)" % (timestamp,
                       dt.strftime('%Y-%m-%d %H:%M:%S local'))
    return ret


def repr_manager(manager, indent):
    """Return a debug representation of a manager object."""
    return repr_text(repr(manager), indent=indent)
