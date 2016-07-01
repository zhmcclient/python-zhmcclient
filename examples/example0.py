#!/usr/bin/env python
#
# Example for showing the API version of an HMC.
#

import sys
import yaml
import requests.packages.urllib3

import zhmcclient

HMC = "9.152.150.86"         # HMC to use

requests.packages.urllib3.disable_warnings()

if len(sys.argv) != 1:
    print("Usage: %s" % sys.argv[0])
    sys.exit(2)

print("Using HMC %s without any userid ..." % HMC)
session = zhmcclient.Session(HMC)
cl = zhmcclient.Client(session)

vi = cl.version_info()
print("HMC API version: {}.{}".format(vi[0], vi[1]))

