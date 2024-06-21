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
import getpass
import requests.packages.urllib3

import zhmcclient

requests.packages.urllib3.disable_warnings()

# HMC and user (password is prompted)
host = '10.11.12.13'
userid = 'myuser'
verify_cert = False

# CPC and partition to be updated
cpc_name = 'MYCPC'
partition_name = 'my_partition'

# Crypto adapters to be assigned to the partition
crypto_adapter_names = ['CRYP00']

# Crypto domains to be assigned to the partition and ther access mode
crypto_domains = range(2, 39)
access_mode = 'control'


def get_password(host, userid):
    prompt = f"Enter password for userid {userid} on HMC at {host}: "
    return getpass.getpass(prompt)


print(__doc__)

print(f"Using HMC at {host} with userid {userid} ...")

print("Creating a session with the HMC ...")
try:
    session = zhmcclient.Session(
        host, userid, get_password=get_password, verify_cert=verify_cert)
except zhmcclient.Error as exc:
    print(f"Error: Cannot establish session with HMC {host}: "
          f"{exc.__class__.__name__}: {exc}")
    sys.exit(1)

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

        partition.increase_crypto_config(crypto_adapters, crypto_domain_config)

    except zhmcclient.Error as exc:
        print(f"Error: {exc}")
        sys.exit(1)

finally:
    print("Logging off ...")
    session.logoff()
