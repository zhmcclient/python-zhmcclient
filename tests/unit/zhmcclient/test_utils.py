# Copyright 2017,2021 IBM Corp. All Rights Reserved.
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
Unit tests for _utils module.
"""


import os
import sys
from datetime import datetime, MAXYEAR
import time
import pytz
import pytest

from zhmcclient._utils import datetime_from_timestamp, \
    timestamp_from_datetime, datetime_to_isoformat, datetime_from_isoformat


# The Unix epoch
EPOCH_DT = datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc)

# HMC timestamp numbers (milliseconds since the Unix epoch)
TS_2000_02_29 = 951782400000  # last day in february in leap year
TS_2001_02_28 = 983318400000  # last day in february in non-leap year
TS_2017_08_15 = 1502755200000  # some day in summer
TS_2038_LIMIT = 2147483647000  # 2038-01-19 03:14:07 UTC (Year 2038 Problem)
TS_3000_12_31 = 32535129600000
TS_3001_LIMIT = 32535244799000  # 3001-01-01 07:59:59 UTC (Visual C++ limit)
TS_MAX = 253402300799999  # 9999-12-31 23:59:59.999 UTC

# Some durations in milliseconds
SEC_MS = 1000
MIN_MS = SEC_MS * 60
HOUR_MS = MIN_MS * 60
DAY_MS = HOUR_MS * 24

# Test cases for datetime / timestamp conversion functions
DATETIME_TIMESTAMP_TESTCASES = [
    # (datetime_tuple(y,m,d,h,m,s,us), timestamp)
    ((1970, 1, 1, 0, 0, 0, 0), 0),
    ((1970, 1, 1, 0, 0, 0, 123000), 123),
    ((1970, 1, 1, 0, 2, 3, 456000), 123456),
    ((1970, 1, 2, 10, 17, 36, 789000), 123456789),
    ((1973, 11, 29, 21, 33, 9, 123000), 123456789123),
    ((2000, 2, 29, 0, 0, 0, 0), TS_2000_02_29),
    ((2000, 3, 1, 0, 0, 0, 0), TS_2000_02_29 + DAY_MS),
    ((2001, 2, 28, 0, 0, 0, 0), TS_2001_02_28),
    ((2001, 3, 1, 0, 0, 0, 0), TS_2001_02_28 + DAY_MS),
    ((2017, 8, 15, 0, 0, 0, 0), TS_2017_08_15),
    ((2038, 1, 19, 3, 14, 7, 0), TS_2038_LIMIT),
    ((2038, 1, 19, 3, 14, 7, 1000), TS_2038_LIMIT + 1),
    ((3000, 12, 31, 23, 59, 59, 999000), TS_3000_12_31 + DAY_MS - 1),
    ((3001, 1, 1, 7, 59, 59, 0), TS_3001_LIMIT),
    ((3001, 1, 1, 8, 0, 0, 0), TS_3001_LIMIT + 1000),
    ((MAXYEAR - 1, 12, 31, 0, 0, 0, 0), TS_MAX + 1 - DAY_MS - 365 * DAY_MS),
    ((MAXYEAR, 12, 30, 0, 0, 0, 0), TS_MAX + 1 - 2 * DAY_MS),
    ((MAXYEAR, 12, 30, 23, 59, 59, 0),
     TS_MAX + 1 - 2 * DAY_MS + 23 * HOUR_MS + 59 * MIN_MS + 59 * SEC_MS),

    # The following testcases would be in range but are too close to the max
    # for pytz due to an implementation limitation: pytz.localize() checks the
    # input +/- 1 day.
    # ((MAXYEAR, 12, 31, 0, 0, 0, 0), TS_MAX + 1 - 1 * DAY_MS),
    # ((MAXYEAR, 12, 31, 23, 59, 59, 0), TS_MAX - 999),
    # ((MAXYEAR, 12, 31, 23, 59, 59, 998000), TS_MAX - 1),
    # ((MAXYEAR, 12, 31, 23, 59, 59, 999000), TS_MAX),
]


def find_max_value(test_func, initial_value):
    """
    Starting from an initial number (integer or float), find the maximum value
    for which the test function does not yet fail, and return that maximum
    value.
    """
    assert isinstance(initial_value, int) and initial_value > 0

    fails = FailsArray(test_func)
    value = initial_value

    # Advance the value exponentially beyond the max value
    while fails[value] == 0:
        value *= 2

    # Search for the exact max value in the previous range. We search for the
    # boundary where the fails array goes from 0 to 1.
    boundary = 0.5
    value = binary_search(fails, boundary, value // 2, value)
    max_value = value - 1

    # Verify that we found exactly the maximum:
    assert fails[max_value] == 0 and fails[max_value + 1] == 1, (
        f"max_value={max_value}, fails[+-2]: {fails[max_value - 2]}, "
        f"{fails[max_value - 1]}, {fails[max_value]}, "
        f"{fails[max_value + 1]}, {fails[max_value + 2]}")

    return max_value


class FailsArray:
    # pylint: disable=too-few-public-methods
    """
    An array that when accessed at an index returns 1 if the array value at
    that index causes an exception to be raised when passed to a test function,
    and 0 otherwise.
    """

    def __init__(self, test_func):
        """
        test_func is a test function that gets one integer argument and that
        raises an exception if the argument is out of range.
        """
        self.test_func = test_func

    def __getitem__(self, test_value):
        """
        Array access function, returning 1 if the given test value caused the
        test function to fail, and 0 otherwise.
        """
        try:
            self.test_func(test_value)
        except Exception:  # pylint: disable=broad-except
            return 1
        return 0


def binary_search(haystack, needle, lo, hi):
    """
    Binary search: Return index of value needle (or the next one if no exact
    match) in array haystack, within index range lo to hi.
    """
    while lo < hi:
        mid = (lo + hi) // 2
        if haystack[mid] > needle:
            hi = mid
        elif haystack[mid] < needle:
            lo = mid + 1
        else:
            return mid
    return hi


# TODO: Add testcases for repr_text() (currently indirectly tested)
# TODO: Add testcases for repr_list() (currently indirectly tested)
# TODO: Add testcases for repr_dict() (currently indirectly tested)
# TODO: Add testcases for repr_timestamp() (currently indirectly tested)
# TODO: Add testcases for repr_manager() (currently indirectly tested)


# Some tests for Python date & time related functions that we use.

def test_gmtime_epoch():
    """Test that time.gmtime() is based upon the UNIX epoch."""
    epoch_st = time.struct_time([1970, 1, 1, 0, 0, 0, 3, 1, 0])
    st = time.gmtime(0)
    assert st == epoch_st


def x_test_print_gmtime_max():
    """Print the maximum for time.gmtime()."""
    max_ts = find_max_value(time.gmtime, 1)
    max_st = time.gmtime(max_ts)
    print("\nMax Unix timestamp value for Python time.gmtime(): "
          f"{max_ts} ({max_st!r})")
    sys.stdout.flush()


def x_test_print_fromtimestamp_max():
    """Print the maximum for datetime.fromtimestamp(utc)."""

    def datetime_fromtimestamp_utc(ts):
        return datetime.fromtimestamp(ts, pytz.utc)

    max_ts = find_max_value(datetime_fromtimestamp_utc, 1)
    max_dt = datetime_fromtimestamp_utc(max_ts)
    print("\nMax Unix timestamp value for Python "
          f"datetime.fromtimestamp(utc): {max_ts} ({max_dt!r})")
    sys.stdout.flush()


def x_test_print_datetime_max():
    """Print datetime.max."""
    print(f"\nMax value for Python datetime (datetime.max): {datetime.max!r}")
    sys.stdout.flush()


# All tests for the datetime_from_timestamp() function.

@pytest.mark.parametrize(
    "tz_name", [None, 'UTC', 'US/Eastern', 'Europe/Berlin']
)
@pytest.mark.parametrize(
    "datetime_tuple, timestamp", DATETIME_TIMESTAMP_TESTCASES
)
def test_success_datetime_from_timestamp(
        datetime_tuple, timestamp, tz_name):
    """Test successful calls to datetime_from_timestamp()."""

    if os.name == 'nt' and timestamp > TS_3001_LIMIT:
        # Skip this test case, due to the lower limit on Windows
        return

    # Expected result, as timezone-unaware (but implied UTC)
    exp_dt_unaware = datetime(*datetime_tuple)

    # Expected result, as timezone-aware
    exp_dt = pytz.utc.localize(exp_dt_unaware)

    if tz_name is None:

        # Execute the code to be tested
        act_dt = datetime_from_timestamp(timestamp)

    else:
        tz = pytz.timezone(tz_name)

        # Execute the code to be tested
        act_dt = datetime_from_timestamp(timestamp, tz)

    # Verify the result.
    # Note: timezone-aware datetime objects compare equal according to
    # their effective point in time (e.g. as if normalized to UTC).
    assert act_dt == exp_dt


@pytest.mark.parametrize(
    "timestamp, exc_type", [
        (None, ValueError),
        (-1, ValueError),
        (TS_MAX + 1, ValueError),
    ]
)
def test_error_datetime_from_timestamp(timestamp, exc_type):
    """Test failing calls to datetime_from_timestamp()."""

    with pytest.raises(Exception) as exc_info:

        # Execute the code to be tested
        datetime_from_timestamp(timestamp)

    # Verify the result
    assert isinstance(exc_info.value, exc_type)


def x_test_print_max_datetime_from_timestamp():
    """Print the maximum for datetime_from_timestamp()."""
    max_ts = find_max_value(datetime_from_timestamp, 1)
    max_dt = datetime_from_timestamp(max_ts)
    print("\nMax HMC timestamp value for zhmcclient."
          f"datetime_from_timestamp(): {max_ts} ({max_dt!r})")
    sys.stdout.flush()


# All tests for the timestamp_from_datetime() function.

@pytest.mark.parametrize(
    "tz_name", [None, 'UTC', 'US/Eastern', 'Europe/Berlin']
)
@pytest.mark.parametrize(
    "datetime_tuple, timestamp", DATETIME_TIMESTAMP_TESTCASES
)
def test_success(datetime_tuple, timestamp, tz_name):
    """Test successful calls to timestamp_from_datetime()."""

    # Create a timezone-naive datetime object
    dt = datetime(*datetime_tuple)
    offset = 0  # because of default UTC

    if tz_name is not None:
        # Make the datetime object timezone-aware
        tz = pytz.timezone(tz_name)
        offset = tz.utcoffset(dt).total_seconds()
        dt = tz.localize(dt)

    exp_ts = timestamp - offset * 1000

    # Execute the code to be tested
    ts = timestamp_from_datetime(dt)

    # Verify the result
    assert ts == exp_ts


@pytest.mark.parametrize(
    "datetime_, exc_type", [
        (None, ValueError),
    ]
)
def test_error(datetime_, exc_type):
    """Test failing calls to timestamp_from_datetime()."""

    with pytest.raises(Exception) as exc_info:

        # Execute the code to be tested
        timestamp_from_datetime(datetime_)

    # Verify the result
    assert isinstance(exc_info.value, exc_type)


def test_datetime_max():
    """Test timestamp_from_datetime() with datetime.max."""

    # The test is that it does not raise an exception:
    timestamp_from_datetime(datetime.max)


# Test cases for datetime_to_isoformat()
TESTCASES_DATETIME_TO_ISOFORMAT = [
    # dt, exp_dt_str
    (
        datetime(2017, 9, 5, 12, 13, 10, 0),
        '2017-09-05 12:13:10'
    ),
    (
        datetime(2017, 9, 5, 12, 13, 10, 123456),
        '2017-09-05 12:13:10.123456'
    ),
    (
        datetime(2017, 9, 5, 12, 13, 10, 0, pytz.utc),
        '2017-09-05 12:13:10+00:00'
    ),
    (
        datetime(2017, 9, 5, 12, 13, 10, 0, pytz.timezone('CET')),
        '2017-09-05 12:13:10+01:00'
    ),
    (
        datetime(2017, 9, 5, 12, 13, 10, 0, pytz.timezone('EST')),
        '2017-09-05 12:13:10-05:00'
    ),
]


@pytest.mark.parametrize(
    "dt, exp_dt_str",
    TESTCASES_DATETIME_TO_ISOFORMAT)
def test_datetime_to_isoformat(dt, exp_dt_str):
    """
    Test function for datetime_to_isoformat().
    """

    # The function to be tested
    dt_str = datetime_to_isoformat(dt)

    assert dt_str == exp_dt_str


# Test cases for datetime_from_isoformat()
TESTCASES_DATETIME_FROM_ISOFORMAT = [
    # dt_str, exp_dt
    (
        '2017-09-05 12:13:10',
        datetime(2017, 9, 5, 12, 13, 10, 0)  # timezone-naive
    ),
    (
        '2017-09-05T12:13:10',
        datetime(2017, 9, 5, 12, 13, 10, 0)  # timezone-naive
    ),
    (
        '2017-09-05 12:13:10.123456',
        datetime(2017, 9, 5, 12, 13, 10, 123456)  # timezone-naive
    ),
    (
        '2017-09-05 12:13:10+00:00',
        datetime(2017, 9, 5, 12, 13, 10, 0, pytz.utc)
    ),
    (
        '2017-09-05 12:13:10+0000',
        datetime(2017, 9, 5, 12, 13, 10, 0, pytz.utc)
    ),
    (
        '2017-09-05 12:13:10+01:00',
        datetime(2017, 9, 5, 12, 13, 10, 0, pytz.timezone('CET'))
    ),
    (
        '2017-09-05 12:13:10+0100',
        datetime(2017, 9, 5, 12, 13, 10, 0, pytz.timezone('CET'))
    ),
    (
        '2017-09-05 12:13:10-05:00',
        datetime(2017, 9, 5, 12, 13, 10, 0, pytz.timezone('EST'))
    ),
]


@pytest.mark.parametrize(
    "dt_str, exp_dt",
    TESTCASES_DATETIME_FROM_ISOFORMAT)
def test_datetime_from_isoformat(dt_str, exp_dt):
    """
    Test function for datetime_from_isoformat().
    """

    # The function to be tested
    dt = datetime_from_isoformat(dt_str)

    assert dt == exp_dt
