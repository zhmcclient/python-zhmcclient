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

try:
    print("Using HMC %s with userid %s ..." % (hmc, userid))
    session = zhmcclient.Session(hmc, userid, password)
    cl = zhmcclient.Client(session)

    cpc = cl.cpcs.find(name=cpcname, status=cpcstatus)
    print("Status of CPC %s: %s" % \
          (cpc.properties['name'], cpc.properties['status']))

    lpar = cpc.lpars.find(name=lparname)
    print("Status of LPAR %s: %s" % \
          (lpar.properties['name'], lpar.properties['status']))

    print("De-Activating LPAR %s ..." % lpar.properties['name'])
    status = lpar.deactivate()

    lpar = cpc.lpars.find(name=lparname)
    print("Status of LPAR %s: %s" % \
          (lpar.properties['name'], lpar.properties['status']))

    print("Activating LPAR %s ..." % lpar.properties['name'])
    status = lpar.activate()

    lpar = cpc.lpars.find(name=lparname)
    print("Status of LPAR %s: %s" % \
          (lpar.properties['name'], lpar.properties['status']))

    print("Loading LPAR %s from device %s ..." % \
          (lpar.properties['name'], loaddev))
    status = lpar.load(loaddev)

    lpar = cpc.lpars.find(name=lparname)
    print("Status of LPAR %s: %s" % \
          (lpar.properties['name'], lpar.properties['status']))

    if deactivate == "yes":
        print("De-Activating LPAR %s ..." % lpar.properties['name'])
        status = lpar.deactivate()
        
        lpar = cpc.lpars.find(name=lparname)
        print("Status of LPAR %s: %s" % \
              (lpar.properties['name'], lpar.properties['status']))

except zhmcclient.Error as exc:
    print("%s: %s" % (exc.__class__.__name__, exc))
    sys.exit(1)
