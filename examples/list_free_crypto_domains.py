#!/usr/bin/env python
# Copyright 2017,2022 IBM Corp. All Rights Reserved.
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
Example that determines the crypto domains that are free on all crypto adapters
of a CPC in DPM mode.
"""

import sys
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

        print(f"Finding all crypto adapters of CPC {cpc.name} ...")
        crypto_adapters = cpc.adapters.findall(type='crypto')
        print("Found crypto adapters:")
        for ca in crypto_adapters:
            print(f"  {ca.name} (type: {ca.get_property('crypto-type')})")

        print("Determining crypto domains that are free on all crypto "
              f"adapters of CPC {cpc.name} ...")
        free_domains = cpc.get_free_crypto_domains(crypto_adapters)
        # print(f"Free domains (as list): {free_domains}")

        # Convert this list of numbers into better readable number ranges:
        ranges = []
        range_start = -1
        last_d = -1
        for d in sorted(free_domains):
            if range_start == -1:
                range_start = d
            elif d == last_d + 1:
                pass
            else:
                if range_start == last_d:
                    ranges.append(f"{last_d}")
                else:
                    ranges.append(f"{range_start}-{last_d}")
                range_start = d
            last_d = d
            continue
        if range_start != -1:  # Process the last range, if any
            if range_start == last_d:
                ranges.append(f"{last_d}")
            else:
                ranges.append(f"{range_start}-{last_d}")
        free_domains_str = ', '.join(ranges)
        print(f"Free domains (as ranges): {free_domains_str}")

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
