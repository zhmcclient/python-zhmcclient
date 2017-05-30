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
Example demonstrates JMS notifications for completion of async operation
"""

import sys
from time import sleep
import threading
from pprint import pprint
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

jms_notifications = examples.get("jms_notifications", None)
if jms_notifications is None:
    print("jms_notifications not found in credentials file %s" %
          (hmccreds_file))
    sys.exit(1)

hmc = jms_notifications["hmc"]
cpcname = jms_notifications["cpcname"]
partname = jms_notifications["partname"]
amqport = jms_notifications['amqport']
callback = None
topic = None

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" %
          (hmc, hmccreds_file))
    sys.exit(1)

userid = cred['userid']
password = cred['password']

# Thread-safe handover of notifications between listener and main threads
NOTI_DATA = None
NOTI_LOCK = threading.Condition()

class MyListener(object):

    def on_connecting(self, host_and_port):
        print("Listener: Attempting to connect to message broker")
        sys.stdout.flush()

    def on_connected(self, headers, message):
        print("Listener: Connected to broker")
        sys.stdout.flush()

    def on_disconnected(self):
        print("Listener: Disconnected from broker")
        sys.stdout.flush()

    def on_error(self, headers, message):
        print('Listener: Received an error: %s' % message)
        sys.stdout.flush()

    def on_message(self, headers, message):
        global NOTI_DATA, NOTI_LOCK
        print('Listener: Received a notification')
        sys.stdout.flush()
        with NOTI_LOCK:
            # Wait until main program has processed the previous notification
            while NOTI_DATA:
                NOTI_LOCK.wait()
            # Indicate to main program that there is a new notification
            NOTI_DATA = headers
            NOTI_LOCK.notifyAll()

print(__doc__)

print("Using HMC %s with userid %s ..." % (hmc, userid))
session = zhmcclient.Session(hmc, userid, password)
cl = zhmcclient.Client(session)

print("Retrieving notification topics ...")
topics = session.get_notification_topics()

for topic in topics:
    if topic['topic-type'] == 'job-notification':
        job_topic_name = topic['topic-name']
        break

conn = stomp.Connection([(session.host, amqport)], use_ssl="SSL")
conn.set_listener('', MyListener())
conn.start()
conn.connect(userid, password, wait=True)

sub_id = 42  # subscription ID

print("Subscribing for job notifications using topic: %s" % job_topic_name)
conn.subscribe(destination="/topic/"+job_topic_name, id=sub_id, ack='auto')

print("Finding CPC by name=%s ..." % cpcname)
try:
    cpc = cl.cpcs.find(name=cpcname)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (cpcname, hmc))
    sys.exit(1)

print("Finding partition by name=%s ..." % partname)
try:
    partition = cpc.partitions.find(name=partname)
except zhmcclient.NotFound:
    print("Could not find partition %s in CPC %s" % (partname, cpc.name))
    sys.exit(1)

print("Accessing status of partition %s ..." % partition.name)
partition_status = partition.get_property('status')
print("Status of partition %s: %s" % (partition.name, partition_status))

if partition_status == 'active':
    print("Stopping partition %s asynchronously ..." % partition.name)
    job = partition.stop(wait_for_completion=False)
elif partition_status in ('inactive', 'stopped'):
    print("Starting partition %s asynchronously ..." % partition.name)
    job = partition.start(wait_for_completion=False)
else:
    raise zhmcclient.Error("Cannot deal with partition status: %s" % \
                           partition_status)
print("Waiting for completion of job %s ..." % job.uri)
sys.stdout.flush()

# Just for demo purposes, we show how a loop for processing multiple
# notifications would look like.
while True:
    with NOTI_LOCK:

        # Wait until listener has a new notification
        while not NOTI_DATA:
            NOTI_LOCK.wait()

        # Process the notification
        print("Received notification:")
        pprint(NOTI_DATA)
        sys.stdout.flush()

        # This test is just for demo purposes, it should always be our job
        # given what we subscribed for.
        if NOTI_DATA['job-uri'] == job.uri:
            break
        else:
            print("Unexpected completion received for job %s" % \
                  NOTI_DATA['job-uri'])
            sys.stdout.flush()

        # Indicate to listener that we are ready for next notification
        NOTI_DATA = None
        NOTI_LOCK.notifyAll()

print("Job has completed: %s" % job.uri)
sys.stdout.flush()

conn.disconnect()
sleep(1)  # Allow listener to print disconnect message (just for demo)

print("Done.")
