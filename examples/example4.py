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
Example 4: Using the asynchronous interface.
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

example4 = examples.get("example4", None)
if example4 is None:
    print("example4 not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = example4.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = example4["hmc"]
cpcname = example4["cpcname"]
cpcstatus = example4["cpcstatus"]
lparname = example4["lparname"]

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

timestats = example4.get("timestats", None)
if timestats:
    session.time_stats_keeper.enable()

print("Finding CPC by name=%s and status=%s ..." % (cpcname, cpcstatus))
try:
    cpc = cl.cpcs.find(name=cpcname, status=cpcstatus)
except zhmcclient.NotFound:
    print("Could not find CPC %s with status %s on HMC %s" %
          (cpcname, cpcstatus, hmc))
    sys.exit(1)

print("Finding LPAR by name=%s ..." % lparname)
try:
    lpar = cpc.lpars.find(name=lparname)
except zhmcclient.NotFound:
    print("Could not find LPAR %s in CPC %s" % (lparname, cpc.name))
    sys.exit(1)

print("Accessing status of LPAR %s ..." % lpar.name)
status = lpar.get_property('status')
print("Status of LPAR %s: %s" % (lpar.name, status))

print("De-Activating LPAR %s (async.) ..." % lpar.name)
job_obj = lpar.deactivate(wait_for_completion=False)
job_uri = job_obj['job-uri']
print("Job URI: %s" % job_uri)

print("Retrieving job properties ...")
job = session.query_job_status(job_uri)
print("Job properties: %s" % job)

while job['status'] != 'complete':
    time.sleep(1)
    print("Retrieving job properties ...")
    job = session.query_job_status(job_uri)
    print("Job properties: %s" % job)

print('De-Activation complete!')

print('Deleting completed job ...')
session.delete_completed_job_status(job_uri)

print("Logging off ...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
