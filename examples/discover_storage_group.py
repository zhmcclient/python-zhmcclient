#!/usr/bin/env python
# Copyright 2020,2022 IBM Corp. All Rights Reserved.
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
import json
import urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions, setup_hmc_session


def main():
    "Main function of the script"

    urllib3.disable_warnings()

    print(__doc__)

    # Get HMC info from HMC inventory and vault files
    hmc_def = hmc_definitions()[0]
    host = hmc_def.host
    print(f"Creating a session with the HMC at {host} ...")
    try:
        session = setup_hmc_session(hmc_def)
    except zhmcclient.Error as exc:
        print(f"Error: Cannot establish session with HMC {host}: "
              f"{exc.__class__.__name__}: {exc}")
        return 1

    try:
        client = zhmcclient.Client(session)

        print("Finding CPCs in DPM mode ...")
        cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
        if not cpcs:
            print(f"Error: HMC at {host} does not manage any CPCs in DPM mode")
            return 1

        print("Selecting a z14 or higher CPC ...")
        cpc = None
        for _cpc in cpcs:
            se_version_info = \
                [int(v) for v in _cpc.get_property('se-version').split('.')]
            if se_version_info >= [2, 14]:
                cpc = _cpc
                break
        if not cpc:
            print(f"Error: HMC at {host} does not manage any z14 or higher CPC "
                  "in DPM mode")
            return 1
        se_version = cpc.get_property('se-version')
        print(f"Using CPC {cpc.name} (SE version: {se_version})")

        print(f"Listing storage groups of CPC {cpc.name} and selecting the "
              "first FCP storage group ...")
        storage_groups = cpc.list_associated_storage_groups()
        sg = None
        for _sg in storage_groups:
            if _sg.get_property('type') == 'fcp':
                sg = _sg
                break
        if not sg:
            print(f"Could not find any FCP storage group for CPC {cpc.name}")
            return 1
        print(f"Using FCP storage group: {sg.name} "
              f"(type: {sg.get_property('type')}, "
              f"shared: {sg.get_property('shared')}, "
              f"fulfillment: {sg.get_property('fulfillment-state')})")

        print(f"Listing partitions attached to storage group {sg.name} ...")
        parts = sg.list_attached_partitions()
        part_names = [p.name for p in parts]
        part_names_str = ', '.join(part_names) if part_names else "<none>"
        print(f"Partitions attached to storage group {sg.name}: "
              f"{part_names_str}")

        print(f"Getting connection report for storage group {sg.name} ...")
        report = sg.get_connection_report()

        print("fcp-storage-subsystems section of connection report, before "
              "discovery:")
        print(json.dumps(report['fcp-storage-subsystems'], indent=2))

        print("Discovering LUNs of storage group (waiting for completion) ...")
        sg.discover_fcp()

        print(f"Getting connection report for storage group {sg.name} ...")
        report = sg.get_connection_report()

        print("fcp-storage-subsystems section of connection report, after "
              "discovery:")
        print(json.dumps(report['fcp-storage-subsystems'], indent=2))

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
