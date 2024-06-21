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
Example that uses the auto-updating of resource properties on a partition on
a CPC in DPM mode.
"""

import sys
import uuid
import requests.packages.urllib3
from time import sleep

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

    part_name = f"zhmc_test_{uuid.uuid4()}"
    print(f"Creating partition {part_name} ...")
    part_props = {
        'name': part_name,
        'description': 'Original partition description.',
        'cp-processors': 2,
        'initial-memory': 1024,
        'maximum-memory': 2048,
        'processor-mode': 'shared',
        'boot-device': 'test-operating-system'
    }
    try:
        part = cpc.partitions.create(properties=part_props)
    except zhmcclient.Error as exc:
        print(f"Error: Cannot create partition {part_name} on CPC {cpc.name}: "
              f"{exc.__class__.__name__}: {exc}")
        sys.exit(1)

    try:
        obj_topic = session.object_topic
        print(f"Object notification topic: {obj_topic}")

        # Two different zhmcclient.Partition objects representing the same
        # partition on the HMC
        partition1 = cpc.partitions.find(name=part_name)
        partition2 = cpc.partitions.find(name=part_name)

        # The property that will be updated
        part_prop = 'description'

        print("Enabling auto-update for partition object 1 for partition "
              f"{part_name} (id={id(partition1)})")
        partition1.enable_auto_update()

        print("Not enabling auto-update for partition object 2 for partition "
              f"{part_name} (id={id(partition2)})")

        print(f"Entering loop that displays property '{part_prop}' of "
              "partition objects 1 and 2")
        print("")
        print(f"==> Update property '{part_prop}' of partition '{part_name}' "
              f"on CPC '{cpc.name}' from another session")
        print(f"==> Delete partition '{part_name}' on CPC '{cpc.name}' from "
              "another session")
        print("")
        try:
            while True:
                try:
                    value1 = partition1.prop(part_prop)
                except zhmcclient.CeasedExistence:
                    value1 = 'N/A'
                value2 = partition2.prop(part_prop)
                print(f"Property '{part_prop}' on partition objects 1: "
                      f"{value1!r}, 2: {value2!r}")
                sleep(1)
        except KeyboardInterrupt:
            print("Keyboard interrupt - leaving loop")
        finally:
            print("Disabling auto-update for partition object 1")
            partition1.disable_auto_update()

    finally:
        print(f"Deleting partition {part.name} ...")
        try:
            part.delete()
        except zhmcclient.Error as exc:
            print(f"Error: Cannot delete partition {part.name} on CPC "
                  f"{cpc.name} for clean up - "
                  f"Please delete it manually: {exc.__class__.__name__}: {exc}")
            sys.exit(1)

finally:
    print("Logging off ...")
    session.logoff()
