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
Example that creates and deletes a Hipersocket adapter in a CPC in DPM mode.
"""

import sys
import uuid
import urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions, setup_hmc_session


def main():
    "Main function of the script"

    urllib3.disable_warnings()

    print(__doc__)

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

        print("Determining the CPC to use ...")
        cpc_name = None
        for name, props in hmc_def.cpcs.items():
            if props.get("dpm_enabled", False) is True:
                cpc_name = name
                break
        if cpc_name:
            print(f"Finding CPC {cpc_name} specified in HMC inventory ...")
            try:
                cpc = client.cpcs.find_by_name(cpc_name)
            except zhmcclient.Error as exc:
                print(f"Error: Cannot find CPC {cpc_name}: "
                      f"{exc.__class__.__name__}: {exc}")
                return 1
        else:
            print("Finding any CPC in DPM mode ...")
            cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
            if not cpcs:
                print(f"Error: HMC at {host} does not manage any CPCs in DPM "
                      "mode")
                return 1
            cpc = cpcs[0]
        print(f"Using CPC {cpc.name}")

        ad_name = f"zhmc_test_{uuid.uuid4()}"
        print(f"Creating Hipersocket adapter {ad_name} ...")
        ad_props = {
            'name': ad_name,
            'description': 'Original adapter description.',
        }
        try:
            ad = cpc.adapters.create_hipersocket(properties=ad_props)
        except zhmcclient.Error as exc:
            print(f"Error: Cannot create Hipersocket adapter {ad_name} on CPC "
                  f"{cpc.name}: {exc.__class__.__name__}: {exc}")
            return 1

        print(f"Deleting Hipersocket adapter {ad_name} ...")
        try:
            ad.delete()
        except zhmcclient.Error as exc:
            print(f"Error: Cannot delete Hipersocket adapter {ad_name} on CPC "
                  f"{cpc.name}: {exc.__class__.__name__}: {exc}")
            return 1

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
