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
Unit tests for _idpool module of the zhmcclient_mock package.
"""


from requests.packages import urllib3
import pytest

from zhmcclient_mock._idpool import IdPool

urllib3.disable_warnings()


def test_init_error_1():
    """
    Test invalid IdPool.__init__() with lowest > highest.
    """

    with pytest.raises(ValueError):
        IdPool(7, 6)


def test_invalid_free_error_1():
    """
    Test invalid IdPool.free() in some variations.
    """

    pool = IdPool(5, 5)

    with pytest.raises(ValueError):
        pool.free(4)  # not in range

    with pytest.raises(ValueError):
        pool.free(5)  # in range but not allocated

    with pytest.raises(ValueError):
        pool.free(6)  # not in range


def test_invalid_free_error_2():
    """
    Test invalid IdPool.free_if_allocated() in some variations.
    """

    pool = IdPool(5, 5)

    pool.free_if_allocated(4)  # not in range (= not allocated)

    pool.free_if_allocated(5)  # in range but not allocated

    pool.free_if_allocated(6)  # not in range (= not allocated)


def _test_exhausting_for_lo_hi(lowest, highest):
    """
    Internal helper function that tests exhausting an IdPool.
    """

    start = lowest
    end = highest + 1

    pool = IdPool(lowest, highest)

    # Exhaust the pool
    id_list = []
    for _ in range(start, end):
        _id = pool.alloc()
        id_list.append(_id)

    # Verify uniqueness of the ID values
    id_set = set(id_list)
    assert len(id_set) == len(id_list)

    # Verify that the pool is exhausted
    with pytest.raises(ValueError):
        pool.alloc()


def _test_free_for_lo_hi(lowest, highest):
    """
    Internal helper function that tests exhausting, freeing, and again
    exhausting an IdPool.
    """

    start = lowest
    end = highest + 1

    pool = IdPool(lowest, highest)

    # Exhaust the pool
    id_list1 = []
    for _ in range(start, end):
        _id = pool.alloc()
        id_list1.append(_id)

    # Return everything to the pool
    for _id in id_list1:
        pool.free(_id)

    # Verify that nothing is used in the pool
    assert len(pool._used) == 0  # pylint: disable=protected-access

    # Exhaust the pool
    id_list2 = []
    for _ in range(start, end):
        _id = pool.alloc()
        id_list2.append(_id)

    # Verify that the same ID values came back as last time
    assert set(id_list1) == set(id_list2)

    # Verify that the pool is exhausted
    with pytest.raises(ValueError):
        pool.alloc()


TESTCASES_LO_HI = [
    (0, 0),
    (0, 1),
    (0, 9),
    (0, 10),
    (0, 11),
    (0, 19),
    (0, 20),
    (0, 21),
    (3, 3),
    (3, 4),
    (3, 9),
    (3, 10),
    (3, 11),
    (3, 12),
    (3, 13),
    (3, 14),
    (9, 9),
    (9, 10),
    (9, 11),
    (9, 18),
    (9, 19),
    (9, 20),
    (10, 10),
    (10, 11),
    (10, 19),
    (10, 20),
    (10, 21),
    (11, 11),
    (11, 12),
    (11, 20),
    (11, 21),
    (11, 22),
]


@pytest.mark.parametrize("lowest, highest", TESTCASES_LO_HI)
def test_lo_hi(lowest, highest):
    """
    Test pool exhaustion, etc. for some pool sizes.

    Knowing that the chunk size is 10, we focus on the sizes and range
    boundaries around that
    """
    _test_exhausting_for_lo_hi(lowest, highest)
    _test_free_for_lo_hi(lowest, highest)
