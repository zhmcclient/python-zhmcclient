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
The :class:`~zhmcclient.TimeStatsKeeper` class allows measuring the elapsed
time of accordingly instrumented code and keeps a statistics of these times.

The :class:`~zhmcclient.Session` class uses this class for keeping
statistics about the time to issue HTTP requests against the HMC API (see its
:attr:`~zhmcclient.Session.time_stats_keeper` property).

The :class:`~zhmcclient.TimeStats` class is a helper class that contains the
actual measurement data for all invocations of a particular HTTP request. Its
objects are under control of the :class:`~zhmcclient.TimeStatsKeeper` class.

Example::

    import zhmcclient

    session = zhmcclient.Session(hmc, userid, password)
    session.time_stats_keeper.enable()

    # Some operations that are being measured
    client = zhmcclient.Client(session)
    cpcs = client.cpcs.list()

    print(session.time_stats_keeper)
"""

from __future__ import absolute_import

import time
import copy

from ._logging import logged_api_call

__all__ = ['TimeStatsKeeper', 'TimeStats']


class TimeStats(object):
    """
    Elapsed time statistics for all invocations of a particular named
    operation.

    All invocations of the operation will be accumulated into the statistics
    data kept by an object of this class.

    Objects of this class don't need to (and in fact, are not supposed to) be
    created by the user. Instead, the
    :meth:`zhmcclient.TimeStatsKeeper.get_stats` method should be used to
    create objects of this class.
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
        self._begin_time = None

    @property
    def name(self):
        """
        :term:`string`: Name of the operation this time statistics has data
        for.

        This name is used by the :class:`~zhmcclient.TimeStatsKeeper` object
        holding this time statistics as a key.
        """
        return self._name

    @property
    def keeper(self):
        """
        :class:`~zhmcclient.TimeStatsKeeper`: The time statistics keeper
        holding this time statistics.
        """
        return self._keeper

    @property
    def count(self):
        """
        :term:`integer`: The number of invocations of the operation.
        """
        return self._count

    @property
    def avg_time(self):
        """
        float: The average elapsed time for invoking the operation, in seconds.
        """
        try:
            return self._sum / self._count
        except ZeroDivisionError:
            return 0

    @property
    def min_time(self):
        """
        float: The minimum elapsed time for invoking the operation, in seconds.
        """
        return self._min

    @property
    def max_time(self):
        """
        float: The maximum elapsed time for invoking the operation, in seconds.
        """
        return self._max

    @logged_api_call
    def reset(self):
        """
        Reset the time statistics data for the operation.
        """
        self._count = 0
        self._sum = float(0)
        self._min = float('inf')
        self._max = float(0)

    @logged_api_call
    def begin(self):
        """
        This method must be called before invoking the operation.
        Note that this method is not to be invoked by the user; it is invoked
        by the implementation of the :class:`~zhmcclient.Session` class.

        If the statistics keeper holding this time statistics is enabled, this
        method takes the current time, so that
        :meth:`~zhmcclient.TimeStats.end` can calculate the elapsed time
        between the two method calls.

        If the statistics keeper holding this time statistics is disabled,
        this method does nothing, in order to save resources.
        """
        if self.keeper.enabled:
            self._begin_time = time.time()

    @logged_api_call
    def end(self):
        """
        This method must be called after the operation returns.
        Note that this method is not to be invoked by the user; it is invoked
        by the implementation of the :class:`~zhmcclient.Session` class.

        If the statistics keeper holding this time statistics is enabled, this
        method takes the current time, calculates the duration of the operation
        since the last call to :meth:`~zhmcclient.TimeStats.begin`, and updates
        the time statistics to reflect the new operation.

        If the statistics keeper holding this time statistics is disabled,
        this method does nothing, in order to save resources.

        If this method is called without a preceding call to
        :meth:`~zhmcclient.TimeStats.begin`, a :exc:`py:RuntimeError` is
        raised.

        Raises:
          RuntimeError
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

    def __str__(self):
        """
        Return a human readable string with the time statistics for this
        operation.

        Example result:

        .. code-block:: text

            TimeStats: count=1 avg=1.000s min=1.000s max=1.000s get /api/cpcs
        """
        return "TimeStats: count={:d} avg={:.3f}s min={:.3f}s "\
               "max={:.3f}s {}".format(
                   self.count, self.avg_time, self.min_time, self.max_time,
                   self.name)


class TimeStatsKeeper(object):
    """
    Statistics keeper for elapsed times.

    The statistics keeper can hold multiple time statistics (see
    :class:`~zhmcclient.TimeStats`), that are identified by a name.

    The statistics keeper can be in a state of enabled or disabled. If enabled,
    it accumulates the elapsed times between subsequent calls to the
    :meth:`~zhmcclient.TimeStats.begin` and :meth:`~zhmcclient.TimeStats.end`
    methods of class :class:`~zhmcclient.TimeStats`.
    If disabled, calls to these methods do not accumulate any time.

    Initially, the statistics keeper is disabled.
    """

    def __init__(self):
        self._enabled = False
        self._time_stats = {}  # TimeStats objects
        self._disabled_stats = TimeStats(self, "disabled")

    @property
    def enabled(self):
        """
        Indicates whether the statistics keeper is enabled.
        """
        return self._enabled

    @logged_api_call
    def enable(self):
        """
        Enable the statistics keeper.
        """
        self._enabled = True

    @logged_api_call
    def disable(self):
        """
        Disable the statistics keeper.
        """
        self._enabled = False

    @logged_api_call
    def get_stats(self, name):
        """
        Get the time statistics for a name.
        If a time statistics for that name does not exist yet, create one.

        Parameters:

          name (string):
            Name of the time statistics.

        Returns:

          TimeStats: The time statistics for the specified name. If the
          statistics keeper is disabled, a dummy time statistics object is
          returned, in order to save resources.
        """
        if not self.enabled:
            return self._disabled_stats
        if name not in self._time_stats:
            self._time_stats[name] = TimeStats(self, name)
        return self._time_stats[name]

    @logged_api_call
    def snapshot(self):
        """
        Return a snapshot of the time statistics of this keeper.

        The snapshot represents the statistics data at the time this method
        is called, and remains unchanged even if the statistics of this keeper
        continues to be updated.

        Returns:

         dict: A dictionary of the time statistics by operation, where:

          - key (:term:`string`): Name of the operation
          - value (:class:`~zhmcclient.TimeStats`): Time statistics for the
            operation
        """
        return copy.deepcopy(self._time_stats)

    def __str__(self):
        """
        Return a human readable string with the time statistics for this
        keeper. The operations are sorted by decreasing average time.

        Example result, if keeper is enabled:

        .. code-block:: text

            Time statistics (times in seconds):
            Count  Average  Minimum  Maximum  Operation name
                1  0.024    0.024    0.024    get /api/cpcs
                1  0.009    0.009    0.009    get /api/version
        """
        ret = "Time statistics (times in seconds):\n"
        if self.enabled:
            ret += "Count  Average  Minimum  Maximum  Operation name\n"
            stats_dict = self.snapshot()
            snapshot_by_avg = sorted(stats_dict.items(),
                                     key=lambda item: item[1].avg_time,
                                     reverse=True)
            for name, stats in snapshot_by_avg:
                ret += "{:5d}  {:7.3f}  {:7.3f}  {:7.3f}  {}\n".format(
                    stats.count, stats.avg_time, stats.min_time,
                    stats.max_time, name)
        else:
            ret += "Disabled.\n"
        return ret.strip()
