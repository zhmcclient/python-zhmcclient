#!/usr/bin/env python
# Copyright 2017-2022 IBM Corp. All Rights Reserved.
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
import requests.packages.urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions

requests.packages.urllib3.disable_warnings()

# Get HMC info from HMC inventory and vault files
hmc_def = hmc_definitions()[0]
nickname = hmc_def.nickname
host = hmc_def.host
userid = hmc_def.userid
password = hmc_def.password
verify_cert = hmc_def.verify_cert

print(__doc__)

print("Using HMC {} at {} with userid {} ...".format(nickname, host, userid))

print("Creating a session with the HMC ...")
try:
    session = zhmcclient.Session(
        host, userid, password, verify_cert=verify_cert)
except zhmcclient.Error as exc:
    print("Error: Cannot establish session with HMC {}: {}: {}".
          format(host, exc.__class__.__name__, exc))
    sys.exit(1)

try:
    client = zhmcclient.Client(session)

    print("Finding a CPC in DPM mode ...")
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
    if not cpcs:
        print("Error: HMC at {} does not manage any CPCs in DPM mode".
              format(host))
        sys.exit(1)
    cpc = cpcs[0]
    print("Using CPC {}".format(cpc.name))

    print("Finding all crypto adapters of CPC {} ...".format(cpc.name))
    crypto_adapters = cpc.adapters.findall(type='crypto')
    crypto_adapter_names = [ca.name for ca in crypto_adapters]
    print("Found crypto adapters:")
    for ca in crypto_adapters:
        print("  {} (type: {})".format(ca.name, ca.get_property('crypto-type')))

    print("Determining crypto domains that are free on all crypto adapters of "
          "CPC {} ...".format(cpc.name))
    free_domains = cpc.get_free_crypto_domains(crypto_adapters)
    # print("Free domains (as list): {}".format(free_domains))

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
                ranges.append("{}".format(last_d))
            else:
                ranges.append("{}-{}".format(range_start, last_d))
            range_start = d
        last_d = d
        continue
    if range_start != -1:  # Process the last range, if any
        if range_start == last_d:
            ranges.append("{}".format(last_d))
        else:
            ranges.append("{}-{}".format(range_start, last_d))
    free_domains_str = ', '.join(ranges)
    print("Free domains (as ranges): {}".format(free_domains_str))

finally:
    print("Logging off ...")
    session.logoff()
