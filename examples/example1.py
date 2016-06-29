#!/usr/bin/env python

import zhmcclient
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

hmc = "192.168....."
user = "admin"
password = "password"
cpcname = "P0000P28"

cl = zhmcclient.Client(hmc, user, password)

cpcs = cl.cpcs.list()
print("Found %d CPCs on HMC %s:" % (len(cpcs), hmc))
for cpc in cpcs:
    print(cpc.name, cpc.status, getattr(cpc, "object-uri"))

cpc = cl.cpcs.find(name=cpcname)
lpars = cpc.lpars.list()
print("Found %d LPARs on CPC %s:" % (len(lpars), cpcname))
for lpar in lpars:
    print(lpar.name, lpar.status, getattr(lpar, "object-uri"))

