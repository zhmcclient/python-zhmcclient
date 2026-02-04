# Copyright 2026 IBM Corp. All Rights Reserved.
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
End2end tests for Tape Library (on CPCs in DPM mode).

These tests do not change any existing Tape Library, but discover,
modify and undefine test Tape Libraries.
"""

import pytest
from requests.packages import urllib3

import zhmcclient

from .utils import skip_warn, pick_test_resources, \
    runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic Tape Library objects (e.g. find_by_name())
TL_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Tape Library objects returned by list() without full props
TL_LIST_PROPS = ['object-uri', 'cpc-uri', 'name', 'state']

# Properties whose values can change between retrievals of StorageGroup objs
TL_VOLATILE_PROPS = []


def test_tl_find_list(hmc_session):
    """
    Test list(), find(), findall().
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Pick the Tape Library to test with
    tl_list = console.tape_library.list()
    if not tl_list:
        skip_warn(f"No Tape Library defined on HMC {hd.host}")
    tl_list = pick_test_resources(tl_list)

    for tl in tl_list:
        print(f"Testing with Tape Library {tl.name!r}")
        runtest_find_list(
            hmc_session, console.tape_library, tl.name,
            'name', 'object-uri', TL_VOLATILE_PROPS,
            TL_MINIMAL_PROPS, TL_LIST_PROPS)


def test_tl_property(hmc_session):
    """
    Test property related methods
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Pick the Tape Library to test with
    tl_list = console.tape_library.list()
    if not tl_list:
        skip_warn(f"No Tape Library defined on HMC {hd.host}")
    tl_list = pick_test_resources(tl_list)

    for tl in tl_list:
        print(f"Testing with Tape Library {tl.name!r}")

        # Select a property that is not returned by list()
        non_list_prop = 'description'

        runtest_get_properties(tl.manager, non_list_prop)


def test_tl_crud(hmc_session):
    """
    Test  update Tape Library
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition
    tl_name_new = 'newtl1'

    # Pick the Tape Library to test with
    tl_list = console.tape_library.list()
    if not tl_list:
        skip_warn(f"No Tape Library defined on HMC {hd.host}")
    tl = tl_list[0]

    # Test updating a property of the Tape Library

    new_desc = "Updated Tape Library description."

    # The code to be tested
    tl.update_properties(dict(description=new_desc))

    assert tl.properties['description'] == new_desc
    tl.pull_full_properties()
    assert tl.properties['description'] == new_desc

    # Test that Tape Library can be renamed

    # The code to be tested
    tl.update_properties(dict(name=tl_name_new))
    tl.pull_full_properties()
    with pytest.raises(zhmcclient.NotFound):
        console.tape_library.find(name='Tape Library')
