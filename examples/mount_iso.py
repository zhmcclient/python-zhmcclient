#!/usr/bin/env python
# Copyright 2016,2022 IBM Corp. All Rights Reserved.
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
Example that mounts an ISO image to a partition and starts the partition
on a CPC in DPM mode.
"""

import sys
import os
import uuid
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

# Customize: Set to the ISO image you want to mount:
# path name of image file on local system
image_file = 'try/SLE-12-Server-DVD-s390x-GM-DVD1.iso'
# path name of INS file within ISO image, or None
image_insfile = 'my_insfile'

print(__doc__)

print(f"Using HMC {nickname} at {host} with userid {userid} ...")

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
    print(f"Using CPC {cpc.name}")

    part_name = f"zhmc_test_{uuid.uuid4()}"
    print(f"Creating partition {part_name} ...")
    try:
        part = cpc.partitions.create(
            properties={
                'name': part_name,
                'type': 'linux',
                'ifl-processors': 2,
                'initial-memory': 4096,
                'maximum-memory': 4096,
            })
    except zhmcclient.Error as exc:
        print("Error: Cannot create partition {} on CPC {}: {}: {}".
              format(part_name, cpc.name, exc.__class__.__name__, exc))
        sys.exit(1)

    try:
        try:
            with open(image_file, 'rb') as image_fp:
                image_name = os.path.basename(image_file)
                image_size_mb = 1.0 * os.path.getsize(image_file) / 1024 / 1024
                print("Mounting ISO image to partition {} ...".
                      format(part.name))
                print("  Image file: {} (size: {:.1f} MB)".
                      format(image_file, image_size_mb))
                print(f"  Image name: {image_name}")
                print(f"  Image INS file: {image_insfile}")
                try:
                    part.mount_iso_image(image_fp, image_name, image_insfile)
                except zhmcclient.Error as exc:
                    print("Error: Cannot mount ISO file {}: {}: {}".
                          format(image_file, exc.__class__.__name__, exc))
                    sys.exit(1)
        except OSError as exc:
            print("Error: Cannot open image file {}: {}: {}".
                  format(image_file, exc.__class__.__name__, exc))
            sys.exit(1)

        part.pull_full_properties()
        print("Partition property 'boot-iso-image-name' has been set to image "
              "name: {}".format(part.get_property('boot-iso-image-name')))

        print("Setting 'iso-image' as a boot device ...")
        try:
            part.update_properties({'boot-device': 'iso-image'})
        except zhmcclient.Error as exc:
            print("Error: Cannot update properties of partition {}: {}: {}".
                  format(part.name, exc.__class__.__name__, exc))
            sys.exit(1)

        print(f"Starting partition {part.name} ...")
        try:
            part.start()
        except zhmcclient.Error as exc:
            print("Error: Cannot start partition {}: {}: {}".
                  format(part.name, exc.__class__.__name__, exc))
            sys.exit(1)

        part.pull_full_properties()
        status = part.get_property('status')
        print(f"Partition status: {status}")

    finally:
        if part.get_property('status') != 'stopped':
            print(f"Stopping partition {part.name} ...")
            try:
                part.stop(wait_for_completion=True)
            except zhmcclient.Error as exc:
                print("Error: Stop operation failed with {}: {}".
                      format(exc.__class__.__name__, exc))
                sys.exit(1)

        print(f"Deleting partition {part.name} ...")
        try:
            part.delete()
        except zhmcclient.Error as exc:
            print("Error: Cannot delete partition {} on CPC {} for clean up - "
                  "Please delete it manually: {}: {}".
                  format(part.name, cpc.name, exc.__class__.__name__, exc))
            sys.exit(1)

finally:
    print("Logging off ...")
    session.logoff()
