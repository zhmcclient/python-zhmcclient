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
import urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions, setup_hmc_session

RANGE = "last-day"
RESOLUTION = "fifteen-minutes"


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
        rc = 0

        cpcs = client.cpcs.list()
        cpc = cpcs[0]
        print('')
        print(f'Getting sustainability metrics on CPC: {cpc.name}')
        print(f'Range: {RANGE}')
        print(f'Resolution: {RESOLUTION}')
        try:
            data = cpc.get_sustainability_data(
                range=RANGE, resolution=RESOLUTION)
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
        print(f'Range: {RANGE}')
        print(f'Resolution: {RESOLUTION}')
        try:
            data = part.get_sustainability_data(
                range=RANGE, resolution=RESOLUTION)
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
            return 1

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
