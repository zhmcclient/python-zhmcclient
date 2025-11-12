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
Example that performs an Increase Crypto Configuration operation on a partition
on a CPC in DPM mode.
"""

import sys
import urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions, setup_hmc_session


def main():
    "Main function of the script"

    urllib3.disable_warnings()

    print(__doc__)

    if len(sys.argv) != 6:
        print(f"Usage: {sys.argv[0]} CPC PARTITION ADAPTER DOMAIN_FROM "
              "DOMAIN_TO")
        print("Where:")
        print("  CPC         Name of the CPC")
        print("  PARTITION   Name of the partition")
        print("  ADAPTER     Name of the crypto adapter to attach")
        print("  DOMAIN_FROM Low end of control domain range to attach")
        print("  DOMAIN_TO   High end of control domain range to attach")
        return 2

    cpc_name = sys.argv[1]
    partition_name = sys.argv[2]
    crypto_adapter_names = [sys.argv[3]]
    crypto_domains = range(int(sys.argv[4]), int(sys.argv[5]))
    access_mode = 'control'

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
            print(f"Finding CPC {cpc_name} ...")
            cpc = client.cpcs.find(name=cpc_name)

            print(f"Finding partition {partition_name} ...")
            partition = cpc.partitions.find(name=partition_name)

            crypto_adapters = []
            for aname in crypto_adapter_names:
                print(f"Finding crypto adapter {aname} ...")
                adapter = cpc.adapters.find(name=aname)
                crypto_adapters.append(adapter)

            crypto_domain_config = []
            for domain in crypto_domains:
                domain_config = {
                    "domain-index": domain,
                    "access-mode": access_mode,
                }
                crypto_domain_config.append(domain_config)

            partition.increase_crypto_config(
                crypto_adapters, crypto_domain_config)

        except zhmcclient.Error as exc:
            print(f"Error: {exc}")
            return 1

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
