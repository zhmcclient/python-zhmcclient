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

"""
Tests for time statistics (`_timestats` module).
"""

from __future__ import absolute_import, print_function

import time
import unittest

from zhmcclient import TimeStatsKeeper


PRINT_HEADER = \
    "Time statistics (times in seconds):\n" \
    "Count  Average  Minimum  Maximum  Operation name"

PRINT_HEADER_DISABLED = \
    "Time statistics (times in seconds):\n" \
    "Disabled."


def time_equal(t1, t2, delta):
    """
    Return True if two float values are nearly equal (as defined by delta).
    """
    return abs(t1 - t2) < delta


class TimeStatsTests(unittest.TestCase):
    """All tests for TimeStatsKeeper and TimeStats."""

    def test_enabling(self):
        """Test enabling and disabling."""

        keeper = TimeStatsKeeper()

        self.assertFalse(keeper.enabled,
                         "Verify that initial state is disabled")

        keeper.disable()
        self.assertFalse(keeper.enabled,
                         "Verify that disabling a disabled keeper works")

        keeper.enable()
        self.assertTrue(keeper.enabled,
                        "Verify that enabling a disabled keeper works")

        keeper.enable()
        self.assertTrue(keeper.enabled,
                        "Verify that enabling an enabled keeper works")

        keeper.disable()
        self.assertFalse(keeper.enabled,
                         "Verify that disabling an enabled keeper works")

    def test_get(self):
        """Test getting time statistics."""

        keeper = TimeStatsKeeper()
        snapshot_length = len(keeper.snapshot())
        self.assertEqual(snapshot_length, 0,
                         "Verify that initial state has no time statistics. "
                         "Actual number = %d" % snapshot_length)

        stats = keeper.get_stats('foo')
        snapshot_length = len(keeper.snapshot())
        self.assertEqual(snapshot_length, 0,
                         "Verify that getting a new stats with a disabled "
                         "keeper results in no time statistics. "
                         "Actual number = %d" % snapshot_length)
        self.assertEqual(stats.keeper, keeper)
        self.assertEqual(stats.name, "disabled")  # stats for disabled keeper
        self.assertEqual(stats.count, 0)
        self.assertEqual(stats.avg_time, 0)
        self.assertEqual(stats.min_time, float('inf'))
        self.assertEqual(stats.max_time, 0)

        keeper.enable()

        stats = keeper.get_stats('foo')
        snapshot_length = len(keeper.snapshot())
        self.assertEqual(snapshot_length, 1,
                         "Verify that getting a new stats with an enabled "
                         "keeper results in one time statistics. "
                         "Actual number = %d" % snapshot_length)

        self.assertEqual(stats.keeper, keeper)
        self.assertEqual(stats.name, 'foo')
        self.assertEqual(stats.count, 0)
        self.assertEqual(stats.avg_time, 0)
        self.assertEqual(stats.min_time, float('inf'))
        self.assertEqual(stats.max_time, 0)

        keeper.get_stats('foo')
        snapshot_length = len(keeper.snapshot())
        self.assertEqual(snapshot_length, 1,
                         "Verify that getting an existing stats with an "
                         "enabled keeper results in the same number of time "
                         "statistics. "
                         "Actual number = %d" % snapshot_length)

    def test_measure_enabled(self):
        """Test measuring time with enabled keeper."""

        keeper = TimeStatsKeeper()
        keeper.enable()

        duration = 0.2
        delta = duration / 100

        stats = keeper.get_stats('foo')
        stats.begin()
        time.sleep(duration)
        stats.end()

        for _, stats in keeper.snapshot():
            self.assertEqual(stats.count, 1)
            self.assertTrue(time_equal(stats.avg_time, duration, delta))
            self.assertTrue(time_equal(stats.min_time, duration, delta))
            self.assertTrue(time_equal(stats.max_time, duration, delta))

        stats.reset()
        self.assertEqual(stats.count, 0)
        self.assertEqual(stats.avg_time, 0)
        self.assertEqual(stats.min_time, float('inf'))
        self.assertEqual(stats.max_time, 0)

    def test_measure_disabled(self):
        """Test measuring time with disabled keeper."""

        keeper = TimeStatsKeeper()

        duration = 0.2

        stats = keeper.get_stats('foo')
        self.assertEqual(stats.name, 'disabled')

        stats.begin()
        time.sleep(duration)
        stats.end()

        for _, stats in keeper.snapshot():
            self.assertEqual(stats.count, 0)
            self.assertEqual(stats.avg_time, 0)
            self.assertEqual(stats.min_time, float('inf'))
            self.assertEqual(stats.max_time, 0)

    def test_snapshot(self):
        """Test that snapshot() takes a stable snapshot."""

        keeper = TimeStatsKeeper()
        keeper.enable()

        duration = 0.2
        delta = duration / 100

        stats = keeper.get_stats('foo')
        stats.begin()
        time.sleep(duration)
        stats.end()

        # take the snapshot
        snapshot = keeper.snapshot()

        # keep producing statistics data
        stats.begin()
        time.sleep(duration * 2)
        stats.end()

        # verify that only the first set of data is in the snapshot
        for _, stats in snapshot:
            self.assertEqual(stats.count, 1)
            self.assertTrue(time_equal(stats.avg_time, duration, delta))
            self.assertTrue(time_equal(stats.min_time, duration, delta))
            self.assertTrue(time_equal(stats.max_time, duration, delta))

    def test_str_empty(self):
        """Test str() for an empty enabled keeper."""

        keeper = TimeStatsKeeper()
        keeper.enable()
        s = str(keeper)
        self.assertEqual(s, PRINT_HEADER)

    def test_str_disabled(self):
        """Test str() for a disabled keeper."""

        keeper = TimeStatsKeeper()
        s = str(keeper)
        self.assertEqual(s, PRINT_HEADER_DISABLED)


if __name__ == '__main__':
    unittest.main()
