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
Example shows how to get partial and full properties for CPCs
and for LPARs of a CPC.
"""

import sys
import logging
import yaml
import requests.packages.urllib3
from datetime import datetime

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

get_partial_and_full_properties = examples.get("get_partial_and_full_properties", None)
if get_partial_and_full_properties is None:
    print("get_partial_and_full_properties not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = get_partial_and_full_properties.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = get_partial_and_full_properties["hmc"]
cpcname = get_partial_and_full_properties["cpcname"]

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
timestats = get_partial_and_full_properties.get("timestats", None)
if timestats:
    session.time_stats_keeper.enable()

for full_properties in (False, True):
    print("Listing CPCs with full_properties=%s ..." % full_properties)
    start_dt = datetime.now()
    cpcs = cl.cpcs.list(full_properties)
    end_dt = datetime.now()
    duration = end_dt - start_dt
    print("Duration: %s" % duration)
    for cpc in cpcs:
        print("Number of properties of CPC %s: %s" %
              (cpc.name, len(cpc.properties)))

print("Finding CPC by name=%s ..." % cpcname)
try:
    cpc = cl.cpcs.find(name=cpcname)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (cpcname, hmc))
    sys.exit(1)
print("Found CPC %s at: %s" % (cpc.name, cpc.uri))

for full_properties in (False, True):
    print("Listing LPARs on CPC %s with full_properties=%s ..." %
          (cpc.name, full_properties))
    start_dt = datetime.now()
    lpars = cpc.lpars.list(full_properties)
    end_dt = datetime.now()
    duration = end_dt - start_dt
    print("Duration: %s" % duration)
    for lpar in lpars:
        print("Number of properties of LPAR %s: %s" %
              (lpar.name, len(lpar.properties)))

print("Logging off ...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
