#!/usr/bin/python
from zhmcwsclient import client
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

hmc = "192.168...."
user = "admin"
password = "1234"
cl = client.Client(hmc, user, password)

cpc = cl.cpcs.find(name="P0000P30", status="service-required")
print cpc.name, cpc.status

lpar = cpc.lpars.find(name="PART8")
print lpar.name, lpar.status

print "De-Activating ..."
status = lpar.deactivate()
print status

lpar = cpc.lpars.find(name="PART8")
print lpar.name, lpar.status

print "Activating ..."
status = lpar.activate()
print status
lpar = cpc.lpars.find(name="PART8")
print lpar.name, lpar.status

print "Loading ..."
status = lpar.load("5172")
lpar = cpc.lpars.find(name="PART8")
print lpar.name, lpar.status

# print "De-Activating ..."
# status = lpar.deactivate()
# print status

# lpar = cpc.lpars.find(name="PART8")
# print lpar.name, lpar.status
