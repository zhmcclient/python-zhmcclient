#!/usr/bin/env python
# Copyright 2016,2022 IBM Corp. All Rights Reserved.
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
Example that lists the Adapter, Port and Virtual Switch resources on a CPC
in DPM mode.
"""

import sys
import requests.packages.urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions

requests.packages.urllib3.disable_warnings()

# Get HMC info from HMC inventory and vault files
hmc_def = hmc_definitions()[0]
nickname = hmc_def.nickname
host = hmc_def.host
userid = hmc_def.userid
password = hmc_def.password
verify_cert = hmc_def.verify_cert

print(__doc__)

print(f"Using HMC {nickname} at {host} with userid {userid} ...")

print("Creating a session with the HMC ...")
try:
    session = zhmcclient.Session(
        host, userid, password, verify_cert=verify_cert)
except zhmcclient.Error as exc:
    print(f"Error: Cannot establish session with HMC {host}: "
          f"{exc.__class__.__name__}: {exc}")
    sys.exit(1)

try:
    client = zhmcclient.Client(session)

    print("Finding a CPC in DPM mode ...")
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
    if not cpcs:
        print(f"Error: HMC at {host} does not manage any CPCs in DPM mode")
        sys.exit(1)
    cpc = cpcs[0]
    print(f"Using CPC {cpc.name}")

    print(f"Listing adapters on CPC {cpc.name} ...")
    adapters = cpc.adapters.list()
    for adapter in adapters:
        card_type = adapter.get_property('detected-card-type')
        print(f"{adapter.name} ({card_type})")
        ports = adapter.ports.list(full_properties=False)
        for port in ports:
            print(f"\t{port.name}")

    print("Listing virtual switches and backing adapters on CPC "
          f"{cpc.name} ...")
    vswitches = cpc.vswitches.list()
    for vswitch in vswitches:
        backing_adapter_uri = vswitch.get_property('backing-adapter-uri')
        backing_adapter = vswitch.manager.resource_object(backing_adapter_uri)
        print(f"{vswitch.name} (adapter: {backing_adapter.name})")

finally:
    print("Logging off ...")
    session.logoff()
