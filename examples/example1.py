#!/usr/bin/env python
# Copyright 2016 IBM Corp. All Rights Reserved.
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

#
# Example for listing CPCs and LPARs on a CPC.
#

import sys
import yaml
import requests.packages.urllib3

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

example1 = examples.get("example1", None)
if example1 is None:
    print("example1 not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

hmc = example1["hmc"]
cpcname = example1["cpcname"]

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" % \
          (hmc, hmccreds_file))
    sys.exit(1)
    
userid = cred['userid']
password = cred['password']

print("Using HMC %s with userid %s ..." % (hmc, userid))
session = zhmcclient.Session(hmc, userid, password)
cl = zhmcclient.Client(session)

print("Listing CPCs ...")
cpcs = cl.cpcs.list()
for cpc in cpcs:
#    print(cpc.name, cpc.status, getattr(cpc, "object-uri"))
    print(cpc.properties['name'], cpc.properties['status'],
          cpc.properties['object-uri'])

print("Finding CPC by name=%s ..." % cpcname)
try:
    cpc = cl.cpcs.find(name=cpcname)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (cpcname, hmc))
    sys.exit(1)

if cpc.dpm_enabled:
    print("Listing Partitions on CPC %s ..." % cpcname)
    partitions = cpc.partitions.list()
else:
    print("Listing LPARs on CPC %s ..." % cpcname)
    partitions = cpc.lpars.list()
for partition in partitions:
    print(partition.properties['name'], partition.properties['status'],
          partition.properties['object-uri'])
