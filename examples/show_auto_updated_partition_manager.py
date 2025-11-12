#!/usr/bin/env python
# Copyright 2022 IBM Corp. All Rights Reserved.
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
Example that shows the auto-updating of a partition manager on a CPC in DPM
mode.

The shorter durations of list() indicate that the locally maintained list was
used; the longer durations indicate that a list operation was performed on the
HMC.
"""

import sys
import uuid
import logging
from datetime import datetime, timedelta
import urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions, setup_hmc_session

# Flag to control logging of the HTTP and notification interactions with
# the HMC to stderr.
ENABLE_LOGGING = False


def delta_ms(start_dt, end_dt):
    """Return float that is the time delta in milliseconds"""
    return (end_dt - start_dt) / timedelta(microseconds=1) / 1000


def main():
    "Main function of the script"

    urllib3.disable_warnings()

    if ENABLE_LOGGING:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

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

    cleanup_partition = None
    try:
        client = zhmcclient.Client(session)

        print("Finding a CPC in DPM mode ...")
        cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
        if not cpcs:
            print(f"Error: HMC at {host} does not manage any CPCs in DPM mode")
            return 1
        cpc = cpcs[0]
        print(f"Using CPC {cpc.name}")

        part_mgr = cpc.partitions

        print("Listing partitions using list() (not auto-enabled) ...")
        start_dt = datetime.now()
        part_list = part_mgr.list()
        end_dt = datetime.now()
        print(f"Result of list(): returned {len(part_list)} partitions in "
              f"{delta_ms(start_dt, end_dt)} ms")

        print("Enabling auto-updating for partition manager")
        try:
            part_mgr.enable_auto_update()
        except zhmcclient.Error as exc:
            print(f"Error: Cannot auto-enable partition manager for CPC "
                  f"{cpc.name}: {exc.__class__.__name__}: {exc}")
            return 1

        print("Listing partitions using list() "
              "(auto-enabled - uses from local list) ...")
        start_dt = datetime.now()
        part_list = part_mgr.list()
        end_dt = datetime.now()
        print(f"Result of list(): returned {len(part_list)} partitions in "
              f"{delta_ms(start_dt, end_dt)} ms")

        part_name = f"zhmc_test_{uuid.uuid4()}"
        print(f"Creating partition {part_name} ...")
        part_props = {
            'name': part_name,
            'description': 'Original partition description.',
            'cp-processors': 2,
            'initial-memory': 1024,
            'maximum-memory': 2048,
            'processor-mode': 'shared'
        }
        try:
            part = cpc.partitions.create(properties=part_props)
            cleanup_partition = part
        except zhmcclient.Error as exc:
            print(f"Error: Cannot create partition {part_name} on CPC "
                  f"{cpc.name}: {exc.__class__.__name__}: {exc}")
            return 1
        print(f"Partition uri: {part.uri}")

        print("Listing partitions using list() "
              "(auto-enabled - added partition causes pull from HMC) ...")
        start_dt = datetime.now()
        part_list = part_mgr.list()
        end_dt = datetime.now()
        print(f"Result of list(): returned {len(part_list)} partitions in "
              f"{delta_ms(start_dt, end_dt)} ms")

        print("Listing partitions using list() "
              "(auto-enabled - uses from local list) ...")
        start_dt = datetime.now()
        part_list = part_mgr.list()
        end_dt = datetime.now()
        print(f"Result of list(): returned {len(part_list)} partitions in "
              f"{delta_ms(start_dt, end_dt)} ms")

        print(f"Deleting partition {part.name} (uri: {part.uri}) ...")
        try:
            part.delete()
            cleanup_partition = None
        except zhmcclient.Error as exc:
            print(f"Error: Cannot delete partition {part.name} on CPC "
                  "{cpc.name} for clean up - Please delete it manually: "
                  f"{exc.__class__.__name__}: {exc}")
            return 1

        print("Listing partitions using list() "
              "(auto-enabled - uses from local list) ...")
        start_dt = datetime.now()
        part_list = part_mgr.list()
        end_dt = datetime.now()
        print(f"Result of list(): returned {len(part_list)} partitions in "
              f"{delta_ms(start_dt, end_dt)} ms")

        print("Disabling auto-updating for partition manager")
        part_mgr.disable_auto_update()

        print("Listing partitions using list() (not auto-enabled) ...")
        start_dt = datetime.now()
        part_list = part_mgr.list()
        end_dt = datetime.now()
        print(f"Result of list(): returned {len(part_list)} partitions in "
              f"{delta_ms(start_dt, end_dt)} ms")

        return 0

    finally:
        if cleanup_partition:
            print(f"Cleanup: Deleting partition {cleanup_partition.name} ...")
            try:
                cleanup_partition.delete()
            except zhmcclient.Error as exc:
                print(f"Error: Cannot delete partition {part.name} on CPC "
                      f"{cpc.name} for clean up - Please delete it "
                      f"manually: {exc.__class__.__name__}: {exc}")
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
