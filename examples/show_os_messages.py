#!/usr/bin/env python
# Copyright 2017-2022 IBM Corp. All Rights Reserved.
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

import zhmcclient
from zhmcclient.testutils import hmc_definitions

requests.packages.urllib3.disable_warnings()

# Get HMC info from HMC definition file
hmc_def = hmc_definitions()[0]
nick = hmc_def.nickname
host = hmc_def.hmc_host
userid = hmc_def.hmc_userid
password = hmc_def.hmc_password
verify_cert = hmc_def.hmc_verify_cert

# Print metadata for each OS message, before each message
PRINT_METADATA = False

print(__doc__)

print("Using HMC {} at {} with userid {} ...".format(nick, host, userid))

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
    print("Using CPC {}".format(cpc.name))

    print("Finding an active partition on CPC {} ...".format(cpc.name))
    parts = cpc.partitions.list(filter_args={'status': 'active'})
    if not parts:
        print("Error: CPC {} does not have any active partitions".
              format(cpc.name))
        sys.exit(1)
    part = parts[0]
    print("Using partition {} with status {}".
          format(part.name, part.get_property('status')))

    print("Opening OS message channel for partition {} on CPC {} (including "
          "refresh messages) ...".
          format(part.name, cpc.name))
    try:
        msg_topic = part.open_os_message_channel(include_refresh_messages=True)
    except zhmcclient.Error as exc:
        print("Error: Cannot open OS message channel for partition {}: {}: {}".
              format(part.name, exc.__class__.__name__, exc))
        sys.exit(1)
    print("OS message channel notification topic: {}".format(msg_topic))

    print("Creating a notification receiver for topic {} ...".
          format(msg_topic))
    try:
        receiver = zhmcclient.NotificationReceiver(
            msg_topic, host, userid, password)
    except Exception as exc:
        print("Error: Cannot create notification receiver: {}".format(exc))
        sys.exit(1)

    print("Showing OS messages ...")
    print("-----------------------")
    try:
        for headers, message in receiver.notifications():
            os_msg_list = message['os-messages']
            for os_msg in os_msg_list:
                if PRINT_METADATA:
                    msg_id = os_msg['message-id']
                    held = os_msg['is-held']
                    priority = os_msg['is-priority']
                    prompt = os_msg.get('prompt-text', None)
                    print("# OS message {} (held: {}, priority: {}, "
                          "prompt: {}):".
                          format(msg_id, held, priority, prompt))
                msg_txt = os_msg['message-text'].strip('\n')
                print(msg_txt)
    except KeyboardInterrupt:
        print("Keyboard interrupt - leaving receiver loop")
    finally:
        print("Closing receiver ...")
        receiver.close()

finally:
    print("Logging off ...")
    session.logoff()
