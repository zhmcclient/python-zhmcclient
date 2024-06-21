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
Example that gets the sustainability data of a CPC.
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

range = "last-day"
resolution = "fifteen-minutes"

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
    format_str = "{:<8}  {:<6}  {:<7}  {:<16}"
    rc = 0

    cpcs = client.cpcs.list()
    cpc = cpcs[0]
    print('')
    print(f'Getting sustainability metrics on CPC: {cpc.name}')
    print(f'Range: {range}')
    print(f'Resolution: {resolution}')
    try:
        data = cpc.get_sustainability_data(
            range=range, resolution=resolution)
    except zhmcclient.Error as exc:
        print(f"Error: {exc}")
        rc = 1
    else:
        print('')
        print('CPC sustainability metrics:')
        for metric_name, metric_array in data.items():
            print(f"{metric_name}:")
            for dp in metric_array:
                print(f"  {dp['timestamp']}: {dp['data']}")

    if cpc.dpm_enabled:
        parts = cpc.partitions.list()
        part_str = "Partition"
    else:
        parts = cpc.lpars.list()
        part_str = "LPAR"
    part = parts[0]
    print('')
    print(f'Getting sustainability metrics on {part_str}: {part.name}')
    print(f'Range: {range}')
    print(f'Resolution: {resolution}')
    try:
        data = part.get_sustainability_data(
            range=range, resolution=resolution)
    except zhmcclient.Error as exc:
        print(f"Error: {exc}")
        rc = 1
    else:
        print('')
        print(f'{part_str} sustainability metrics:')
        for metric_name, metric_array in data.items():
            print(f"{metric_name}:")
            for dp in metric_array:
                print(f"  {dp['timestamp']}: {dp['data']}")

    if rc != 0:
        print("Error happened - see above")
        sys.exit(rc)

finally:
    print("Logging off ...")
    session.logoff()
