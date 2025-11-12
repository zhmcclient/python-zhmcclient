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
Example that performs a "Get Partition Properties" operation using the
'properties' query parameter.
"""

import sys
import random
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

        partitions = cpc.partitions.list()
        partition = random.choice(partitions)
        print(f"Using partition {partition.name} ...")

        print("\nLocal partition properties after list: "
              f"{list(partition.properties.keys())}")

        print("\nExecuting pull_properties() with valid property "
              "'maximum-memory' ...")
        partition.pull_properties('maximum-memory')

        print("Local partition properties after this pull: "
              f"{list(partition.properties.keys())}")

        print("\nExecuting pull_properties() with invalid property "
              "'foo' ...")
        partition.pull_properties('foo')

        print("Local partition properties after this pull: "
              f"{list(partition.properties.keys())}")

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
