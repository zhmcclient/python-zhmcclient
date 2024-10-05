#!/usr/bin/env python
# Copyright 2025 IBM Corp. All Rights Reserved.
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
Example that lists partition links attached to a partition.
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

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} CPC PARTITION")
    sys.exit(2)

cpc_name = sys.argv[1]
part_name = sys.argv[2]

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
    console = client.consoles.console

    print(f"Finding partition {part_name} on CPC {cpc_name} ...")
    cpc = client.cpcs.find(name=cpc_name)
    part = cpc.partitions.find(name=part_name)

    print(f"Listing partition links attached to partition {part_name} ...")
    partition_links = part.list_attached_partition_links()

    print()
    print("Partition Link        Type          State       Attached partitions")
    print("---------------------------------------------------------------------------------------")
    for pl in partition_links:
        name = pl.get_property('name')
        type = pl.get_property('type')
        state = pl.get_property('state')
        attached_parts = pl.list_attached_partitions()
        attached_part_names = [p.name for p in attached_parts]
        print(f"{name:20s}  {type:12s}  {state:10}  {', '.join(attached_part_names)}")
    print()

finally:
    print("Logging off ...")
    session.logoff()
