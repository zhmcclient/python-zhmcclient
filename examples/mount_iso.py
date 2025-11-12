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
import urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions, setup_hmc_session


def main():
    "Main function of the script"

    urllib3.disable_warnings()

    print(__doc__)

    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} IMAGE_FILE INS_FILE")
        print("Where:")
        print("  IMAGE_FILE  Path name of the ISO image file")
        print("  INS_FILE    Path name of the INS file in the ISO file")
        return 2

    image_file = sys.argv[1]
    image_insfile = sys.argv[2]

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

        print("Finding a CPC in DPM mode ...")
        cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
        if not cpcs:
            print(f"Error: HMC at {host} does not manage any CPCs in DPM mode")
            return 1
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
            print(f"Error: Cannot create partition {part_name} on CPC "
                  f"{cpc.name}: {exc.__class__.__name__}: {exc}")
            return 1

        try:
            try:
                with open(image_file, 'rb') as image_fp:
                    image_name = os.path.basename(image_file)
                    image_size_mb = \
                        1.0 * os.path.getsize(image_file) / 1024 / 1024
                    print(f"Mounting ISO image to partition {part.name} ...")
                    print(f"  Image file: {image_file} (size: "
                          f"{image_size_mb:.1f} MB)")
                    print(f"  Image name: {image_name}")
                    print(f"  Image INS file: {image_insfile}")
                    try:
                        part.mount_iso_image(
                            image_fp, image_name, image_insfile)
                    except zhmcclient.Error as exc:
                        print(f"Error: Cannot mount ISO file {image_file}: "
                              f"{exc.__class__.__name__}: {exc}")
                        return 1
            except OSError as exc:
                print(f"Error: Cannot open image file {image_file}: "
                      f"{exc.__class__.__name__}: {exc}")
                return 1

            part.pull_full_properties()
            image_name = part.get_property('boot-iso-image-name')
            print("Partition property 'boot-iso-image-name' has been set to "
                  f"image name: {image_name}")

            print("Setting 'iso-image' as a boot device ...")
            try:
                part.update_properties({'boot-device': 'iso-image'})
            except zhmcclient.Error as exc:
                print(f"Error: Cannot update properties of partition "
                      f"{part.name}: {exc.__class__.__name__}: {exc}")
                return 1

            print(f"Starting partition {part.name} ...")
            try:
                part.start()
            except zhmcclient.Error as exc:
                print(f"Error: Cannot start partition {part.name}: "
                      f"{exc.__class__.__name__}: {exc}")
                return 1

            part.pull_full_properties()
            status = part.get_property('status')
            print(f"Partition status: {status}")

            return 0

        finally:
            if part.get_property('status') != 'stopped':
                print(f"Stopping partition {part.name} ...")
                try:
                    part.stop(wait_for_completion=True)
                except zhmcclient.Error as exc:
                    print("Error: Stop operation failed with "
                          f"{exc.__class__.__name__}: {exc}")

            print(f"Deleting partition {part.name} ...")
            try:
                part.delete()
            except zhmcclient.Error as exc:
                print(f"Error: Cannot delete partition {part.name} on CPC "
                      f"{cpc.name} for clean up - Please delete it "
                      f"manually: {exc.__class__.__name__}: {exc}")

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
