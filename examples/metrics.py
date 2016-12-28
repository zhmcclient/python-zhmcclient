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
Example: Create a metrics context, retrieve metrics and
delete metrics context.
"""

import sys
import logging
import yaml
import requests.packages.urllib3
import time

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

example = examples.get("metrics", None)
if example is None:
    print("metrics section not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)


hmc = example["hmc"]

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" % \
          (hmc, hmccreds_file))
    sys.exit(1)

userid = cred['userid']
password = cred['password']

try:
    print(__doc__)

    print("Using HMC %s with userid %s ..." % (hmc, userid))
    session = zhmcclient.Session(hmc, userid, password)
    cl = zhmcclient.Client(session)

    timestats = example.get("timestats", None)
    if timestats:
        session.time_stats_keeper.enable()

    print("Create Metrics Context ...")
    properties = { "anticipated-frequency-seconds" : 15,
#                   "metric-groups": ["cpc-usage-overview", "logical-partition-usage", "channel-usage"] }
#                   "metric-groups": ["cpc-usage-overview"] }
#                   "metric-groups": [ "channel-usage"] }
#                   "metric-groups": ["dpm-system-usage-overview", "partition-usage", "adapter-usage"] }
#                   "metric-groups": ["dpm-system-usage-overview"] }
                   "metric-groups": ["partition-usage"] }
#                   "metric-groups": ["logical-partition-usage"] }
#                   "metric-groups": [ "adapter-usage"] }
    mc = cl.metrics_contexts.create(properties)
    print(mc.uri)
#    print(mc.properties)

    print("Metrics Context List:")
    print(cl.metrics_contexts.list())

    time.sleep(30)
    print("Get Metrics:")
    metrics_values = mc.get_metrics()
    cv = zhmcclient.CollectedMetrics(mc, metrics_values)

    for metric in cv.metrics:
        print(metric.properties)
        print(metric.managed_object)
    print("Delete Metrics Context.")

    mc.delete()

    print("Logging off ...")
    session.logoff()

    if timestats:
        print(session.time_stats_keeper)

    print("Done.")

except zhmcclient.Error as exc:
    print("%s: %s" % (exc.__class__.__name__, exc))
    sys.exit(1)
