#!/usr/bin/env python
# Copyright 2021 IBM Corp. All Rights Reserved.
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
Example that shows the auto-update of resource properties.
"""

import sys
import logging
import yaml
import requests.packages.urllib3
from time import sleep

import zhmcclient

# Print metadata for each OS message, before each message
PRINT_METADATA = False

requests.packages.urllib3.disable_warnings()

if len(sys.argv) != 2:
    print("Usage: %s hmccreds.yaml" % sys.argv[0])
    sys.exit(2)
hmccreds_file = sys.argv[1]

with open(hmccreds_file, 'r') as fp:
    hmccreds = yaml.safe_load(fp)

examples = hmccreds.get("examples", None)
if examples is None:
    print("examples not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

show_auto_update = examples.get("show_auto_update", None)
if show_auto_update is None:
    print("show_auto_update not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = show_auto_update.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logmodule = show_auto_update.get("logmodule", None)
    if logmodule is None:
        logmodule = ''  # root logger
    print("Logging for module %s with level %s" % (logmodule, loglevel))
    handler = logging.StreamHandler()
    format_string = '%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(format_string))
    logger = logging.getLogger(logmodule)
    logger.addHandler(handler)
    logger.setLevel(level)

hmc = show_auto_update["hmc"]
cpcname = show_auto_update["cpcname"]
partname = show_auto_update["partname"]
partprop = show_auto_update["partprop"]

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" % \
          (hmc, hmccreds_file))
    sys.exit(1)

userid = cred['userid']
password = cred['password']

print(__doc__)

print("Using HMC %s with userid %s ..." % (hmc, userid))
session = zhmcclient.Session(hmc, userid, password, verify_cert=False)
cl = zhmcclient.Client(session)

timestats = show_auto_update.get("timestats", False)
if timestats:
    session.time_stats_keeper.enable()

session.logon()
topic = session.object_topic
if topic is None:
    print("Error: Object notification topic is not set")
    sys.exit(1)

print("Object notification topic: %s" % topic)

cpc = cl.cpcs.find(name=cpcname)

# Two different zhmcclient.Partition objects representing the same partition
# on the HMC
partition1 = cpc.partitions.find(name=partname)
partition2 = cpc.partitions.find(name=partname)

print("Enabling auto-update for partition object 1 for partition {} (id={})".
      format(partname, id(partition1)))
sys.stdout.flush()
partition1.enable_auto_update()

print("Not enabling auto-update for partition object 2 for partition {} "
      "(id={})".format(partname, id(partition2)))

print("Entering loop that displays property '{}' of partition objects 1 and 2".
      format(partprop))
sys.stdout.flush()
try:
    while True:
        value1 = partition1.prop(partprop)
        value2 = partition2.prop(partprop)
        print("Property '{}' on partition objects 1: {!r}, 2: {!r}".
              format(partprop, value1, value2))
        sys.stdout.flush()
        sleep(1)
except KeyboardInterrupt:
    print("Keyboard interrupt - leaving loop")
    sys.stdout.flush()
finally:
    print("Disabling auto-update for partition object 1")
    sys.stdout.flush()
    partition1.disable_auto_update()

print("Logging off...")
sys.stdout.flush()
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
