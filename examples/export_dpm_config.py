#!/usr/bin/env python
# Copyright 2021-2022 IBM Corp. All Rights Reserved.
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
Example that exports a DPM configuration from a CPC and checks it for
consistency with the inventory data.
"""

import sys
import requests.packages.urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions

requests.packages.urllib3.disable_warnings()

# Get HMC info from HMC definition file
hmc_def = hmc_definitions()[0]
nick = hmc_def.nickname
host = hmc_def.hmc_host
userid = hmc_def.hmc_userid
password = hmc_def.hmc_password
verify_cert = hmc_def.hmc_verify_cert


def check(config_items, inventory_data, classname, uri_prop, prop, value):
    """Check an item in the exported DPM config against the inventory data."""
    if not isinstance(value, (list, tuple)):
        value = [value]
    inventory_items = [x for x in inventory_data if x['class'] == classname
                       and (True if prop is None else x[prop] in value)]
    missing_uris = set([x[uri_prop] for x in inventory_items]) - \
        set([x[uri_prop] for x in config_items])
    missing_items = sorted([x for x in inventory_items
                            if x[uri_prop] in missing_uris],
                           key=lambda x: x[uri_prop])
    delta = len(inventory_items) - len(config_items)
    print("Checking {}: Inventory: {}, DPM config: {}, delta: {}, missing: {}".
          format(classname, len(inventory_items), len(config_items),
                 delta, len(missing_items)))


print(__doc__)

print("Using HMC {} at {} with userid {} ...".format(nick, host, userid))

print("Creating a session with the HMC ...")
try:
    session = zhmcclient.Session(
        host, userid, password, verify_cert=verify_cert)
except zhmcclient.Error as exc:
    print("Error: Cannot establish session with HMC {}: {}: {}".
          format(host, exc.__class__.__name__, exc))
    sys.exit(1)

try:
    client = zhmcclient.Client(session)

    print("Finding a CPC in DPM mode ...")
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
    if not cpcs:
        print("Error: HMC at {} does not manage any CPCs in DPM mode".
              format(host))
        sys.exit(1)
    cpc = cpcs[0]
    print("Using CPC {}".format(cpc.name))

    print("Exporting DPM configuration of CPC {} ...".format(cpc.name))
    dpm_config = cpc.export_dpm_configuration()

    print("Fields in exported DPM configuration: {}".
          format(', '.join(dpm_config.keys())))

    print("Checking some items in the exported DPM configuration for "
          "consistency with the inventory data ...")

    print("Retrieving inventory data ...")
    inventory_data = client.get_inventory(['dpm-resources', 'cpc'])

    adapter_uris = [x['object-uri'] for x in inventory_data
                    if x['class'] == 'adapter' and x['parent'] == cpc.uri]
    partition_uris = [x['object-uri'] for x in inventory_data
                      if x['class'] == 'partition' and x['parent'] == cpc.uri]
    storage_group_uris = [x['object-uri'] for x in inventory_data
                          if x['class'] == 'storage-group'
                          and x['cpc-uri'] == cpc.uri]

    check(dpm_config['adapters'], inventory_data,
          'adapter', 'object-uri', 'parent', cpc.uri)
    check(dpm_config['network-ports'], inventory_data,
          'network-port', 'element-uri', 'parent', adapter_uris)
    check(dpm_config['storage-ports'], inventory_data,
          'storage-port', 'element-uri', 'parent', adapter_uris)

    check(dpm_config['partitions'], inventory_data,
          'partition', 'object-uri', 'parent', cpc.uri)
    check(dpm_config['nics'], inventory_data,
          'nic', 'element-uri', 'parent', partition_uris)
    check(dpm_config['hbas'], inventory_data,
          'hba', 'element-uri', 'parent', partition_uris)
    check(dpm_config['virtual-functions'], inventory_data,
          'virtual-function', 'element-uri', 'parent', partition_uris)

    check(dpm_config['virtual-switches'], inventory_data,
          'virtual-switch', 'object-uri', 'parent', cpc.uri)
    check(dpm_config['capacity-groups'], inventory_data,
          'capacity-group', 'element-uri', 'parent', cpc.uri)

    check(dpm_config['storage-sites'], inventory_data,
          'storage-site', 'object-uri', None, None)

    check(dpm_config['storage-groups'], inventory_data,
          'storage-group', 'object-uri', 'cpc-uri', cpc.uri)
    check(dpm_config['storage-volumes'], inventory_data,
          'storage-volume', 'element-uri', 'parent', storage_group_uris)

finally:
    print("Logging off ...")
    session.logoff()
