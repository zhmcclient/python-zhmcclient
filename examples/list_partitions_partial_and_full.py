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
Example that lists partitions with partial and full properties to show timing
difference.
"""

import sys
from datetime import datetime
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

        try:
            cpc_name = sys.argv[1]
        except IndexError:
            cpc_name = None
        if cpc_name:
            cpc = client.cpcs.find(name=cpc_name)
            print(f"Using specified CPC {cpc.name}")
        else:
            cpcs = client.cpcs.list()
            cpc = cpcs[0]
            print(f"Using first CPC {cpc.name}")

        for full_properties in (False, True):
            print("\nListing partitions with "
                  f"full_properties={full_properties} ...")
            start_dt = datetime.now()
            partitions = cpc.partitions.list(full_properties)
            end_dt = datetime.now()
            duration = end_dt - start_dt
            non_stopped_partitions = [p for p in partitions
                                      if p.properties['status'] != 'stopped']
            num_props = 0
            for partition in partitions:
                num_props += len(partition.properties)
            print(f"Duration: {duration.total_seconds():.2f} s")
            print(f"Number of partitions: {len(partitions)}")
            print("Number of non-stopped partitions: "
                  f"{len(non_stopped_partitions)}")
            avg_props = num_props / len(partitions)
            print("Average number of properties per partition: "
                  f"{avg_props:.1f}")

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
