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
# Example for partial properties (object-info) and
# full properties for CPCs and LPARs on a CPC.
#

import sys
import yaml
import requests.packages.urllib3
import time

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

for full_properties in [False, True]:
    localtime = time.asctime(time.localtime(time.time()))
    print("Local current time :", localtime)
    print("Listing CPCs (full_properties=%r) ..." % full_properties)
    cpcs = cl.cpcs.list(full_properties)
    localtime = time.asctime(time.localtime(time.time()))
    print("Local current time :", localtime)
    for cpc in cpcs:
        print("Number of properties of cpc %s: %d (full_properties_flag=%r timestamp=%d)" \
        % (cpc.properties['name'], len(cpc.properties), cpc.full_properties, \
        cpc.properties_timestamp))
        print(cpc.properties['name'], cpc.properties['status'],
        cpc.properties['object-uri'])

print("Finding CPC by name=%s ..." % CPCNAME)
try:
    cpc = cl.cpcs.find(name=CPCNAME)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (CPCNAME, HMC))
    sys.exit(1)

for full_properties in [False, True]:
    localtime = time.asctime(time.localtime(time.time()))
    print("Local current time :", localtime)
    print("Listing LPARs on CPC %s (full_properties=%r) ..." % (CPCNAME, full_properties))
    lpars = cpc.lpars.list(full_properties)
    localtime = time.asctime(time.localtime(time.time()))
    print("Local current time :", localtime)
    for lpar in lpars:
        print("Number of properties of lpar %s: %d (full_properties_flag=%r timestamp=%d)" \
        % (lpar.properties['name'], len(lpar.properties), lpar.full_properties, \
        lpar.properties_timestamp))
#        print(lpar.properties['name'], lpar.properties['status'], \
#              lpar.properties['object-uri'])
