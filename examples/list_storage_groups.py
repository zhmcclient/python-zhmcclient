#!/usr/bin/env python
# Copyright 2018-2022 IBM Corp. All Rights Reserved.
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
Example that lists storage groups on a CPC in DPM mode.
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

    print("Finding a CPC in DPM mode ...")
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
    if not cpcs:
        print("Error: HMC at {} does not manage any CPCs in DPM mode".
              format(host))
        sys.exit(1)
    cpc = cpcs[0]
    print("Using CPC {}".format(cpc.name))

    print("Listing storage groups of CPC {} ...".format(cpc.name))
    try:
        storage_groups = cpc.list_associated_storage_groups()
    except zhmcclient.Error as exc:
        print("Error: Cannot list storage groups of CPC {}: {}: {}".
              format(cpc.name, exc.__class__.__name__, exc))
        sys.exit(1)

    for sg in storage_groups:

        print("Storage group: {} (type: {}, shared: {}, fulfillment: {})".
              format(sg.name, sg.get_property('type'),
                     sg.get_property('shared'),
                     sg.get_property('fulfillment-state')))

        try:
            volumes = sg.storage_volumes.list()
        except zhmcclient.HTTPError as exc:
            print("Error: Cannot list storage volumes of storage group {}: "
                  "{}: {}".format(sg.name, exc.__class__.__name__, exc))
            sys.exit(1)

        print("    Storage Volumes: {}".format(len(volumes)))
        for sv in volumes:
            print("    Storage Volume: {}".format(sv.name))

        if sg.get_property('type') == 'fcp':

            try:
                vsrs = sg.virtual_storage_resources.list()
            except zhmcclient.HTTPError as exc:
                print("Error: Cannot list virtual storage resources of "
                      "storage group {}: {}: {}".
                      format(sg.name, exc.__class__.__name__, exc))
                sys.exit(1)

            for vsr in vsrs:
                port = vsr.adapter_port
                adapter = port.manager.parent
                print("    Virtual Storage Resource: {} (devno: {}, "
                      "adapter.port: {}.{}, attached to partition: {})".
                      format(vsr.name, vsr.get_property('device-number'),
                             adapter.name, port.name,
                             vsr.attached_partition.name))
            else:
                print("    No Virtual Storage Resources")

finally:
    print("Logging off ...")
    session.logoff()
