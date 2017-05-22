#!/usr/bin/env python
# Copyright 2017 IBM Corp. All Rights Reserved.
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
Example that shows the OS messages of the OS in a Partition or LPAR.
"""

import sys
import logging
import yaml
import requests.packages.urllib3

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

show_os_messages = examples.get("show_os_messages", None)
if show_os_messages is None:
    print("show_os_messages not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = show_os_messages.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logmodule = show_os_messages.get("logmodule", None)
    if logmodule is None:
        logmodule = ''  # root logger
    print("Logging for module %s with level %s" % (logmodule, loglevel))
    handler = logging.StreamHandler()
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(format_string))
    logger = logging.getLogger(logmodule)
    logger.addHandler(handler)
    logger.setLevel(level)

hmc = show_os_messages["hmc"]
cpcname = show_os_messages["cpcname"]
partname = show_os_messages["partname"]

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" % \
          (hmc, hmccreds_file))
    sys.exit(1)

userid = cred['userid']
password = cred['password']

print(__doc__)

print("Using HMC %s with userid %s ..." % (hmc, userid))
session = zhmcclient.Session(hmc, userid, password)
cl = zhmcclient.Client(session)

timestats = show_os_messages.get("timestats", False)
if timestats:
    session.time_stats_keeper.enable()

try:
    cpc = cl.cpcs.find(name=cpcname)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (cpcname, hmc))
    sys.exit(1)

try:
    if cpc.dpm_enabled:
        partkind = "partition"
        partition = cpc.partitions.find(name=partname)
    else:
        partkind = "LPAR"
        partition = cpc.lpars.find(name=partname)
except zhmcclient.NotFound:
    print("Could not find %s %s on CPC %s" % (partkind, partname, cpcname))
    sys.exit(1)

print("Opening OS message channel for %s %s on CPC %s ..." %
      (partkind, partname, cpcname))
topic = partition.open_os_message_channel(include_refresh_messages=True)
print("OS message channel topic: %s" % topic)

receiver = zhmcclient.NotificationReceiver(topic, hmc, userid, password)
print("Showing OS messages (including refresh messages) ...")

try:
    for headers, message in receiver.notifications():
        print("# HMC notification #%s:" % headers['session-sequence-nr'])
        os_msg_list = message['os-messages']
        for os_msg in os_msg_list:
            msg_id = os_msg['message-id']
            held = os_msg['is-held']
            priority = os_msg['is-priority']
            prompt = os_msg.get('prompt-text', None)
            print("# OS message %s (held: %s, priority: %s, prompt: %r):" %
                  (msg_id, held, priority, prompt))
            msg_txt = os_msg['message-text'].strip('\n')
            print(msg_txt)
except KeyboardInterrupt:
    print("Keyboard interrupt: Closing OS message channel...")
    receiver.close()

print("Logging off...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
