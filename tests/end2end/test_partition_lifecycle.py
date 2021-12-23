# Copyright 2017-2021 IBM Corp. All Rights Reserved.
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

# pylint: disable=attribute-defined-outside-init

"""
End2end tests for partition lifecycle in DPM mode.

Only tested on CPCs in DPM mode, and skipped otherwise.
"""

from __future__ import absolute_import, print_function

import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils.hmc_definition_fixtures import hmc_definition, hmc_session  # noqa: F401, E501
# pylint: disable=unused-import

urllib3.disable_warnings()


def test_crud(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a partition.
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition
    for cpc_name in hd.cpcs:
        cpc = client.cpcs.find_by_name(cpc_name)
        if not cpc.get_property('dpm-enabled'):
            pytest.skip("CPC {} is not in DPM mode".format(cpc_name))

    part_name = 'test_crud.part1'

    # Ensure a clean starting point for this test
    try:
        part = cpc.partitions.find(name=part_name)
    except zhmcclient.NotFound:
        pass
    else:
        status = part.get_property('status')
        if status != 'stopped':
            part.stop()
        part.delete()

    # Test creating the partition

    part_input_props = {
        'name': part_name,
        'description': 'Dummy partition description.',
        'ifl-processors': 2,
        'initial-memory': 1024,
        'maximum-memory': 2048,
        'processor-mode': 'shared',  # used for filtering
        'type': 'linux',  # used for filtering
    }
    part_auto_props = {
        'status': 'stopped',
    }

    part = cpc.partitions.create(part_input_props)

    for pn, exp_value in part_input_props.items():
        assert part.properties[pn] == exp_value, \
            "Unexpected value for property {!r}".format(pn)
    part.pull_full_properties()
    for pn, exp_value in part_input_props.items():
        assert part.properties[pn] == exp_value, \
            "Unexpected value for property {!r}".format(pn)
    for pn, exp_value in part_auto_props.items():
        assert part.properties[pn] == exp_value, \
            "Unexpected value for property {!r}".format(pn)

    # Test finding the partition based on its (cached) name

    p = cpc.partitions.find(name=part_name)

    assert p.name == part_name

    # Test finding the partition based on a server-side filtered prop

    parts = cpc.partitions.findall(type='linux')

    assert part_name in [p.name for p in parts]  # noqa: F812

    # Test finding the partition based on a client-side filtered prop

    parts = cpc.partitions.findall(**{'processor-mode': 'shared'})

    assert part_name in [p.name for p in parts]  # noqa: F812

    # Test updating a property of the partition

    new_desc = "Updated partition description."

    part.update_properties(dict(description=new_desc))

    assert part.properties['description'] == new_desc
    part.pull_full_properties()
    assert part.properties['description'] == new_desc

    # Test deleting the partition

    part.delete()

    with pytest.raises(zhmcclient.NotFound):
        cpc.partitions.find(name=part_name)
