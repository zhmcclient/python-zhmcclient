#!/usr/bin/env python
# Copyright 2017,2022 IBM Corp. All Rights Reserved.
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
Example that shows the OS messages of the OS in a started partition on a CPC
in DPM mode.
"""

import sys
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

# Print metadata for each OS message, before each message
PRINT_METADATA = False

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

    print(f"Finding an active partition on CPC {cpc.name} ...")
    parts = cpc.partitions.list(filter_args={'status': 'active'})
    if not parts:
        print(f"Error: CPC {cpc.name} does not have any active partitions")
        sys.exit(1)
    part = parts[0]
    print(f"Using partition {part.name} with status "
          f"{part.get_property('status')}")

    print(f"Opening OS message channel for partition {part.name} on CPC "
          f"{cpc.name} (including refresh messages) ...")
    try:
        msg_topic = part.open_os_message_channel(include_refresh_messages=True)
    except zhmcclient.Error as exc:
        print("Error: Cannot open OS message channel for partition "
              f"{part.name}: {exc.__class__.__name__}: {exc}")
        sys.exit(1)
    print(f"OS message channel notification topic: {msg_topic}")

    print(f"Creating a notification receiver for topic {msg_topic} ...")
    try:
        receiver = zhmcclient.NotificationReceiver(
            msg_topic, host, userid, password)
    except Exception as exc:
        print(f"Error: Cannot create notification receiver: {exc}")
        sys.exit(1)

    print(f"Debug: STOMP retry/timeout config: {receiver._rt_config}")

    print("Showing OS messages ...")
    print("-----------------------")
    while True:
        try:
            for headers, message in receiver.notifications():
                os_msg_list = message['os-messages']
                for os_msg in os_msg_list:
                    if PRINT_METADATA:
                        msg_id = os_msg['message-id']
                        held = os_msg['is-held']
                        priority = os_msg['is-priority']
                        prompt = os_msg.get('prompt-text', None)
                        print(f"# OS message {msg_id} (held: {held}, "
                              f"priority: {priority}, prompt: {prompt}):")
                    msg_txt = os_msg['message-text'].strip('\n')
                    print(msg_txt)
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

finally:
    print("Logging off ...")
    session.logoff()
