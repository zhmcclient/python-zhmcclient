#!/usr/bin/env python
#
# Example for listing CPCs and LPARs on a CPC.
#

import sys
import yaml
import requests.packages.urllib3

import zhmcclient

HMC = "9.152.150.86"         # HMC to use
CPCNAME = "P0000P28"         # CPC to list on that HMC

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

print("Using HMC %s with userid %s ..." % (HMC, userid))
session = zhmcclient.Session(HMC, userid, password)
cl = zhmcclient.Client(session)

print("Listing CPCs ...")
cpcs = cl.cpcs.list()
for cpc in cpcs:
#    print(cpc.name, cpc.status, getattr(cpc, "object-uri"))
    print(cpc.properties['name'], cpc.properties['status'],
          cpc.properties['object-uri'])

print("Finding CPC by name=%s ..." % CPCNAME)
try:
    cpc = cl.cpcs.find(name=CPCNAME)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (CPCNAME, HMC))
    sys.exit(1)

print("Listing LPARs on CPC %s ..." % CPCNAME)
lpars = cpc.lpars.list()
for lpar in lpars:
    print(lpar.properties['name'], lpar.properties['status'],
          lpar.properties['object-uri'])
