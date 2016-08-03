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

"""
Example 3: Get partial and full properties for CPCs and for the LPARs of a CPC.
"""

import sys
import logging
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

example3 = examples.get("example3", None)
if example3 is None:
    print("example3 not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = example3.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = example3["hmc"]
cpcname = example3["cpcname"]

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
timestats = example3.get("timestats", None)
if timestats:
    session.time_stats_keeper.enable()

for full_properties in (False, True):
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

print("Finding CPC by name=%s ..." % cpcname)
try:
    cpc = cl.cpcs.find(name=cpcname)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (cpcname, hmc))
    sys.exit(1)

for full_properties in (False, True):
    localtime = time.asctime(time.localtime(time.time()))
    print("Local current time :", localtime)
    print("Listing LPARs on CPC %s (full_properties=%r) ..." % (cpcname, full_properties))
    lpars = cpc.lpars.list(full_properties)
    localtime = time.asctime(time.localtime(time.time()))
    print("Local current time :", localtime)
    for lpar in lpars:
        print("Number of properties of lpar %s: %d (full_properties_flag=%r timestamp=%d)" \
        % (lpar.properties['name'], len(lpar.properties), lpar.full_properties, \
        lpar.properties_timestamp))
#        print(lpar.properties['name'], lpar.properties['status'], \
#              lpar.properties['object-uri'])

print("Logging off ...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
