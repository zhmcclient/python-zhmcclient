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
Example shows how to use the asynchronous interface in polling mode.
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

async_operation_polling = examples.get("async_operation_polling", None)
if async_operation_polling is None:
    print("async_operation_polling not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = async_operation_polling.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = async_operation_polling["hmc"]
cpcname = async_operation_polling["cpcname"]
cpcstatus = async_operation_polling["cpcstatus"]
lparname = async_operation_polling["lparname"]

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

timestats = async_operation_polling.get("timestats", None)
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
job = lpar.deactivate(wait_for_completion=False)
while True:
    print("Retrieving job status ...")
    job_status, _ = job.check_for_completion()
    print("Job status: %s" % job_status)
    if job_status == 'complete':
        break
    time.sleep(1)
print('De-Activation complete!')

print("Logging off ...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
