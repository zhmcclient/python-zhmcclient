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
Example that performs an asynchronous start of a partition and waits for a job
completion notification.
"""

import sys
import uuid
import requests.packages.urllib3
import stomp
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

# HMC port for JMS notifications
JMS_PORT = 61612

# Notification topic type for jobs
JOB_TOPIC_TYPE = 'job-notification'

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

    print("Finding job completion notification topic ...")
    job_topic_name = None
    topics = session.get_notification_topics()
    for topic in topics:
        if topic['topic-type'] == JOB_TOPIC_TYPE:
            job_topic_name = topic['topic-name']
            break
    print(f"Using job completion notification topic: {job_topic_name}")

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

        print("Creating a notification receiver for topic "
              f"{job_topic_name} ...")
        try:
            receiver = zhmcclient.NotificationReceiver(
                job_topic_name, host, userid, password)
        except Exception as exc:
            print(f"Error: Cannot create notification receiver: {exc}")
            sys.exit(1)

        print("Waiting for job completion notifications ...")
        while True:
            try:
                for headers, _ in receiver.notifications():
                    # message is None for job completion notifications
                    if headers['job-uri'] == job.uri:
                        print("Received completion notification for the start job")
                        break
                    else:
                        print("Received completion notification for another job: "
                              f"{headers['job-uri']} - continue to wait")
            except zhmcclient.NotificationError as exc:
                print(f"Notification Error: {exc} - reconnecting")
                continue
            except stomp.exception.StompException as exc:
                print(f"STOMP Error: {exc} - reconnecting")
                continue
            except KeyboardInterrupt:
                print("Keyboard interrupt - leaving receiver loop")
                receiver.close()
                break
            else:
                raise AssertionError("Receiver was closed - should not happen")

        print("Job completed; Getting job status and result ...")
        try:
            job_status, op_result = job.check_for_completion()
        except zhmcclient.Error as exc:
            print("Error: Start operation failed with "
                  f"{exc.__class__.__name__}: {exc}")
            sys.exit(1)
        assert job_status == 'complete'
        print("Start operation succeeded")

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
                  f"{cpc.name} for clean up - "
                  f"Please delete it manually: {exc.__class__.__name_}: {exc}")
            sys.exit(1)

finally:
    print("Logging off ...")
    session.logoff()
