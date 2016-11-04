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

"""
Example 5: CRUD (Create-Read-Update-Delete) example for Partitions.
"""

import sys
import logging
import yaml
import json
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

example5 = examples.get("example5", None)
if example5 is None:
    print("example5 not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = example5.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = example5["hmc"]
cpcname = example5["cpcname"]
partname = example5["partname"]

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

timestats = example5.get("timestats", False)
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

print("Checking if DPM is enabled on CPC %s..." % cpcname)
if cpc.dpm_enabled:
    print("CPC %s is in DPM mode." % cpcname)
    if cpc.properties['status'] not in ('active', 'service-required'):
        print("CPC %s is in an inactive state: %s" %
              (cpcname, cpc.properties['status']))
        sys.exit(1)
    try:
        print("Finding Partition by name=%s ..." % partname)
        partition = cpc.partitions.find(name=partname)
        if partition.properties['status'] == 'active':
            print("Stopping Partition %s ..." % partname)
            partition.stop()
        print("Deleting Partition %s ..." % partname)
        partition.delete()
    except zhmcclient.NotFound:
        print("Could not find Partition %s on CPC %s" % (partname, cpcname))

    print("Creating a new Partition %s on CPC %s with following properties ..."
          % (partname, cpcname))
    properties = {
         'name': partname,
         'description': 'Original partition description.',
         'cp-processors': 2,
         'initial-memory': 1024,
         'maximum-memory': 2048,
         'processor-mode': 'shared',
         'boot-device': 'test-operating-system'
    }
    print(json.dumps(properties, indent=4))
    new_partition = cpc.partitions.create(properties)
    print("New Partition created: %s" % new_partition)

    print("Starting Partition %s ..." % partname)
    new_partition.start()

    print("Pull full properties of Partition %s ..." % partname)
    new_partition.pull_full_properties()
    print("Description of Partition %s: %s"
        % (partname, new_partition.properties["description"]))

    print("Updating Partition %s properties ..." % partname)
    updated_properties = dict()
    updated_properties["description"] = "Updated partition description."
    new_partition.update_properties(updated_properties)

    print("Pull full properties of Partition %s ..." % partname)
    new_partition.pull_full_properties()
    print("Updated description of Partition %s: %s"
        % (partname, new_partition.properties["description"]))

else:
    print("CPC %s is not in DPM mode." % cpcname)

print("Logging off ...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
