#!/usr/bin/env python
# Copyright 2021,2022 IBM Corp. All Rights Reserved.
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

# Get HMC info from HMC inventory and vault files
hmc_def = hmc_definitions()[0]
nickname = hmc_def.nickname
host = hmc_def.host
userid = hmc_def.userid
password = hmc_def.password
verify_cert = hmc_def.verify_cert


def check(config_items, inventory_data, classname, uri_prop, prop, value):
    """Check an item in the exported DPM config against the inventory data."""
    if config_items is None:
        return
    if not isinstance(value, (list, tuple)):
        value = [value]
    inventory_items = [x for x in inventory_data if x['class'] == classname
                       and (True if prop is None else x[prop] in value)]
    extra_uris = {x[uri_prop] for x in config_items} - \
        {x[uri_prop] for x in inventory_items}
    missing_uris = {x[uri_prop] for x in inventory_items} - \
        {x[uri_prop] for x in config_items}
    status = 'Error' if extra_uris or missing_uris else 'Ok'
    print(f"Checking resource class {classname!r}: "
          f"Inventory: {len(inventory_items)}; DPM config: {len(config_items)} "
          f"(extra: {len(extra_uris)}, missing: {len(missing_uris)}); "
          f"Check status: {status}")


print(__doc__)

print(f"Using HMC {nickname} at {host} with userid {userid} ...")

print("Creating a session with the HMC ...")
try:
    session = zhmcclient.Session(
        host, userid, password, verify_cert=verify_cert)
except zhmcclient.Error as exc:
    print(f"Error: Cannot establish session with HMC {host}: "
          f"{exc.__class__.__name__}: {exc}")
    sys.exit(1)

try:
    client = zhmcclient.Client(session)

    print("Finding a CPC in DPM mode ...")
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
    if not cpcs:
        print(f"Error: HMC at {host} does not manage any CPCs in DPM mode")
        sys.exit(1)
    cpc = cpcs[0]
    print(f"Using CPC {cpc.name}")

    print(f"Exporting DPM configuration of CPC {cpc.name} ...")
    try:
        dpm_config = cpc.export_dpm_configuration()
    except zhmcclient.ConsistencyError as exc:
        print(f"Error: Cannot export DPM configuration: {exc}")
        sys.exit(1)
    fields_str = ', '.join(dpm_config.keys())
    print(f"Fields in exported DPM configuration: {fields_str}")

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

    check(dpm_config.get('adapters'), inventory_data,
          'adapter', 'object-uri', 'parent', cpc.uri)
    check(dpm_config.get('network-ports'), inventory_data,
          'network-port', 'element-uri', 'parent', adapter_uris)
    check(dpm_config.get('storage-ports'), inventory_data,
          'storage-port', 'element-uri', 'parent', adapter_uris)

    check(dpm_config.get('partitions'), inventory_data,
          'partition', 'object-uri', 'parent', cpc.uri)
    check(dpm_config.get('nics'), inventory_data,
          'nic', 'element-uri', 'parent', partition_uris)
    check(dpm_config.get('hbas'), inventory_data,
          'hba', 'element-uri', 'parent', partition_uris)
    check(dpm_config.get('virtual-functions'), inventory_data,
          'virtual-function', 'element-uri', 'parent', partition_uris)

    check(dpm_config.get('virtual-switches'), inventory_data,
          'virtual-switch', 'object-uri', 'parent', cpc.uri)
    check(dpm_config.get('capacity-groups'), inventory_data,
          'capacity-group', 'element-uri', 'parent', cpc.uri)

    check(dpm_config.get('storage-sites'), inventory_data,
          'storage-site', 'object-uri', None, None)

    check(dpm_config.get('storage-groups'), inventory_data,
          'storage-group', 'object-uri', 'cpc-uri', cpc.uri)
    check(dpm_config.get('storage-volumes'), inventory_data,
          'storage-volume', 'element-uri', 'parent', storage_group_uris)

finally:
    print("Logging off ...")
    session.logoff()
