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
Example that lists partitions with name filtering.
"""

import sys
import urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions, setup_hmc_session


def main():
    "Main function of the script"

    urllib3.disable_warnings()

    print(__doc__)

    if len(sys.argv) not in (2, 3):
        print(f"Usage: {sys.argv[0]} CPC [PARTITION]")
        print("Where:")
        print("  CPC        Name of the CPC")
        print("  PARTITION  Optional: Filter string for matching the "
              "partition name")
        return 2

    cpc_name = sys.argv[1]
    try:
        partition_name_filter = sys.argv[2]
    except IndexError:
        partition_name_filter = None

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

        cpc = client.cpcs.find(name=cpc_name)
        print(f"Using CPC {cpc.name}")

        if partition_name_filter:
            filter_args = {'name': partition_name_filter}
        else:
            filter_args = None

        print(f"\nListing partitions with filter_args={filter_args!r} ...")
        partitions = cpc.partitions.list(filter_args=filter_args)
        print("Resulting partitions (sorted):")
        for part in sorted(partitions, key=lambda p: p.name):
            print(f"  name={part.name}")

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
