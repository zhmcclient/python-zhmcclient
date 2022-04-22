#!/usr/bin/env python
# Copyright 2016-2022 IBM Corp. All Rights Reserved.
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
Example that finds CPCs in different ways.
"""

import sys
import requests.packages.urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions

requests.packages.urllib3.disable_warnings()

# Get HMC info from HMC definition file
hmc_def = hmc_definitions()[0]
nick = hmc_def.nickname
host = hmc_def.hmc_host
userid = hmc_def.hmc_userid
password = hmc_def.hmc_password
verify_cert = hmc_def.hmc_verify_cert

print(__doc__)

print("Using HMC {} at {} with userid {} ...".format(nick, host, userid))

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

    print("Finding CPCs in classic mode by filtering on properties ...")
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': False})
    if not cpcs:
        print("Error: HMC at {} does not manage any CPCs in classic mode".
              format(host))
        sys.exit(1)
    cpc_names = [cpc.name for cpc in cpcs]
    print("Found CPCs: {}".format(', '.join(cpc_names)))

    cpc_name = cpc_names[0]
    print("Finding CPC by name={} ...".format(cpc_name))
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.NotFound:
        print("Error: Could not find CPC {}".format(cpc_name))
        sys.exit(1)
    print("Found CPC: {}".format(cpc.name))

finally:
    print("Logging off ...")
    session.logoff()
