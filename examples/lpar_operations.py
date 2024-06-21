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
Example that finds an LPAR on a CPC in classic mode and performs
activate/load/deactivate on the LPAR.
"""

import sys
import time
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

# Customize: Set to the LPAR that you want to activate/load/deactivate
lpar_name = 'ZHMCTEST'

# Customize: Set to the device number from which the LPAR should load
lpar_load_devno = '0100'

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

    print("Finding a CPC in classic mode ...")
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': False})
    if not cpcs:
        print(f"Error: HMC at {host} does not manage any CPCs in classic mode")
        sys.exit(1)
    cpc = cpcs[0]
    print(f"Using CPC {cpc.name}")

    print(f"Finding LPAR by name={lpar_name} ...")
    # We use list() instead of find() because find(name=..) is optimized by
    # using the name-to-uri cache and therefore returns an Lpar object with
    # only a minimal set of properties, and particularly no 'status' property.
    # That would drive an extra "Get Logical Partition Properties" operation
    # when the status property is accessed.
    lpars = cpc.lpars.list(filter_args={'name': lpar_name})
    if len(lpars) != 1:
        print(f"Error: Could not find LPAR {lpar_name} on CPC {cpc.name} - "
              "customize the LPAR name in the example script")
        lpar_names = [lpar.name for lpar in cpc.lpars.list()]
        lpar_str = ', '.join(lpar_names)
        print(f"Note: The following LPARs exist on CPC {cpc.name}: {lpar_str}")
        sys.exit(1)
    lpar = lpars[0]
    status = lpar.get_property('status')
    print(f"Found LPAR {lpar.name} with status {status}")

    retries = 10

    if status != "not-activated":
        print(f"Deactivating LPAR {lpar.name} ...")
        lpar.deactivate()
        for i in range(0, retries):
            lpar = cpc.lpars.list(filter_args={'name': lpar_name})[0]
            status = lpar.get_property('status')
            print(f"LPAR status: {status}")
            if status == 'not-activated':
                break
            time.sleep(1)
        else:
            print(f"Warning: After {retries} retries, status of LPAR "
                  f"{lpar.name} after Deactivate is still: {status}")

    print(f"Activating LPAR {lpar.name} ...")
    lpar.activate()
    for i in range(0, retries):
        lpar = cpc.lpars.list(filter_args={'name': lpar_name})[0]
        status = lpar.get_property('status')
        print(f"LPAR status: {status}")
        if status == 'not-operating':
            break
        time.sleep(1)
    else:
        print(f"Warning: After {retries} retries, status of LPAR {lpar.name} "
              f"after Activate is still: {status}")

    print(f"Loading LPAR {lpar.name} from device {lpar_load_devno} ...")
    lpar.load(lpar_load_devno)
    for i in range(0, retries):
        lpar = cpc.lpars.list(filter_args={'name': lpar_name})[0]
        status = lpar.get_property('status')
        print(f"LPAR status: {status}")
        if status == 'operating':
            break
        time.sleep(1)
    else:
        print(f"Warning: After {retries} retries, status of LPAR {lpar.name} "
              f"after Load is still: {status}")

    print(f"Deactivating LPAR {lpar.name} ...")
    lpar.deactivate()
    for i in range(0, retries):
        lpar = cpc.lpars.list(filter_args={'name': lpar_name})[0]
        status = lpar.get_property('status')
        print(f"LPAR status: {status}")
        if status == 'not-activated':
            break
        time.sleep(1)
    else:
        print(f"Warning: After {retries} retries, status of LPAR {lpar.name} "
              f"after Deactivate is still: {status}")

finally:
    print("Logging off ...")
    session.logoff()
