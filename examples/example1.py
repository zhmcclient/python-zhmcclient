#!/usr/bin/python
from zhmcwsclient import client

hmc = "192.168...."
user = "admin"
password = "1234"
cl = client.Client(hmc, user, password)
cpcs = cl.cpcs.list()
print len(cpcs)
for cpc in cpcs:
    print cpc.name, cpc.status, getattr(cpc, "object-uri")

lpar = cl.cpcs.find(name="P0000P30")
print lpar

lpars = cpcs[1].lpars.list()
print len(lpars)
for lpar in lpars:
    print lpar.name, lpar.status, getattr(lpar, "object-uri")
