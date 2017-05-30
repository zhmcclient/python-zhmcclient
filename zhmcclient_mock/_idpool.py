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
The :class:`~zhmcclient_mock.IdPool` class provides a pool of integer ID values
from a defined value range. This is used for example to manage automatically
allocated device numbers.
"""

from __future__ import absolute_import

__all__ = ['IdPool']


class IdPool(object):
    """
    A pool of integer ID values from a defined value range.

    The IDs can be allocated from and returned to the pool.

    The pool is optimized for memory consumption, by only materializing ID
    values as needed.
    """

    def __init__(self, lowest, highest):
        """
        Parameters:

          lowest (integer): Lowest value of the ID value range.

          highest (integer): Highest value of the ID value range.
        """

        if lowest > highest:
            raise ValueError("Lowest value %d is higher than highest %d" %
                             (lowest, highest))

        # ID value range, using slice semantics (end points past the highest)
        self._range_start = lowest
        self._range_end = highest + 1

        # The ID values in use.
        self._used = set()

        # Free pool: The ID values that are free and materialized.
        self._free = set()

        # Start of new free ID values to be materialized when the free pool is
        # expanded.
        self._expand_start = lowest

        # Expansion chunk size: Number of new free ID values to be materialized
        # when the free pool is expanded.
        self._expand_len = 10

    def _expand(self):
        """
        Expand the free pool, if possible.

        If out of capacity w.r.t. the defined ID value range, ValueError is
        raised.
        """
        assert not self._free  # free pool is empty
        expand_end = self._expand_start + self._expand_len
        if expand_end > self._range_end:
            # This happens if the size of the value range is not a multiple
            # of the expansion chunk size.
            expand_end = self._range_end
        if self._expand_start == expand_end:
            raise ValueError("Out of capacity in ID pool")
        self._free = set(range(self._expand_start, expand_end))
        self._expand_start = expand_end

    def alloc(self):
        """
        Allocate an ID value and return it.

        Raises:
            ValueError: Out of capacity in ID pool.
        """
        if not self._free:
            self._expand()
        id = self._free.pop()
        self._used.add(id)
        return id

    def free(self, id):
        """
        Free an ID value.

        The ID value must be allocated.

        Raises:
            ValueError: ID value to be freed is not currently allocated.
        """
        self._free_impl(id, fail_if_not_allocated=True)

    def free_if_allocated(self, id):
        """
        Free an ID value, if it is currently allocated.

        If the specified ID value is not currently allocated, nothing happens.
        """
        self._free_impl(id, fail_if_not_allocated=False)

    def _free_impl(self, id, fail_if_not_allocated):
        if id in self._used:
            self._used.remove(id)
            self._free.add(id)
        elif fail_if_not_allocated:
            raise ValueError("ID value to be freed is not currently "
                             "allocated: %d" % id)
