#!/usr/bin/env python
# Copyright 2020-2021 IBM Corp. All Rights Reserved.
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
Example that discovers a storage group and prints the connection report
(DPM mode, z14).
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
    hmccreds = yaml.safe_load(fp)

examples = hmccreds.get("examples", None)
if examples is None:
    print("examples not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

discover_storage_group = examples.get("discover_storage_group", None)
if discover_storage_group is None:
    print("discover_storage_group not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = discover_storage_group.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logmodule = discover_storage_group.get("logmodule", None)
    if logmodule is None:
        logmodule = ''  # root logger
    print("Logging for module %s with level %s" % (logmodule, loglevel))
    handler = logging.StreamHandler()
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(format_string))
    logger = logging.getLogger(logmodule)
    logger.addHandler(handler)
    logger.setLevel(level)

hmc = discover_storage_group["hmc"]
cpcname = discover_storage_group["cpcname"]

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

api_dict = cl.query_api_version()
api_version = '%d.%d' % (api_dict['api-major-version'],
                         api_dict['api-minor-version'])
hmc_version = api_dict['hmc-version']
print("HMC version: %s" % hmc_version)
print("HMC API version: %s" % api_version)

timestats = discover_storage_group.get("timestats", False)
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

storage_groups = cpc.list_associated_storage_groups()
fcp_sg = None
for sg in storage_groups:
    if sg.get_property('type') == 'fcp':
        fcp_sg = sg
        break
if not fcp_sg:
    print("Could not find an FCP storage group on HMC %s" % hmc)
    sys.exit(1)

sgname = discover_storage_group.get("sgname") or fcp_sg.name

try:
    sg = cl.consoles.console.storage_groups.find(name=sgname)
except zhmcclient.NotFound:
    print("Could not find storage group %s on HMC %s" % (sgname, hmc))
    sys.exit(1)

part_names = [p.name for p in sg.list_attached_partitions()]
part_names_str = ', '.join(part_names) if part_names else "<none>"
print("Storage Group: %s (type: %s, shared: %s, fulfillment: %s, "
      "attached to partitions: %s)" %
      (sg.name, sg.get_property('type'), sg.get_property('shared'),
       sg.get_property('fulfillment-state'), part_names_str))


print("Getting connection report...")
report = sg.get_connection_report()

print("fcp-storage-subsystems section of connection report, before discovery:")
print(json.dumps(report['fcp-storage-subsystems'], indent=2))

print("Discovering LUNs of storage group (waiting for completion)...")
sg.discover_fcp()

print("Getting connection report...")
report = sg.get_connection_report()

print("fcp-storage-subsystems section of connection report, after discovery:")
print(json.dumps(report['fcp-storage-subsystems'], indent=2))

session.logoff()

if timestats:
    print(session.time_stats_keeper)
