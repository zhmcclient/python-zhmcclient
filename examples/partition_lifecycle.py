#!/usr/bin/env python
# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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

"""
Example shows lifecycle (Create-Read-Update-Delete) of a Partition.
"""

import sys
import logging
import yaml
import json
import requests.packages.urllib3
from pprint import pprint

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

partition_lifecycle = examples.get("partition_lifecycle", None)
if partition_lifecycle is None:
    print("partition_lifecycle not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = partition_lifecycle.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = partition_lifecycle["hmc"]
cpcname = partition_lifecycle["cpcname"]
partname = partition_lifecycle["partname"]

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" % \
          (hmc, hmccreds_file))
    sys.exit(1)

userid = cred["userid"]
password = cred["password"]

print(__doc__)

print("Using HMC %s with userid %s ..." % (hmc, userid))
session = zhmcclient.Session(hmc, userid, password)
cl = zhmcclient.Client(session)

timestats = partition_lifecycle.get("timestats", False)
if timestats:
    session.time_stats_keeper.enable()

print("Listing CPCs ...")
cpcs = cl.cpcs.list()
for cpc in cpcs:
    print(cpc)

print("Finding CPC by name=%s ..." % cpcname)
try:
    cpc = cl.cpcs.find(name=cpcname)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (cpcname, hmc))
    sys.exit(1)

print("Checking if DPM is enabled on CPC %s..." % cpc.name)
if not cpc.dpm_enabled:
    print("CPC %s is not in DPM mode." % cpc.name)
    sys.exit(1)
print("CPC %s is in DPM mode." % cpc.name)

print("Finding Partition by name=%s on CPC %s ..." % (partname, cpc.name))
try:
    partition = cpc.partitions.find(name=partname)
except zhmcclient.NotFound:
    print("Partition %s does not exist yet" % partname)
else:
    print("Partition %s already exists - cleaning it up" % partition.name)
    status = partition.get_property('status')
    print("Partition %s status: %s" % (partition.name, status))
    if status == 'active':
        print("Stopping Partition %s ..." % partition.name)
        partition.stop()
    print("Deleting Partition %s ..." % partition.name)
    partition.delete()

properties = {
     'name': partname,
     'description': 'Original partition description.',
     'cp-processors': 2,
     'initial-memory': 1024,
     'maximum-memory': 2048,
     'processor-mode': 'shared',
     'boot-device': 'test-operating-system'
}
print("Creating a new Partition %s on CPC %s with following properties ..."
      % (partname, cpcname))
pprint(properties)
new_partition = cpc.partitions.create(properties)
print("New Partition %s created at: %s" %
      (new_partition.name, new_partition.uri))

print("Starting Partition %s ..." % new_partition.name)
new_partition.start()

print("Description of Partition %s: %s"
    % (new_partition.name, new_partition.get_property('description')))

new_description = "Updated partition description."
print("Updating partition description to: %s" % new_description)
updated_properties = dict()
updated_properties["description"] = new_description
new_partition.update_properties(updated_properties)

print("Refreshing properties of Partition %s ..." % new_partition.name)
new_partition.pull_full_properties()
print("Description of Partition %s: %s"
    % (new_partition.name, new_partition.get_property('description')))

print("Logging off ...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
