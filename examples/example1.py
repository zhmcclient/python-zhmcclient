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

HMC = "9.152.150.86"         # HMC to use
CPCNAME = "P0000P28"         # CPC to list on that HMC

requests.packages.urllib3.disable_warnings()

if len(sys.argv) != 2:
    print("Usage: %s hmccreds.yaml" % sys.argv[0])
    sys.exit(2)
hmccreds_file = sys.argv[1]

with open(hmccreds_file, 'r') as fp:
    hmccreds = yaml.load(fp)

cred = hmccreds.get(HMC, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" % \
          (HMC, hmccreds_file))
    sys.exit(1)
    
userid = cred['userid']
password = cred['password']

print("Using HMC %s with userid %s ..." % (HMC, userid))
session = zhmcclient.Session(HMC, userid, password)
cl = zhmcclient.Client(session)

print("Listing CPCs ...")
cpcs = cl.cpcs.list()
for cpc in cpcs:
#    print(cpc.name, cpc.status, getattr(cpc, "object-uri"))
    print(cpc.properties['name'], cpc.properties['status'],
          cpc.properties['object-uri'])

print("Finding CPC by name=%s ..." % CPCNAME)
try:
    cpc = cl.cpcs.find(name=CPCNAME)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (CPCNAME, HMC))
    sys.exit(1)

print("Listing LPARs on CPC %s ..." % CPCNAME)
lpars = cpc.lpars.list()
for lpar in lpars:
    print(lpar.properties['name'], lpar.properties['status'],
          lpar.properties['object-uri'])
