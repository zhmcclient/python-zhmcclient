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
Example that performs an asynchronous start of a partition and polls for job
completion.
"""

import sys
import uuid
import requests.packages.urllib3
import time

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
        print(f"Error: Cannot create partition {part_name} on CPC {cpc.name}: "
              f"{exc.__class__.__name__}: {exc}")
        sys.exit(1)

    try:
        print(f"Starting partition {part.name} asynchronously ...")
        job = part.start(wait_for_completion=False)

        sleep_time = 1
        print(f"Polling for job completion with sleep time {sleep_time} sec ...")
        while True:
            try:
                job_status, op_result = job.check_for_completion()
            except zhmcclient.Error as exc:
                print("Error: Job completed; Start operation failed with "
                      f"{exc.__class__.__name__}: {exc}")
                break
            print(f"Job status: {job_status}")
            if job_status == 'complete':
                break
            time.sleep(sleep_time)
        print("Job completed; Start operation succeeded")

    finally:
        if part.get_property('status') != 'stopped':
            print(f"Stopping partition {part.name} ...")
            try:
                part.stop(wait_for_completion=True)
            except zhmcclient.Error as exc:
                print("Error: Stop operation failed with "
                      f"{exc.__class__.__name__}: {exc}")
                sys.exit(1)

        print(f"Deleting partition {part.name} ...")
        try:
            part.delete()
        except zhmcclient.Error as exc:
            print(f"Error: Cannot delete partition {part.name} on CPC "
                  "{cpc.name} for clean up - "
                  f"Please delete it manually: {exc.__class__.__name__}: {exc}")
            sys.exit(1)

finally:
    print("Logging off ...")
    session.logoff()
