# Copyright 2017 IBM Corp. All Rights Reserved.
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
Unit tests for _idpool module of the zhmcclient_mock package.
"""

from __future__ import absolute_import, print_function

import requests.packages.urllib3
import pytest

from zhmcclient_mock._idpool import IdPool

requests.packages.urllib3.disable_warnings()


class TestIdPool(object):
    """All tests for class IdPool."""

    def test_init_error_1(self):

        with pytest.raises(ValueError):
            IdPool(7, 6)

    def test_invalid_free_error_1(self):

        pool = IdPool(5, 5)

        with pytest.raises(ValueError):
            pool.free(4)  # not in range

        with pytest.raises(ValueError):
            pool.free(5)  # in range but not allocated

        with pytest.raises(ValueError):
            pool.free(6)  # not in range

    def test_invalid_free_error_2(self):

        pool = IdPool(5, 5)

        pool.free_if_allocated(4)  # not in range (= not allocated)

        pool.free_if_allocated(5)  # in range but not allocated

        pool.free_if_allocated(6)  # not in range (= not allocated)

    def _test_exhausting_for_lo_hi(self, lowest, highest):
        start = lowest
        end = highest + 1

        pool = IdPool(lowest, highest)

        # Exhaust the pool
        id_list = []
        for i in range(start, end):
            id = pool.alloc()
            id_list.append(id)

        # Verify uniqueness of the ID values
        id_set = set(id_list)
        assert len(id_set) == len(id_list)

        # Verify that the pool is exhausted
        with pytest.raises(ValueError):
            pool.alloc()

    def _test_free_for_lo_hi(self, lowest, highest):
        start = lowest
        end = highest + 1

        pool = IdPool(lowest, highest)

        # Exhaust the pool
        id_list1 = []
        for i in range(start, end):
            id = pool.alloc()
            id_list1.append(id)

        # Return everything to the pool
        for id in id_list1:
            pool.free(id)

        # Verify that nothing is used in the pool
        assert len(pool._used) == 0

        # Exhaust the pool
        id_list2 = []
        for i in range(start, end):
            id = pool.alloc()
            id_list2.append(id)

        # Verify that the same ID values came back as last time
        assert set(id_list1) == set(id_list2)

        # Verify that the pool is exhausted
        with pytest.raises(ValueError):
            pool.alloc()

    def _test_all_for_lo_hi(self, lowest, highest):
        self._test_exhausting_for_lo_hi(lowest, highest)
        self._test_free_for_lo_hi(lowest, highest)

    def test_all(self):
        # Knowing that the chunk size is 10, we focus on the sizes and range
        # boundaries around that
        self._test_all_for_lo_hi(0, 0)
        self._test_all_for_lo_hi(0, 1)
        self._test_all_for_lo_hi(0, 9)
        self._test_all_for_lo_hi(0, 10)
        self._test_all_for_lo_hi(0, 11)
        self._test_all_for_lo_hi(0, 19)
        self._test_all_for_lo_hi(0, 20)
        self._test_all_for_lo_hi(0, 21)
        self._test_all_for_lo_hi(3, 3)
        self._test_all_for_lo_hi(3, 4)
        self._test_all_for_lo_hi(3, 9)
        self._test_all_for_lo_hi(3, 10)
        self._test_all_for_lo_hi(3, 11)
        self._test_all_for_lo_hi(3, 12)
        self._test_all_for_lo_hi(3, 13)
        self._test_all_for_lo_hi(3, 14)
        self._test_all_for_lo_hi(9, 9)
        self._test_all_for_lo_hi(9, 10)
        self._test_all_for_lo_hi(9, 11)
        self._test_all_for_lo_hi(9, 18)
        self._test_all_for_lo_hi(9, 19)
        self._test_all_for_lo_hi(9, 20)
        self._test_all_for_lo_hi(10, 10)
        self._test_all_for_lo_hi(10, 11)
        self._test_all_for_lo_hi(10, 19)
        self._test_all_for_lo_hi(10, 20)
        self._test_all_for_lo_hi(10, 21)
        self._test_all_for_lo_hi(11, 11)
        self._test_all_for_lo_hi(11, 12)
        self._test_all_for_lo_hi(11, 20)
        self._test_all_for_lo_hi(11, 21)
        self._test_all_for_lo_hi(11, 22)
