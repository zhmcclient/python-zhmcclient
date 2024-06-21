#!/usr/bin/env python
# Copyright 2017,2022 IBM Corp. All Rights Reserved.
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
Example that retrieves certain resource classes from the inventory.
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

    resource_classes = ['cpc', 'partition', 'adapter']
    rc_str = ', '.join(resource_classes)
    print(f"Retrieving inventory for resource classes: {rc_str} ...")
    resources = client.get_inventory(resource_classes)

    print("Returned resources with a subset of properties in the returned "
          "order:")
    format_str = "{:<24s} {:<24s} {}"
    print(format_str.format("Class", "Name", "URI"))
    for res in resources:
        name = res.get('name', '<no name>')
        uri = res.get('object-uri') or res.get('element-uri')
        line = format_str.format(res['class'], name, uri)
        print(line)

finally:
    print("Logging off ...")
    session.logoff()
