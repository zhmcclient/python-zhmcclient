#!/usr/bin/env python
# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
Example mounting an ISO image to an existing partition and starting the partition.
"""

import sys
import io
import logging
import yaml
import json
import requests.packages.urllib3
from pprint import pprint

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

mount_iso = examples.get("mount_iso", None)
if mount_iso is None:
    print("mount_iso not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = mount_iso.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = mount_iso["hmc"]
cpcname = mount_iso["cpcname"]
partname = mount_iso["partname"]
imagename = mount_iso["imagename"]
imagefile = mount_iso["imagefile"]
imageinsfile = mount_iso["imageinsfile"]

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" % \
          (hmc, hmccreds_file))
    sys.exit(1)

userid = cred["userid"]
password = cred["password"]

print(__doc__)

print("Using HMC %s with userid %s ..." % (hmc, userid))
session = zhmcclient.Session(hmc, userid, password)
cl = zhmcclient.Client(session)

timestats = mount_iso.get("timestats", False)
if timestats:
    session.time_stats_keeper.enable()

try:
    print("Finding CPC by name=%s ..." % cpcname)
    try:
        cpc = cl.cpcs.find(name=cpcname)
    except zhmcclient.NotFound:
        print("Error: Could not find CPC %s on HMC %s" % (cpcname, hmc))
        sys.exit(1)

    #print("Checking if DPM is enabled on CPC %s..." % cpc.name)
    #if not cpc.dpm_enabled:
    #    print("Error: CPC %s is not in DPM mode." % cpc.name)
    #    sys.exit(1)

    print("Finding Partition by name=%s on CPC %s ..." % (partname, cpc.name))
    try:
        partition = cpc.partitions.find(name=partname)
    except zhmcclient.NotFound:
        print("Error: Partition %s does not exist" % partname)
        sys.exit(1)

    status = partition.get_property('status')
    print("Partition %s status: %s" % (partition.name, status))
    if status == 'active':
        print("Stopping Partition %s ..." % partition.name)
        partition.stop()

    print("Opening image file %s ..." % imagefile)
    image_fp = open(imagefile, 'rb')
    print("Mounting image file as ISO image named %r with INS file %r in Partition %s ..." %
          (imagename, imageinsfile, partition.name))
    partition.mount_iso_image(image_fp, imagename, imageinsfile)

    partition.pull_full_properties()
    print("Partition property 'boot-iso-image-name' has been set to image name: %r" %
          (partition.get_property('boot-iso-image-name')))

    print("Setting 'iso-image' as a boot device ...")
    partition.update_properties({'boot-device': 'iso-image'})

    print("Starting Partition %s ..." % partition.name)
    try:
        partition.start()
    except zhmcclient.HTTPError as exc:
        print("Error: %s" % exc)
        sys.exit(1)

    partition.pull_full_properties()
    status = partition.get_property('status')
    print("Partition %s status: %s" % (partition.name, status))

finally:

    print("Logging off ...")
    session.logoff()

    if timestats:
        print(session.time_stats_keeper)
