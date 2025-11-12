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
Example that performs a create-read-update-delete lifecycle of a partition
on a CPC in DPM mode.
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

        print("Finding a CPC in DPM mode ...")
        cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
        if not cpcs:
            print(f"Error: HMC at {host} does not manage any CPCs in DPM mode")
            return 1
        cpc = cpcs[0]
        print(f"Using CPC {cpc.name}")

        part_name = f"zhmc_test_{uuid.uuid4()}"
        print(f"Creating partition {part_name} ...")
        part_props = {
            'name': part_name,
            'description': 'Original partition description.',
            'cp-processors': 2,
            'initial-memory': 1024,
            'maximum-memory': 2048,
            'processor-mode': 'shared',
            'boot-device': 'test-operating-system'
        }
        try:
            part = cpc.partitions.create(properties=part_props)
        except zhmcclient.Error as exc:
            print(f"Error: Cannot create partition {part_name} on CPC "
                  f"{cpc.name}: {exc.__class__.__name__}: {exc}")
            return 1

        print(f"Starting partition {part.name} ...")
        part.start()

        print("Current partition description: "
              f"{part.get_property('description')}")
        new_description = "Updated partition description."
        updated_properties = {}
        updated_properties["description"] = new_description

        print(f"Updating partition description to: {new_description}")
        part.update_properties(updated_properties)

        print("Partition description on local resource object: "
              f"{part.get_property('description')}")

        print("Refreshing properties of local resource object ...")
        part.pull_full_properties()
        print("Partition description on local resource object: "
              f"{part.get_property('description')}")

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
