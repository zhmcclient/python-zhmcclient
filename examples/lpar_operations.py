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

    print("Finding a CPC in classic mode ...")
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': False})
    if not cpcs:
        print("Error: HMC at {} does not manage any CPCs in classic mode".
              format(host))
        sys.exit(1)
    cpc = cpcs[0]
    print("Using CPC {}".format(cpc.name))

    print("Finding LPAR by name={} ...".format(lpar_name))
    # We use list() instead of find() because find(name=..) is optimized by
    # using the name-to-uri cache and therefore returns an Lpar object with
    # only a minimal set of properties, and particularly no 'status' property.
    # That would drive an extra "Get Logical Partition Properties" operation
    # when the status property is accessed.
    lpars = cpc.lpars.list(filter_args={'name': lpar_name})
    if len(lpars) != 1:
        print("Error: Could not find LPAR {} on CPC {} - customize the LPAR "
              "name in the example script".
              format(lpar_name, cpc.name))
        lpar_names = [lpar.name for lpar in cpc.lpars.list()]
        print("Note: The following LPARs exist on CPC {}: {}".
              format(cpc.name, ', '.join(lpar_names)))
        sys.exit(1)
    lpar = lpars[0]
    status = lpar.get_property('status')
    print("Found LPAR {} with status {}".format(lpar.name, status))

    retries = 10

    if status != "not-activated":
        print("Deactivating LPAR {} ...".format(lpar.name))
        lpar.deactivate()
        for i in range(0, retries):
            lpar = cpc.lpars.list(filter_args={'name': lpar_name})[0]
            status = lpar.get_property('status')
            print("LPAR status: {}".format(status))
            if status == 'not-activated':
                break
            time.sleep(1)
        else:
            print("Warning: After {} retries, status of LPAR {} after "
                  "Deactivate is still: {}".format(retries, lpar.name, status))

    print("Activating LPAR {} ...".format(lpar.name))
    lpar.activate()
    for i in range(0, retries):
        lpar = cpc.lpars.list(filter_args={'name': lpar_name})[0]
        status = lpar.get_property('status')
        print("LPAR status: {}".format(status))
        if status == 'not-operating':
            break
        time.sleep(1)
    else:
        print("Warning: After {} retries, status of LPAR {} after "
              "Activate is still: {}".format(retries, lpar.name, status))

    print("Loading LPAR {} from device {} ...".
          format(lpar.name, lpar_load_devno))
    lpar.load(lpar_load_devno)
    for i in range(0, retries):
        lpar = cpc.lpars.list(filter_args={'name': lpar_name})[0]
        status = lpar.get_property('status')
        print("LPAR status: {}".format(status))
        if status == 'operating':
            break
        time.sleep(1)
    else:
        print("Warning: After {} retries, status of LPAR {} after "
              "Load is still: {}".format(retries, lpar.name, status))

    print("Deactivating LPAR {} ...".format(lpar.name))
    lpar.deactivate()
    for i in range(0, retries):
        lpar = cpc.lpars.list(filter_args={'name': lpar_name})[0]
        status = lpar.get_property('status')
        print("LPAR status: {}".format(status))
        if status == 'not-activated':
            break
        time.sleep(1)
    else:
        print("Warning: After {} retries, status of LPAR {} after "
              "Deactivate is still: {}".format(retries, lpar.name, status))

finally:
    print("Logging off ...")
    session.logoff()
