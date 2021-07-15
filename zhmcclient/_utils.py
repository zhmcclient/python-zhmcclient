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
Utility functions.
"""

from __future__ import absolute_import

import re
from collections import OrderedDict
try:
    from collections.abc import Mapping, MutableSequence, Iterable
except ImportError:
    # pylint: disable=deprecated-class
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
        new_exc = ValueError(str(exc))
        new_exc.__cause__ = None
        raise new_exc  # ValueError
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


def divide_filter_args(query_props, filter_args):
    """
    Divide the filter arguments into filter query parameters for filtering
    on the server side, and the remaining client-side filters.

    Parameters:

      query_props (iterable of strings):
        Names of resource properties that are supported as filter query
        parameters in the WS API operation (i.e. server-side filtering).

        May be `None`.

        If the support for a resource property changes within the set of
        HMC versions that support this type of resource, this list must
        represent the version of the HMC this session is connected to.

      filter_args (dict):
        Filter arguments that narrow the list of returned resources to
        those that match the specified filter arguments. For details, see
        :ref:`Filtering`.

        `None` causes no filtering to happen, i.e. all resources are
        returned.

    Returns:

      : tuple (query_parms_str, client_filter_args)
    """
    query_parms = []  # query parameter strings
    client_filter_args = {}

    if filter_args is not None:
        for prop_name in filter_args:
            prop_match = filter_args[prop_name]
            if prop_name in query_props:
                append_query_parms(query_parms, prop_name, prop_match)
            else:
                client_filter_args[prop_name] = prop_match
    query_parms_str = '&'.join(query_parms)
    if query_parms_str:
        query_parms_str = '?{}'.format(query_parms_str)

    return query_parms_str, client_filter_args


def matches_filters(obj, filter_args):
    """
    Return a boolean indicating whether a resource object matches a set
    of filter arguments.

    This is used for client-side filtering.

    Depending on the properties specified in the filter arguments, this
    method retrieves the resource properties from the HMC.

    Parameters:

      obj (BaseResource):
        Resource object.

      filter_args (dict):
        Filter arguments. For details, see :ref:`Filtering`.
        `None` causes the resource to always match.

    Returns:

      bool: Boolean indicating whether the resource object matches the
        filter arguments.
    """
    if filter_args is not None:
        for prop_name in filter_args:
            prop_match = filter_args[prop_name]
            if not matches_prop(obj, prop_name, prop_match):
                return False
    return True


def matches_prop(obj, prop_name, prop_match):
    """
    Return a boolean indicating whether a resource object matches with
    a single property against a property match value.

    This is used for client-side filtering.

    Depending on the specified property, this method retrieves the resource
    properties from the HMC.

    Parameters:

      obj (BaseResource):
        Resource object.

      prop_match:
        Property match value that is used to match the actual value of
        the specified property against, as follows:

        - If the match value is a list or tuple, this method is invoked
          recursively to find whether one or more match values inthe list
          match.

        - Else if the property is of string type, its value is matched by
          interpreting the match value as a regular expression.

        - Else the property value is matched by exact value comparison
          with the match value.

    Returns:

      bool: Boolean indicating whether the resource object matches w.r.t.
        the specified property and the match value.
    """
    if isinstance(prop_match, (list, tuple)):
        # List items are logically ORed, so one matching item suffices.
        for pm in prop_match:
            if matches_prop(obj, prop_name, pm):
                return True
    else:
        # Some lists of resources do not have all properties, for example
        # Hipersocket adapters do not have a "card-location" property.
        # If a filter property does not exist on a resource, the resource
        # does not match.
        try:
            prop_value = obj.get_property(prop_name)
        except KeyError:
            return False
        if isinstance(prop_value, six.string_types):
            # HMC resource property is Enum String or (non-enum) String,
            # and is both matched by regexp matching. Ideally, regexp
            # matching should only be done for non-enum strings, but
            # distinguishing them is not possible given that the client
            # has no knowledge about the properties.

            # The regexp matching implemented in the HMC requires begin and
            # end of the string value to match, even if the '^' for begin
            # and '$' for end are not specified in the pattern. The code
            # here is consistent with that: We add end matching to the
            # pattern, and begin matching is done by re.match()
            # automatically.
            re_match = prop_match + '$'
            m = re.match(re_match, prop_value)
            if m:
                return True
        else:
            if prop_value == prop_match:
                return True
    return False
