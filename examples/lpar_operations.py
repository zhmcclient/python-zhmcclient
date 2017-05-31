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
Example shows how to find an LPAR in a CPC
and activate/deactivate/load of an LPAR.
"""

import sys
import logging
import yaml
import time
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

lpar_operations = examples.get("lpar_operations", None)
if lpar_operations is None:
    print("lpar_operations not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = lpar_operations.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = lpar_operations["hmc"]
cpcname = lpar_operations["cpcname"]
lparname = lpar_operations["lparname"]
loaddev = lpar_operations["loaddev"]
deactivate = lpar_operations["deactivate"]

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

timestats = lpar_operations.get("timestats", None)
if timestats:
    session.time_stats_keeper.enable()

retries = 10

print("Finding CPC by name=%s ..." % cpcname)
try:
    cpc = cl.cpcs.find(name=cpcname)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (cpcname, hmc))
    sys.exit(1)
print("Found CPC %s at: %s" % (cpc.name, cpc.uri))

print("Finding LPAR by name=%s ..." % lparname)
# We use list() instead of find() because find(name=..) is optimized by using
# the name-to-uri cache and therefore returns an Lpar object with only a
# minimal set of properties, and particularly no 'status' property.
# That would drive an extra "Get Logical Partition Properties" operation when
# the status property is accessed.
lpars = cpc.lpars.list(filter_args={'name': lparname})
if len(lpars) != 1:
    print("Could not find LPAR %s in CPC %s" % (lparname, cpc.name))
    sys.exit(1)
lpar = lpars[0]
print("Found LPAR %s at: %s" % (lpar.name, lpar.uri))

status = lpar.get_property('status')
print("Status of LPAR %s: %s" % (lpar.name, status))

if status != "not-activated":
    print("Deactivating LPAR %s ..." % lpar.name)
    lpar.deactivate()
    for i in range(0, retries):
        print("Refreshing ...")
        lpar = cpc.lpars.list(filter_args={'name': lparname})[0]
        status = lpar.get_property('status')
        print("Status of LPAR %s: %s" % (lpar.name, status))
        if status == 'not-activated':
            break
        time.sleep(1)
    else:
        print("Warning: After %d retries, status of LPAR %s after Deactivate "
              "is still: %s" % (retries, lpar.name, status))

print("Activating LPAR %s ..." % lpar.name)
lpar.activate()
for i in range(0, retries):
    print("Refreshing ...")
    lpar = cpc.lpars.list(filter_args={'name': lparname})[0]
    status = lpar.get_property('status')
    print("Status of LPAR %s: %s" % (lpar.name, status))
    if status == 'not-operating':
        break
    time.sleep(1)
else:
    print("Warning: After %d retries, status of LPAR %s after Activate "
          "is still: %s" % (retries, lpar.name, status))

print("Loading LPAR %s from device %s ..." % (lpar.name, loaddev))
lpar.load(loaddev)
for i in range(0, retries):
    print("Refreshing ...")
    lpar = cpc.lpars.list(filter_args={'name': lparname})[0]
    status = lpar.get_property('status')
    print("Status of LPAR %s: %s" % (lpar.name, status))
    if status == 'operating':
        break
    time.sleep(1)
else:
    print("Warning: After %d retries, status of LPAR %s after Load "
          "is still: %s" % (retries, lpar.name, status))

if deactivate == "yes":
    print("Deactivating LPAR %s ..." % lpar.name)
    lpar.deactivate()
    for i in range(0, retries):
        print("Refreshing ...")
        lpar = cpc.lpars.list(filter_args={'name': lparname})[0]
        status = lpar.get_property('status')
        print("Status of LPAR %s: %s" % (lpar.name, status))
        if status == 'not-activated':
            break
        time.sleep(1)
    else:
        print("Warning: After %d retries, status of LPAR %s after Deactivate "
              "is still: %s" % (retries, lpar.name, status))

print("Logging off ...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
