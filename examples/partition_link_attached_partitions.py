#!/usr/bin/env python
# Copyright 2024 IBM Corp. All Rights Reserved.
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
Example that lists the attached partitions of a partition link.
"""

import sys
import requests.packages.urllib3
from pprint import pprint

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

# Whether to list partition links with full properties
full_properties = False

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

    print(f"\nListing partition links ...")
    partition_links = console.partition_links.list(
        full_properties=full_properties)
    print(f"Number of partition links: {len(partition_links)}")

    print(f"\nAttached partitions for all partition links:")
    for pl in partition_links:
        pl_type = pl.get_property('type')
        pl_state = pl.get_property('state')
        print(f"\nPartition Link {pl.name!r}:")
        print(f"  Type: {pl_type}")
        print(f"  State: {pl_state}")
        print(f"  Attached partitions:")
        parts = pl.list_attached_partitions()
        for part in parts:
            print(f"    {part.name}")

finally:
    print("Logging off ...")
    session.logoff()
