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
Example that exports a DPM configuration from a CPC.
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
    hmccreds = yaml.safe_load(fp)

examples = hmccreds.get("examples", None)
if examples is None:
    print("examples not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

export_dpm_config = examples.get("export_dpm_config", None)
if export_dpm_config is None:
    print("export_dpm_config not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = export_dpm_config.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logmodule = export_dpm_config.get("logmodule", None)
    if logmodule is None:
        logmodule = ''  # root logger
    print("Logging for module %s with level %s" % (logmodule, loglevel))
    handler = logging.StreamHandler()
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(format_string))
    logger = logging.getLogger(logmodule)
    logger.addHandler(handler)
    logger.setLevel(level)

hmc = export_dpm_config["hmc"]
cpcname = export_dpm_config["cpcname"]

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
client = zhmcclient.Client(session)

timestats = export_dpm_config.get("timestats", False)
if timestats:
    session.time_stats_keeper.enable()

print("Finding CPC %s ..." % cpcname)
try:
    cpc = client.cpcs.find(name=cpcname)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (cpcname, hmc))
    sys.exit(1)

if False:
    print("Checking CPC %s to be in DPM mode ..." % cpcname)
    if not cpc.dpm_enabled:
        print("Storage groups require DPM mode, but CPC %s is not in DPM mode" %
              cpcname)
        sys.exit(1)

print("Exporting DPM configuration of CPC %s (all adapters) ..." % cpcname)
dpm_config = cpc.export_dpm_configuration()

print("Fields in returned DPM configuration: {}".format(', '.join(dpm_config.keys())))

print("Comparing some items in the returned DPM configuration with the plain inventory data...")

print("Retrieving inventory data ...")
inventory_data = client.get_inventory(['dpm-resources', 'cpc'])

print("Checking ...")

def check(config_items, inventory_data, classname, uri_prop, prop, value):
    if not isinstance(value, (list, tuple)):
        value = [value]
    inventory_items = [x for x in inventory_data if x['class'] == classname and \
        (True if prop is None else x[prop] in value)]
    missing_uris = set([x[uri_prop] for x in inventory_items]) - set([x[uri_prop] for x in config_items])
    missing_items = sorted([x for x in inventory_items if x[uri_prop] in missing_uris], key=lambda x: x[uri_prop])
    delta = len(inventory_items) - len(config_items)
    print("Checking {}: Inventory: {}, DPM config: {}, delta: {}, missing: {}".
          format(classname, len(inventory_items), len(config_items), delta, len(missing_items)))

adapter_uris = [x['object-uri'] for x in inventory_data if x['class'] == 'adapter' and x['parent'] == cpc.uri]
partition_uris = [x['object-uri'] for x in inventory_data if x['class'] == 'partition' and x['parent'] == cpc.uri]
storage_group_uris = [x['object-uri'] for x in inventory_data if x['class'] == 'storage-group' and x['cpc-uri'] == cpc.uri]

check(dpm_config['adapters'], inventory_data, 'adapter', 'object-uri', 'parent', cpc.uri)
check(dpm_config['network-ports'], inventory_data, 'network-port', 'element-uri', 'parent', adapter_uris)
check(dpm_config['storage-ports'], inventory_data, 'storage-port', 'element-uri', 'parent', adapter_uris)

check(dpm_config['partitions'], inventory_data, 'partition', 'object-uri', 'parent', cpc.uri)
check(dpm_config['nics'], inventory_data, 'nic', 'element-uri', 'parent', partition_uris)
check(dpm_config['hbas'], inventory_data, 'hba', 'element-uri', 'parent', partition_uris)
check(dpm_config['virtual-functions'], inventory_data, 'virtual-function', 'element-uri', 'parent', partition_uris)

check(dpm_config['virtual-switches'], inventory_data, 'virtual-switch', 'object-uri', 'parent', cpc.uri)
check(dpm_config['capacity-groups'], inventory_data, 'capacity-group', 'element-uri', 'parent', cpc.uri)

check(dpm_config['storage-sites'], inventory_data, 'storage-site', 'object-uri', None, None)

check(dpm_config['storage-groups'], inventory_data, 'storage-group', 'object-uri', 'cpc-uri', cpc.uri)
check(dpm_config['storage-volumes'], inventory_data, 'storage-volume', 'element-uri', 'parent', storage_group_uris)

session.logoff()

if timestats:
    print(session.time_stats_keeper)
