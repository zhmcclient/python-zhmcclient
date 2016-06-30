#!/usr/bin/env python

import sys
import requests.packages.urllib3

import zhmcclient

hmc = "192.168...."
user = "admin"
password = "password"

# LPAR top be used for this example.
# Attention: This LPAR will be deactivated and rebooted!
cpcname = "P0000P30"
lparname = "PART8"
load_devno = "5172"

requests.packages.urllib3.disable_warnings()

try:
    cl = zhmcclient.Client(hmc, user, password)

    cpc = cl.cpcs.find(name=cpcname, status="service-required")
    print("Status of CPC %s: %s" % (cpc.name, cpc.status))

    lpar = cpc.lpars.find(name=lparname)
    print("Status of LPAR %s: %s" % (lpar.name, lpar.status))

    print("De-Activating LPAR %s ..." % lparname)
    status = lpar.deactivate()
    print("Return value: %s" % status)

    lpar = cpc.lpars.find(name=lparname)
    print("Status of LPAR %s: %s" % (lpar.name, lpar.status))

    print("Activating LPAR %s ..." % lparname)
    status = lpar.activate()
    print("Return value: %s" % status)

    lpar = cpc.lpars.find(name=lparname)
    print("Status of LPAR %s: %s" % (lpar.name, lpar.status))

    print("Loading LPAR %s from device %s ..." % (lparname, load_devno))
    status = lpar.load("5172")
    print("Return value: %s" % status)

    lpar = cpc.lpars.find(name=lparname)
    print("Status of LPAR %s: %s" % (lpar.name, lpar.status))

    print("De-Activating LPAR %s ..." % lparname)
    status = lpar.deactivate()
    print("Return value: %s" % status)

    lpar = cpc.lpars.find(name=lparname)
    print("Status of LPAR %s: %s" % (lpar.name, lpar.status))

except zhmcclient.Error as exc:
    print("%s: %s" % (exc.__class__.__name__, exc))
    sys.exit(1)
