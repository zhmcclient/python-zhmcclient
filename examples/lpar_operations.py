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
import urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions, setup_hmc_session


def main():
    "Main function of the script"

    urllib3.disable_warnings()

    print(__doc__)

    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} CPC LPAR DEVNO")
        print("Where:")
        print("  CPC        Name of the CPC")
        print("  LPAR       Name of the LPAR to activate/load/deactivate")
        print("  DEVNO      Device number from which the LPAR should load")
        return 2

    cpc_name = sys.argv[1]
    lpar_name = sys.argv[2]
    lpar_load_devno = sys.argv[3]

    # Get HMC info from HMC inventory and vault files
    hmc_def = hmc_definitions()[0]
    host = hmc_def.host
    print(f"Creating a session with the HMC at {host} ...")
    try:
        session = setup_hmc_session(hmc_def)
    except zhmcclient.Error as exc:
        print(f"Error: Cannot establish session with HMC {host}: "
              f"{exc.__class__.__name__}: {exc}")
        return 1

    try:
        client = zhmcclient.Client(session)

        print(f"Finding CPC {cpc_name} (classic mode) ...")
        try:
            cpc = client.cpcs.find_by_name(cpc_name)
        except zhmcclient.Error as exc:
            print(f"Error: Cannot find CPC {cpc_name}: "
                  f"{exc.__class__.__name__}: {exc}")
            return 1
        if cpc.get_property("dpm-enabled", False):
            print(f"Error: CPC {cpc_name} is not in classic mode")
            return 1

        print(f"Using CPC {cpc.name}")

        print(f"Finding LPAR by name={lpar_name} ...")
        # We use list() instead of find() because find(name=..) is optimized by
        # using the name-to-uri cache and therefore returns an Lpar object with
        # only a minimal set of properties, and particularly no 'status'
        # property. That would drive an extra "Get Logical Partition Properties"
        # operation when the status property is accessed.
        lpars = cpc.lpars.list(filter_args={'name': lpar_name})
        if len(lpars) != 1:
            print(f"Error: Could not find LPAR {lpar_name} on CPC {cpc.name} - "
                  "customize the LPAR name in the example script")
            lpar_names = [lpar.name for lpar in cpc.lpars.list()]
            lpar_str = ', '.join(lpar_names)
            print(f"Note: The following LPARs exist on CPC {cpc.name}: "
                  f"{lpar_str}")
            return 1
        lpar = lpars[0]
        status = lpar.get_property('status')
        print(f"Found LPAR {lpar.name} with status {status}")

        retries = 10

        if status != "not-activated":
            print(f"Deactivating LPAR {lpar.name} ...")
            lpar.deactivate()
            for _ in range(0, retries):
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
        for _ in range(0, retries):
            lpar = cpc.lpars.list(filter_args={'name': lpar_name})[0]
            status = lpar.get_property('status')
            print(f"LPAR status: {status}")
            if status == 'not-operating':
                break
            time.sleep(1)
        else:
            print(f"Warning: After {retries} retries, status of LPAR "
                  f"{lpar.name} after Activate is still: {status}")

        print(f"Loading LPAR {lpar.name} from device {lpar_load_devno} ...")
        lpar.load(lpar_load_devno)
        for _ in range(0, retries):
            lpar = cpc.lpars.list(filter_args={'name': lpar_name})[0]
            status = lpar.get_property('status')
            print(f"LPAR status: {status}")
            if status == 'operating':
                break
            time.sleep(1)
        else:
            print(f"Warning: After {retries} retries, status of LPAR "
                  f"{lpar.name} after Load is still: {status}")

        print(f"Deactivating LPAR {lpar.name} ...")
        lpar.deactivate()
        for _ in range(0, retries):
            lpar = cpc.lpars.list(filter_args={'name': lpar_name})[0]
            status = lpar.get_property('status')
            print(f"LPAR status: {status}")
            if status == 'not-activated':
                break
            time.sleep(1)
        else:
            print(f"Warning: After {retries} retries, status of LPAR "
                  f"{lpar.name} after Deactivate is still: {status}")

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
