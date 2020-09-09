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
Utility functions.
"""

from __future__ import absolute_import

from collections import OrderedDict
try:
    from collections.abc import Mapping, MutableSequence, Iterable
except ImportError:
    from collections import Mapping, MutableSequence, Iterable
from datetime import datetime
import six
import pytz
from requests.utils import quote

__all__ = ['datetime_from_timestamp', 'timestamp_from_datetime']


_EPOCH_DT = datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc)


def _indent(text, amount, ch=' '):
    """Return the indent text, where each line is indented by `amount`
    characters `ch`."""
    padding = amount * ch
    return ''.join(padding + line for line in text.splitlines(True))


def repr_text(text, indent):
    """Return a debug representation of a multi-line text (e.g. the result
    of another repr...() function)."""
    if text is None:
        return 'None'
    ret = _indent(text, amount=indent)
    return ret.lstrip(' ')


def repr_list(lst, indent):
    """Return a debug representation of a list or tuple."""
    # pprint represents lists and tuples in one row if possible. We want one
    # per row, so we iterate ourselves.
    if lst is None:
        return 'None'
    if isinstance(lst, MutableSequence):
        bm = '['
        em = ']'
    elif isinstance(lst, Iterable):
        bm = '('
        em = ')'
    else:
        raise TypeError("Object must be an iterable, but is a %s" %
                        type(lst))
    ret = bm + '\n'
    for value in lst:
        ret += _indent('%r,\n' % value, 2)
    ret += em
    ret = repr_text(ret, indent=indent)
    return ret.lstrip(' ')


def repr_dict(dct, indent):
    """Return a debug representation of a dict or OrderedDict."""
    # pprint represents OrderedDict objects using the tuple init syntax,
    # which is not very readable. Therefore, dictionaries are iterated over.
    if dct is None:
        return 'None'
    if not isinstance(dct, Mapping):
        raise TypeError("Object must be a mapping, but is a %s" %
                        type(dct))
    if isinstance(dct, OrderedDict):
        kind = 'ordered'
        ret = '%s {\n' % kind  # non standard syntax for the kind indicator
        for key in six.iterkeys(dct):
            value = dct[key]
            ret += _indent('%r: %r,\n' % (key, value), 2)
    else:  # dict
        kind = 'sorted'
        ret = '%s {\n' % kind  # non standard syntax for the kind indicator
        for key in sorted(six.iterkeys(dct)):
            value = dct[key]
            ret += _indent('%r: %r,\n' % (key, value), 2)
    ret += '}'
    ret = repr_text(ret, indent=indent)
    return ret.lstrip(' ')


def repr_timestamp(timestamp):
    """Return a debug representation of an HMC timestamp number."""
    if timestamp is None:
        return 'None'
    dt = datetime_from_timestamp(timestamp)
    ret = "%d (%s)" % (timestamp,
                       dt.strftime('%Y-%m-%d %H:%M:%S.%f %Z'))
    return ret


def repr_manager(manager, indent):
    """Return a debug representation of a manager object."""
    return repr_text(repr(manager), indent=indent)


def datetime_from_timestamp(ts, tzinfo=pytz.utc):
    """
    Convert an :term:`HMC timestamp number <timestamp>` into a
    :class:`~py:datetime.datetime` object. The resulting object will be
    timezone-aware and will be represented in the specified timezone,
    defaulting to UTC.

    The HMC timestamp number must be non-negative. This means the special
    timestamp value -1 cannot be represented as datetime and will cause
    ``ValueError`` to be raised.

    The date and time range supported by this function has the following
    bounds:

    * The upper bounds is determined by :attr:`py:datetime.datetime.max` and
      additional limitations, as follows:

      * 9999-12-31 23:59:59 UTC, for 32-bit and 64-bit CPython on Linux and
        OS-X.
      * 3001-01-01 07:59:59 UTC, for 32-bit and 64-bit CPython on Windows, due
        to a limitation in `gmtime() in Visual C++
        <https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/gmtime-gmtime32-gmtime64>`_.
      * 2038-01-19 03:14:07 UTC, for some 32-bit Python implementations,
        due to the `Year 2038 problem
        <https://en.wikipedia.org/wiki/Year_2038_problem>`_.

    * The lower bounds is the UNIX epoch: 1970-01-01 00:00:00 UTC.

    Parameters:

      ts (:term:`timestamp`):
        Point in time as an HMC timestamp number.

        Must not be `None`.

      tzinfo (:class:`py:datetime.tzinfo`):
        Timezone in which the returned object will be represented.
        This may be any object derived from :class:`py:datetime.tzinfo`,
        including but not limited to objects returned by
        :func:`pytz.timezone`.

        Note that this parameter does not affect how the HMC timestamp value is
        interpreted; i.e. the effective point in time represented by the
        returned object is not affected. What is affected by this parameter
        is for example the timezone in which the point in time is shown when
        printing the returned object.

        Must not be `None`.

    Returns:

      :class:`~py:datetime.datetime`:
        Point in time as a timezone-aware Python datetime object for the
        specified timezone.

    Raises:
        ValueError
    """
    # Note that in Python 2, "None < 0" is allowed and will return True,
    # therefore we do an extra check for None.
    if ts is None:
        raise ValueError("HMC timestamp value must not be None.")
    if ts < 0:
        raise ValueError(
            "Negative HMC timestamp value {} cannot be represented as "
            "datetime.".format(ts))
    epoch_seconds = ts // 1000
    delta_microseconds = ts % 1000 * 1000
    if tzinfo is None:
        raise ValueError("Timezone must not be None.")
    try:
        dt = datetime.fromtimestamp(epoch_seconds, tzinfo)
    except (ValueError, OSError) as exc:
        raise ValueError(str(exc))
    dt = dt.replace(microsecond=delta_microseconds)
    return dt


def timestamp_from_datetime(dt):
    """
    Convert a :class:`~py:datetime.datetime` object into an
    :term:`HMC timestamp number <timestamp>`.

    The date and time range supported by this function has the following
    bounds:

    * The upper bounds is :attr:`py:datetime.datetime.max`, as follows:

      * 9999-12-31 23:59:59 UTC, for 32-bit and 64-bit CPython on Linux and
        OS-X.
      * 2038-01-19 03:14:07 UTC, for some 32-bit Python implementations,
        due to the `Year 2038 problem
        <https://en.wikipedia.org/wiki/Year_2038_problem>`_.

    * The lower bounds is the UNIX epoch: 1970-01-01 00:00:00 UTC.

    Parameters:

      dt (:class:`~py:datetime.datetime`):
        Point in time as a Python datetime object. The datetime object may be
        timezone-aware or timezone-naive. If timezone-naive, the UTC timezone
        is assumed.

        Must not be `None`.

    Returns:

      :term:`timestamp`:
        Point in time as an HMC timestamp number.

    Raises:
        ValueError
    """
    if dt is None:
        raise ValueError("datetime value must not be None.")
    if dt.tzinfo is None:
        # Apply default timezone to the timezone-naive input
        dt = pytz.utc.localize(dt)
    epoch_seconds = (dt - _EPOCH_DT).total_seconds()
    ts = int(epoch_seconds * 1000)
    return ts


def append_query_parms(query_parms, prop_name, prop_match):
    """
    Append prop_name=prop_match to query_parms. prop_match may be a list.
    """
    if isinstance(prop_match, (list, tuple)):
        for pm in prop_match:
            append_query_parms(query_parms, prop_name, pm)
    else:
        # Just in case, we also escape the property name
        parm_name = quote(prop_name, safe='')
        parm_value = quote(str(prop_match), safe='')
        qp = '{}={}'.format(parm_name, parm_value)
        query_parms.append(qp)
