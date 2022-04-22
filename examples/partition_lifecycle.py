#!/usr/bin/env python
# Copyright 2016-2022 IBM Corp. All Rights Reserved.
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
Example that performs a create-read-update-delete lifecycle of a partition
on a CPC in DPM mode.
"""

import sys
import uuid
import requests.packages.urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions

requests.packages.urllib3.disable_warnings()

# Get HMC info from HMC definition file
hmc_def = hmc_definitions()[0]
nick = hmc_def.nickname
host = hmc_def.hmc_host
userid = hmc_def.hmc_userid
password = hmc_def.hmc_password
verify_cert = hmc_def.hmc_verify_cert

print(__doc__)

print("Using HMC {} at {} with userid {} ...".format(nick, host, userid))

print("Creating a session with the HMC ...")
try:
    session = zhmcclient.Session(
        host, userid, password, verify_cert=verify_cert)
except zhmcclient.Error as exc:
    print("Error: Cannot establish session with HMC {}: {}: {}".
          format(host, exc.__class__.__name__, exc))
    sys.exit(1)

try:
    client = zhmcclient.Client(session)

    print("Finding a CPC in DPM mode ...")
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
    if not cpcs:
        print("Error: HMC at {} does not manage any CPCs in DPM mode".
              format(host))
        sys.exit(1)
    cpc = cpcs[0]
    print("Using CPC {}".format(cpc.name))

    part_name = "zhmc_test_{}".format(uuid.uuid4())
    print("Creating partition {} ...".format(part_name))
    part_props = {
        'name': part_name,
        'description': 'Original partition description.',
        'cp-processors': 2,
        'initial-memory': 1024,
        'maximum-memory': 2048,
        'processor-mode': 'shared',
        'boot-device': 'test-operating-system'
    }
    try:
        part = cpc.partitions.create(properties=part_props)
    except zhmcclient.Error as exc:
        print("Error: Cannot create partition {} on CPC {}: {}: {}".
              format(part_name, cpc.name, exc.__class__.__name__, exc))
        sys.exit(1)

    print("Starting partition {} ...".format(part.name))
    part.start()

    print("Current partition description: {}".
          format(part.get_property('description')))
    new_description = "Updated partition description."
    updated_properties = dict()
    updated_properties["description"] = new_description

    print("Updating partition description to: {}".format(new_description))
    part.update_properties(updated_properties)

    print("Partition description on local resource object: {}".
          format(part.get_property('description')))

    print("Refreshing properties of local resource object ...")
    part.pull_full_properties()
    print("Partition description on local resource object: {}".
          format(part.get_property('description')))

finally:
    print("Logging off ...")
    session.logoff()
