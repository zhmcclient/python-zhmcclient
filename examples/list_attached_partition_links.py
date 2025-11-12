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
Example that lists partition links attached to a partition.
"""

import sys
import urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions, setup_hmc_session


def main():
    "Main function of the script"

    urllib3.disable_warnings()

    print(__doc__)

    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} CPC PARTITION")
        print("Where:")
        print("  CPC         Name of the CPC")
        print("  PARTITION   Name of the partition")
        return 2

    cpc_name = sys.argv[1]
    part_name = sys.argv[2]

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

        print(f"Finding partition {part_name} on CPC {cpc_name} ...")
        cpc = client.cpcs.find(name=cpc_name)
        part = cpc.partitions.find(name=part_name)

        print(f"Listing partition links attached to partition {part_name} ...")
        partition_links = part.list_attached_partition_links()

        print()
        print("Partition Link        Type          State       "
              "Attached partitions")
        print(87 * "-")
        for pl in partition_links:
            name = pl.get_property('name')
            pl_type = pl.get_property('type')
            state = pl.get_property('state')
            attached_parts = pl.list_attached_partitions()
            attached_part_names = [p.name for p in attached_parts]
            print(f"{name:20s}  {pl_type:12s}  {state:10}  "
                  f"{', '.join(attached_part_names)}")
        print()

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
