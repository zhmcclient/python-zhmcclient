#!/usr/bin/env python
#
# Example for LPAR activation, deactivation and boot.
#

import sys
import yaml
import requests.packages.urllib3

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
    status = lpar.deactivate()

    lpar = cpc.lpars.find(name=LPARNAME)
    print("Status of LPAR %s: %s" % \
          (lpar.properties['name'], lpar.properties['status']))

    print("Activating LPAR %s ..." % lpar.properties['name'])
    status = lpar.activate()

    lpar = cpc.lpars.find(name=LPARNAME)
    print("Status of LPAR %s: %s" % \
          (lpar.properties['name'], lpar.properties['status']))

    print("Loading LPAR %s from device %s ..." % \
          (lpar.properties['name'], LOAD_DEVNO))
    status = lpar.load(LOAD_DEVNO)

    lpar = cpc.lpars.find(name=LPARNAME)
    print("Status of LPAR %s: %s" % \
          (lpar.properties['name'], lpar.properties['status']))

    print("De-Activating LPAR %s ..." % lpar.properties['name'])
    status = lpar.deactivate()

    lpar = cpc.lpars.find(name=LPARNAME)
    print("Status of LPAR %s: %s" % \
          (lpar.properties['name'], lpar.properties['status']))

except zhmcclient.Error as exc:
    print("%s: %s" % (exc.__class__.__name__, exc))
    sys.exit(1)
