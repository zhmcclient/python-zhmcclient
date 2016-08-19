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

try:
    print("Using HMC %s with userid %s ..." % (hmc, userid))
    session = zhmcclient.Session(hmc, userid, password)
    cl = zhmcclient.Client(session)

    timestats = example4.get("timestats", None)
    if timestats:
        session.time_stats_keeper.enable()

    cpc = cl.cpcs.find(name=cpcname, status=cpcstatus)
    print("Status of CPC %s: %s" % \
          (cpc.properties['name'], cpc.properties['status']))

    lpar = cpc.lpars.find(name=lparname)
    print("Status of LPAR %s: %s" % \
          (lpar.properties['name'], lpar.properties['status']))

    print("De-Activating LPAR %s ..." % lpar.properties['name'])
    status = lpar.deactivate(wait_for_completion=False)

    print("job-uri: %s" % (status['job-uri']))
    job = session.query_job_status(status['job-uri'])
    print("job response: %s" % job)

    while job['status'] != 'complete':
        print("Job Status: %s" % (job['status']))
        time.sleep(1)
        job = session.query_job_status(status['job-uri'])

    print("job response: %s" % job)
    print('De-Activate complete !')

    print('Deleting completed job status ...')
    session.delete_completed_job_status(status['job-uri'])

#    print('Deleting completed job status again ...')
#    session.delete_completed_job_status(status['job-uri'])
#    Returns exception:
#    HTTPError: 404,1: No job or status for 'b571dbde-c9cb-11e1-8327-00215e676926_45fdd752-65f4-11e6-a6c3-00215e676926

    print("Logging off ...")
    session.logoff()

    if timestats:
        print(session.time_stats_keeper)

    print("Done.")

except zhmcclient.Error as exc:
    print("%s: %s" % (exc.__class__.__name__, exc))
    sys.exit(1)
