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
These classes allow measuring the elapsed time of accordingly instrumented code
and keeping a statistics of these times.

The :class:`~zhmcclient.Session` class uses these classes for keeping
statistics about the time to issue HTTP requests against the HMC API (see its
:attr:`~zhmcclient.Session.time_stats_keeper` property).

Example for measuring the HMC API operations:

::

    import zhmcclient

    # keeper is created as an instance variable of Session
    session = zhmcclient.Session(hmc, userid, password)

    # enable the keeper
    session.time_stats_keeper.enable()

    # perform some operations
    client = zhmcclient.Client(session)
    cpcs = client.cpcs.list()

    # print the time statistics
    session.time_stats_keeper.print()

These classes can also be used independent of the ``zhmcclient`` package.

Example for such independent use:

::

    import zhmcclient

    # create and enable the keeper
    keeper = zhmcclient.TimeStatsKeeper()
    keeper.enable()

    # measure an operation
    stats = keeper.get_stats('my_operation')
    stats.begin()
    my_operation()
    stats.end()

    # print the time statistics
    keeper.print()

"""

from __future__ import absolute_import, print_function

import time

__all__ = ['TimeStatsKeeper', 'TimeStats']


class TimeStats(object):
    """
    Elapsed time statistics for one particular kind of operation.
    """

    def __init__(self, keeper, name):
        """
        Parameters:

          keeper (TimeStatsKeeper):
            The statistics keeper that holds this time statistics.

          name (string):
            Name of the operation.
        """
        self._keeper = keeper
        self._name = name
        self._count = 0
        self._sum = float(0)
        self._min = float('inf')
        self._max = float(0)

    @property
    def name(self):
        """
        string: Name of the operation this time statistics has data for.

        This name is used by the :class:`~zhmcclient.TimeStatsKeeper` object
        holding this time statistics as a key.
        """
        return self._name

    @property
    def keeper(self):
        """
        TimeStatsKeeper: The time statistics keeper holding this time
        statistics.
        """
        return self._keeper

    @property
    def count(self):
        """
        integer: The number of measurements.
        """
        return self._count

    @property
    def avg_time(self):
        """
        float: The average elapsed time for issuing the operation, in seconds.
        """
        try:
            return self._sum / self._count
        except ZeroDivisionError:
            return None

    @property
    def min_time(self):
        """
        float: The minimum elapsed time for issuing the operation, in seconds.
        """
        return self._min

    @property
    def max_time(self):
        """
        float: The maximum elapsed time for issuing the operation, in seconds.
        """
        return self._max

    def reset(self):
        """
        Reset the time statistics.
        """
        self._count = 0
        self._sum = float(0)
        self._min = float('inf')
        self._max = float(0)

    def begin(self):
        """
        Must be called at the begin of the measurement.

        It just takes the current time.
        """
        if self.keeper.enabled:
            self._begin_time = time.time()

    def end(self):
        """
        Must be called at the end of the measurement.

        It takes the current time, calculates the duration since the begin
        of the measurement, and updates the statistics with this new duration.
        """
        if self.keeper.enabled:
            if self._begin_time is None:
                raise RuntimeError("end() called without preceding begin()")
            dt = time.time() - self._begin_time
            self._begin_time = None
            self._count += 1
            self._sum += dt
            if dt > self._max:
                self._max = dt
            if dt < self._min:
                self._min = dt


class TimeStatsKeeper(object):
    """
    Statistics keeper for elapsed times.

    The statistics keeper can hold multiple time statistics (see
    :class:`~zhmcclient.TimeStats`), that are identified by a name.

    The statistics keeper can be in a state of enabled or disabled. If enabled,
    it accumulates the elapsed times between subsequent calls to the
    :meth:`start` and :meth:`end` methods. If disabled, calls to these methods
    do not accumulate any time.

    Initially, the statistics keeper is disabled.
    """

    def __init__(self):
        self._enabled = False
        self._time_stats = {}  # TimeStats objects

    @property
    def enabled(self):
        """
        Indicates whether the statistics keeper is enabled.
        """
        return self._enabled

    def enable(self):
        """
        Enable the statistics keeper.
        """
        self._enabled = True

    def disable(self):
        """
        Disable the statistics keeper.
        """
        self._enabled = False

    def get_stats(self, name):
        """
        Get the time statistics for a name.
        If a time statistics for that name does not exist yet, create one.

        Parameters:

          name (string):
            Name of the time statistics.

        Returns:

          TimeStats: The new time statistics. If the statistics keeper is
            disabled, a dummy time statistics, to avoid creating objects
            needlessly.
        """
        if not self.enabled:
            return TimeStats(self, None)
        if name not in self._time_stats:
            self._time_stats[name] = TimeStats(self, name)
        return self._time_stats[name]

    def stats_items(self):
        """
        Return an iterator through the time statistics of this keeper.
        """
        return self._time_stats.items()

    def print(self):
        """
        Print the time statistics to stdout.
        """
        print("Time statistics (times in seconds):")
        if self.enabled:
            print("  count  average  minimum  maximum  operation name")
            for name in self._time_stats:
                stats = self._time_stats[name]
                print("  {:5d}  {:7.3f}  {:7.3f}  {:7.3f}  {}".format(
                      stats.count, stats.avg_time, stats.min_time,
                      stats.max_time, name))
        else:
            print("Disabled.")
