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
Example 2: Find an LPAR in a CPC, and activate/deactivate/load the LPAR.
"""

import sys
import logging
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

example2 = examples.get("example2", None)
if example2 is None:
    print("example2 not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = example2.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = example2["hmc"]
cpcname = example2["cpcname"]
cpcstatus = example2["cpcstatus"]
lparname = example2["lparname"]
loaddev = example2["loaddev"]
deactivate = example2["deactivate"]

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

timestats = example2.get("timestats", None)
if timestats:
    session.time_stats_keeper.enable()

print("Finding CPC by name=%s and status=%s ..." % (cpcname, cpcstatus))
try:
    cpc = cl.cpcs.find(name=cpcname, status=cpcstatus)
except zhmcclient.NotFound:
    print("Could not find CPC %s with status %s on HMC %s" %
          (cpcname, cpcstatus, hmc))
    sys.exit(1)
print("Found CPC %s at: %s" % (cpc.name, cpc.uri))

print("Accessing status of CPC %s ..." % cpc.name)
status = cpc.get_property('status')
print("Status of CPC %s: %s" % (cpc.name, status))

print("Finding LPAR by name=%s ..." % lparname)
try:
    lpar = cpc.lpars.find(name=lparname)
except zhmcclient.NotFound:
    print("Could not find LPAR %s in CPC %s" % (lparname, cpc.name))
    sys.exit(1)
print("Found LPAR %s at: %s" % (lpar.name, lpar.uri))

print("Accessing status of LPAR %s ..." % lpar.name)
status = lpar.get_property('status')
print("Status of LPAR %s: %s" % (lpar.name, status))

print("Deactivating LPAR %s ..." % lpar.name)
lpar.deactivate()
print("Refreshing properties of LPAR %s ..." % lpar.name)
lpar.pull_full_properties()
print("Accessing status of LPAR %s ..." % lpar.name)
status = lpar.get_property('status')
print("Status of LPAR %s: %s" % (lpar.name, status))

print("Activating LPAR %s ..." % lpar.name)
lpar.activate()
print("Refreshing properties of LPAR %s ..." % lpar.name)
lpar.pull_full_properties()
print("Accessing status of LPAR %s ..." % lpar.name)
status = lpar.get_property('status')
print("Status of LPAR %s: %s" % (lpar.name, status))

print("Loading LPAR %s from device %s ..." % (lpar.name, loaddev))
lpar.load(loaddev)
for i in range(0, 5):
    print("Refreshing properties of LPAR %s ..." % lpar.name)
    lpar.pull_full_properties()
    print("Accessing status of LPAR %s ..." % lpar.name)
    status = lpar.get_property('status')
    print("Status of LPAR %s: %s" % (lpar.name, status))
    if status == 'operating':
        break

if deactivate == "yes":
    print("Deactivating LPAR %s ..." % lpar.name)
    lpar.deactivate()
    print("Refreshing properties of LPAR %s ..." % lpar.name)
    lpar.pull_full_properties()
    print("Accessing status of LPAR %s ..." % lpar.name)
    status = lpar.get_property('status')
    print("Status of LPAR %s: %s" % (lpar.name, status))

print("Logging off ...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
