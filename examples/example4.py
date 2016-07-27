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
# Example for LPAR activation, deactivation and boot.
#

import sys
import yaml
import requests.packages.urllib3
import time
import zhmcclient

HMC = "9.152.150.65"         # HMC to use
CPCNAME = "P0000P30"         # CPC to use on that HMC
LPARNAME = "PART8"           # LPAR to be used on that CPC
LOAD_DEVNO = "5172"          # device to boot that LPAR from

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

try:
    print("Using HMC %s with userid %s ..." % (HMC, userid))
    session = zhmcclient.Session(HMC, userid, password)
    cl = zhmcclient.Client(session)

    cpc = cl.cpcs.find(name=CPCNAME, status="service-required")
    print("Status of CPC %s: %s" % \
          (cpc.properties['name'], cpc.properties['status']))

    lpar = cpc.lpars.find(name=LPARNAME)
    print("Status of LPAR %s: %s" % \
          (lpar.properties['name'], lpar.properties['status']))

    print("De-Activating LPAR %s ..." % lpar.properties['name'])
    status = lpar.deactivate(wait_for_completion=False)

    print status['job-uri']
    job = session.query_job_status(status['job-uri'])

    while job['status'] != 'complete':
        print job['status']
        time.sleep(1)
        job = session.query_job_status(status['job-uri'])

    print('Deactivate complete !')

except zhmcclient.Error as exc:
    print("%s: %s" % (exc.__class__.__name__, exc))
    sys.exit(1)
