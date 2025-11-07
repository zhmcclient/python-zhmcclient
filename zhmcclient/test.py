#!/usr/bin/env python

import zhmcclient
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
from zhmcclient._manager import BaseManager
from zhmcclient._cpc import CpcManager,Cpc


# Set these variables for your environment:
host = "9.152.57.200"
userid = "service"
password = "passwordforapi"
verify_cert = False

session = zhmcclient.Session(host, userid, password, verify_cert=verify_cert)
client = zhmcclient.Client(session)

cpcs =CpcManager(client)
print(cpcs.list())


cpc = Cpc(cpcs,'/api/cpcs/f81f6e55-40ad-329b-9d9f-56a9a10df992')
print(cpc.pull_full_properties())
print(cpc.partitions.list())