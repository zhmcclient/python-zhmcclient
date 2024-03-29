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
import time
import requests.packages.urllib3
from time import sleep
from datetime import datetime, timedelta

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

# Flag to control logging of the HTTP and notification interactions with
# the HMC to stderr.
ENABLE_LOGGING = False

if ENABLE_LOGGING:
    logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

def delta_ms(start_dt, end_dt):
    """Return float that is the time delta in milliseconds"""
    return (end_dt - start_dt) / timedelta(microseconds=1) / 1000

print(__doc__)

print("Using HMC {} at {} with userid {} ...".format(nickname, host, userid))

print("Creating a session with the HMC ...")
try:
    session = zhmcclient.Session(
        host, userid, password, verify_cert=verify_cert)
except zhmcclient.Error as exc:
    print("Error: Cannot establish session with HMC {}: {}: {}".
          format(host, exc.__class__.__name__, exc))
    sys.exit(1)

cleanup_partition = None
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

    part_mgr = cpc.partitions

    print("Listing partitions using list() (not auto-enabled) ...")
    start_dt = datetime.now()
    part_list = part_mgr.list()
    end_dt = datetime.now()
    print("Result of list(): returned {} partitions in {} ms".
          format(len(part_list), delta_ms(start_dt, end_dt)))

    print("Enabling auto-updating for partition manager")
    try:
        part_mgr.enable_auto_update()
    except zhmcclient.Error as exc:
        print("Error: Cannot auto-enable partition manager for CPC {}: {}: {}".
              format(cpc.name, exc.__class__.__name__, exc))
        sys.exit(1)

    print("Listing partitions using list() "
          "(auto-enabled - uses from local list) ...")
    start_dt = datetime.now()
    part_list = part_mgr.list()
    end_dt = datetime.now()
    print("Result of list(): returned {} partitions in {} ms".
          format(len(part_list), delta_ms(start_dt, end_dt)))

    part_name = "zhmc_test_{}".format(uuid.uuid4())
    print("Creating partition {} ...".format(part_name))
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
        print("Error: Cannot create partition {} on CPC {}: {}: {}".
              format(part_name, cpc.name, exc.__class__.__name__, exc))
        sys.exit(1)
    print("Partition uri: {}".format(part.uri))

    print("Listing partitions using list() "
          "(auto-enabled - added partition causes pull from HMC) ...")
    start_dt = datetime.now()
    part_list = part_mgr.list()
    end_dt = datetime.now()
    print("Result of list(): returned {} partitions in {} ms".
          format(len(part_list), delta_ms(start_dt, end_dt)))

    print("Listing partitions using list() "
          "(auto-enabled - uses from local list) ...")
    start_dt = datetime.now()
    part_list = part_mgr.list()
    end_dt = datetime.now()
    print("Result of list(): returned {} partitions in {} ms".
          format(len(part_list), delta_ms(start_dt, end_dt)))

    print("Deleting partition {} (uri: {}) ...".format(part.name, part.uri))
    try:
        part.delete()
        cleanup_partition = None
    except zhmcclient.Error as exc:
        print("Error: Cannot delete partition {} on CPC {} for clean up - "
              "Please delete it manually: {}: {}".
              format(part.name, cpc.name, exc.__class__.__name__, exc))
        sys.exit(1)

    print("Listing partitions using list() "
          "(auto-enabled - uses from local list) ...")
    start_dt = datetime.now()
    part_list = part_mgr.list()
    end_dt = datetime.now()
    print("Result of list(): returned {} partitions in {} ms".
          format(len(part_list), delta_ms(start_dt, end_dt)))

    print("Disabling auto-updating for partition manager")
    part_mgr.disable_auto_update()

    print("Listing partitions using list() (not auto-enabled) ...")
    start_dt = datetime.now()
    part_list = part_mgr.list()
    end_dt = datetime.now()
    print("Result of list(): returned {} partitions in {} ms".
          format(len(part_list), delta_ms(start_dt, end_dt)))

finally:
    if cleanup_partition:
        print("Cleanup: Deleting partition {} ...".format(cleanup_partition.name))
        try:
            cleanup_partition.delete()
        except zhmcclient.Error as exc:
            print("Error: Cannot delete partition {} on CPC {} for clean up - "
                  "Please delete it manually: {}: {}".
                  format(part.name, cpc.name, exc.__class__.__name__, exc))
    print("Logging off ...")
    session.logoff()
