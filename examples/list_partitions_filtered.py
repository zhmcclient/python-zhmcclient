#!/usr/bin/env python
# Copyright 2023 IBM Corp. All Rights Reserved.
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
Example that lists partitions with name filtering.
"""

import sys
import requests.packages.urllib3
from datetime import datetime

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

FILTERS_LIST = [
    dict(name=r'olo'),
]

print(__doc__)

if len(sys.argv) <= 1:
    print("Usage: {} CPC [PARTITION]".format(sys.argv[0]))
    print("Where:")
    print("  CPC        Name of the CPC")
    print("  PARTITION  Optional: Filter string for matching the partition name")
    sys.exit(1)

cpc_name = sys.argv[1]
try:
    partition_name_filter = sys.argv[2]
except IndexError:
    partition_name_filter = None

print("Using HMC {} at {} with userid {} ...".format(nickname, host, userid))

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

    cpc = client.cpcs.find(name=cpc_name)
    print("Using CPC {}".format(cpc.name))

    if partition_name_filter:
        filter_args = {'name': partition_name_filter}
    else:
        filter_args = None

    print("\nListing partitions with filter_args={!r} ...".
          format(filter_args))
    partitions = cpc.partitions.list(filter_args=filter_args)
    print("Resulting partitions (sorted):")
    for part in sorted(partitions, key=lambda p: p.name):
        print("  name={}".format(part.name))

finally:
    print("Logging off ...")
    session.logoff()
