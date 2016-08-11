#!/usr/bin/env python
# Copyright 2016 IBM Corp. All Rights Reserved.
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
Example 7: Using stomp to receive job completion JMS notifications from HMC
"""

import sys
import yaml
import requests.packages.urllib3
import stomp


import zhmcclient
__callback = None

requests.packages.urllib3.disable_warnings()

if len(sys.argv) != 2:
    print("Usage: %s hmccreds.yaml" % sys.argv[0])
    sys.exit(2)
hmccreds_file = sys.argv[1]

with open(hmccreds_file, 'r') as fp:
    hmccreds = yaml.load(fp)

examples = hmccreds.get("examples", None)
if examples is None:
    print("examples not found in credentials file %s" %
          (hmccreds_file))
    sys.exit(1)

example7 = examples.get("example7", None)
if example7 is None:
    print("example7 not found in credentials file %s" %
          (hmccreds_file))
    sys.exit(1)

hmc = example7["hmc"]
cpcname = example7["cpcname"]
partitionname = example7["partitionname"]
amq_port = example7['amq_port']
callback = None
topic = None

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" %
          (hmc, hmccreds_file))
    sys.exit(1)

userid = cred['userid']
password = cred['password']

messages = []


class MyListener():

    def on_connecting(self, host_and_port):
        print ("Attempting to connect to message broker...")

    def on_connected(self, headers, message):
        print ("Connected to broker: %s" % message)

    def on_disconnected(self, headers, message):
        print ("No longer connected to broker: %s" % message)

    def on_error(self, headers, message):
        print('received an error "%s"' % message)

    def on_message(self, headers, message):
        print ('received a message')
        messages.append(headers)

try:
    print("Using HMC %s with userid %s ..." % (hmc, userid))
    session = zhmcclient.Session(hmc, userid, password)
    cl = zhmcclient.Client(session)

    topics = session.get_notfication_topics()

    for entry in topics:
        if entry['topic-type'] == 'job-notification':
            dest = entry['topic-name']
            break
    print("destination: %s" % dest)

    conn = stomp.Connection([(session.host, amq_port)], use_ssl="SSL")
    conn.set_listener('', MyListener())
    conn.start()
    conn.connect(userid, password, wait=True)
    conn.subscribe(destination="/topic/" + dest, id=1, ack='auto')

    cpc = cl.cpcs.find(name=cpcname)
    cpc.pull_full_properties()
    print("Status of CPC %s: %s" %
          (cpc.properties['name'], cpc.properties['status']))
    partition = cpc.partitions.find(name=partitionname)
    print("Status of Partition %s: %s" %
          (partition.properties['name'], partition.properties['status']))
    print("Stopping partition %s ..." % partition.properties['name'])
    status = partition.stop(wait_for_completion=False)
    while True:
        if messages != []:
            print ("received messages are ", messages)
            break
    print ("Done printing the messages...")
    conn.disconnect()

except zhmcclient.Error as exc:
    print("%s: %s" % (exc.__class__.__name__, exc))
    sys.exit(1)
