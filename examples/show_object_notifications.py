#!/usr/bin/env python
# Copyright 2021 IBM Corp. All Rights Reserved.
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
Example that shows the object notification messages.
"""

import sys
import logging
import yaml
import requests.packages.urllib3

import zhmcclient

# Print metadata for each OS message, before each message
PRINT_METADATA = False

requests.packages.urllib3.disable_warnings()

if len(sys.argv) != 2:
    print("Usage: %s hmccreds.yaml" % sys.argv[0])
    sys.exit(2)
hmccreds_file = sys.argv[1]

with open(hmccreds_file, 'r') as fp:
    hmccreds = yaml.safe_load(fp)

examples = hmccreds.get("examples", None)
if examples is None:
    print("examples not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

show_object_notifications = examples.get("show_object_notifications", None)
if show_object_notifications is None:
    print("show_object_notifications not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = show_object_notifications.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logmodule = show_object_notifications.get("logmodule", None)
    if logmodule is None:
        logmodule = ''  # root logger
    print("Logging for module %s with level %s" % (logmodule, loglevel))
    handler = logging.StreamHandler()
    format_string = '%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(format_string))
    logger = logging.getLogger(logmodule)
    logger.addHandler(handler)
    logger.setLevel(level)

hmc = show_object_notifications["hmc"]
cpcname = show_object_notifications["cpcname"]
partname = show_object_notifications["partname"]

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" % \
          (hmc, hmccreds_file))
    sys.exit(1)

userid = cred['userid']
password = cred['password']

print(__doc__)

print("Using HMC %s with userid %s ..." % (hmc, userid))
session = zhmcclient.Session(hmc, userid, password, verify_cert=False)
cl = zhmcclient.Client(session)

timestats = show_object_notifications.get("timestats", False)
if timestats:
    session.time_stats_keeper.enable()

session.logon()
topic = session.object_topic
if topic is None:
    print("Error: Object notification topic is not set")
    sys.exit(1)

print("Object notification topic: %s" % topic)

receiver = zhmcclient.NotificationReceiver(topic, hmc, userid, password)
print("Showing object notifications ...")
sys.stdout.flush()

try:
    for headers, message in receiver.notifications():
        try:
            uri = headers['object-uri']
        except KeyError:
            uri = headers['element-uri']
        print("Object notification: type={}, uri={}, class={}, name={}".
              format(headers['notification-type'], uri, headers['class'],
                     headers['name']))
        if headers['notification-type'] == 'property-change':
            for prop_change in message['change-reports']:
                print("  Property change: name: {}, new value: {}".
                      format(prop_change['property-name'],
                             prop_change['new-value']))
except KeyboardInterrupt:
    print("Keyboard interrupt - leaving receiver loop")
    sys.stdout.flush()
finally:
    print("Closing receiver...")
    sys.stdout.flush()
    receiver.close()

print("Logging off...")
sys.stdout.flush()
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
