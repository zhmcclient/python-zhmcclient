#!/usr/bin/env python
# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
Example shows how to use the Adapter, Port, Virtual Switch, NIC, HBA
and Virtual Function interface.
"""

import sys
import yaml
import requests.packages.urllib3
import time

import zhmcclient

requests.packages.urllib3.disable_warnings()

if len(sys.argv) != 2:
    print("Usage: %s hmccreds.yaml" % sys.argv[0])
    sys.exit(2)
hmccreds_file = sys.argv[1]

with open(hmccreds_file, 'r') as fp:
    hmccreds = yaml.load(fp)

examples = hmccreds.get("examples", None)
if examples is None:
    print("examples not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

adapter_port_vswitch = examples.get("adapter_port_vswitch", None)
if adapter_port_vswitch is None:
    print("adapter_port_vswitch not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = adapter_port_vswitch.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = adapter_port_vswitch["hmc"]

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" % \
          (hmc, hmccreds_file))
    sys.exit(1)

userid = cred['userid']
password = cred['password']

print(__doc__)

print("Using HMC %s with userid %s ..." % (hmc, userid))
session = zhmcclient.Session(hmc, userid, password)
cl = zhmcclient.Client(session)

timestats = adapter_port_vswitch.get("timestats", None)
if timestats:
    session.time_stats_keeper.enable()

print("Listing CPCs ...")
cpcs = cl.cpcs.list()
for cpc in cpcs:
    print(cpc)
    print("\tListing Adapters for %s ..." % cpc.name)
    adapters = cpc.adapters.list()
    for i, adapter in enumerate(adapters):
        print('\t' + str(adapter))
        ports = adapter.ports.list(full_properties=False)
        for p, port in enumerate(ports):
            if p == 0:
                print("\t\tListing Ports for %s ..." % adapter.name)
#                port.pull_full_properties()
            print('\t\t' + str(port))
    print("\tListing Virtual Switches for %s ..." % cpc.name)
    vswitches = cpc.vswitches.list()
    for i, vswitch in enumerate(vswitches):
        print('\t' + str(vswitch))
    print("\tListing Partitions for %s ..." % cpc.name)
    partitions = cpc.partitions.list()
    for i, partition in enumerate(partitions):
        print('\t' + str(partition))
        nics = partition.nics.list(full_properties=False)
        for j, nic in enumerate(nics):
            if j == 0:
                print("\t\tListing NICs for %s ..." % partition.name)
            print('\t\t' + str(nic))

        hbas = partition.hbas.list(full_properties=False)
        for j, hba in enumerate(hbas):
            if j == 0:
                print("\t\tListing HBAs for %s ..." % partition.name)
            print('\t\t' + str(hba))
#                hba.pull_full_properties()
#                print('\t\t' + str(hba.properties))
        vfs = partition.virtual_functions.list(full_properties=False)
        for k, vf in enumerate(vfs):
            if k == 0:
                print("\t\tListing Virtual Functions for %s ..." % partition.name)
            print('\t\t' + str(vf))
#                vf.pull_full_properties()
#                print('\t\t' + str(vf.properties))

print("Logging off ...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
