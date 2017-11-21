#!/usr/bin/env python
# Copyright 2018 IBM Corp. All Rights Reserved.
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
Example that lists storage groups (DPM mode, z14).
"""

import sys
import logging
import yaml
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

list_storage_groups = examples.get("list_storage_groups", None)
if list_storage_groups is None:
    print("list_storage_groups not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = list_storage_groups.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logmodule = list_storage_groups.get("logmodule", None)
    if logmodule is None:
        logmodule = ''  # root logger
    print("Logging for module %s with level %s" % (logmodule, loglevel))
    handler = logging.StreamHandler()
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(format_string))
    logger = logging.getLogger(logmodule)
    logger.addHandler(handler)
    logger.setLevel(level)

hmc = list_storage_groups["hmc"]
cpcname = list_storage_groups["cpcname"]

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" % \
          (hmc, hmccreds_file))
    sys.exit(1)

userid = cred['userid']
password = cred['password']

print(__doc__)

print("Using HMC %s with userid %s ..." % (hmc, userid))
session = zhmcclient.Session(hmc, userid, password)
cl = zhmcclient.Client(session)

timestats = list_storage_groups.get("timestats", False)
if timestats:
    session.time_stats_keeper.enable()

print("Finding CPC %s ..." % cpcname)
try:
    cpc = cl.cpcs.find(name=cpcname)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (cpcname, hmc))
    sys.exit(1)

if False:
    print("Checking CPC %s to be in DPM mode ..." % cpcname)
    if not cpc.dpm_enabled:
        print("Storage groups require DPM mode, but CPC %s is not in DPM mode" %
              cpcname)
        sys.exit(1)

print("Storage Groups of CPC %s ..." % cpcname)
storage_groups = cpc.storage_groups.list()

sgname = list_storage_groups.get("sgname", None)

for sg in storage_groups:

    if sgname and sg.name != sgname:
        print("  Skipping storage group: %s" % sg.name)
        continue

    part_names = [p.name for p in sg.list_attached_partitions()]
    part_names_str = ', '.join(part_names) if part_names else "<none>"
    print("  Storage Group: %s (type: %s, shared: %s, fulfillment: %s, "
          "attached to partitions: %s)" %
          (sg.name, sg.get_property('type'), sg.get_property('shared'),
           sg.get_property('fulfillment-state'), part_names_str))

    try:
        volumes = sg.storage_volumes.list()
    except zhmcclient.HTTPError as exc:
        print("Error listing storage volumes of storage group %s:\n"
              "HTTPError: %s" % (sg.name, exc))
        volumes = []
    for sv in volumes:
        print("    Storage Volume: %s (oid: %s, uuid: %s, size: %s GiB, "
              "fulfillment: %s)" %
              (sv.name, sv.oid, sv.prop('uuid', 'N/A'),
               sv.get_property('size'), sv.get_property('fulfillment-state')))

    try:
        vsrs = sg.virtual_storage_resources.list()
    except zhmcclient.HTTPError as exc:
        print("Error listing virtual storage resources of storage group %s:\n"
              "HTTPError: %s" % (sg.name, exc))
        vsrs = []
    for vsr in vsrs:
        port = vsr.adapter_port
        adapter = port.manager.parent
        print("    Virtual Storage Resource: %s (devno: %s, "
              "adapter.port: %s.%s, attached to partition: %s)" %
              (vsr.name, vsr.get_property('device-number'),
               adapter.name, port.name, vsr.attached_partition.name))

session.logoff()

if timestats:
    print(session.time_stats_keeper)
