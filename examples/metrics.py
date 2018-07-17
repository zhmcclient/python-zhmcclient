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
Example: Create a metrics context, retrieve metrics and delete metrics context.
"""

import sys
import yaml
import time
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
    print("examples not found in credentials file %s" % hmccreds_file)
    sys.exit(1)

example = examples.get("metrics", None)
if example is None:
    print("metrics section not found in credentials file %s" % hmccreds_file)
    sys.exit(1)


hmc = example["hmc"]

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" %
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

    metric_groups = [

        'cpc-usage-overview',  # Only in classic mode
        'logical-partition-usage',  # Only in classic mode
        'channel-usage',  # Only in classic mode

        'dpm-system-usage-overview',  # Only in DPM mode
        'partition-usage',  # Only in DPM mode
        'adapter-usage',  # Only in DPM mode
        'crypto-usage',  # Only in DPM mode
        'flash-memory-usage',  # Only in DPM mode
        'roce-usage',  # Only in DPM mode

        'virtualization-host-cpu-memory-usage',  # Only in ensemble mode

    ]

    print("Creating Metrics Context ...")
    mc = cl.metrics_contexts.create(
        {'anticipated-frequency-seconds': 15,
         'metric-groups': metric_groups})

    sleep_time = 15  # seconds

    print("Sleeping for %s seconds ..." % sleep_time)
    time.sleep(sleep_time)

    print("Retrieving the current metric values ...")
    mr_str = mc.get_metrics()

    print("Current metric values:")
    mr = zhmcclient.MetricsResponse(mc, mr_str)
    for mg in mr.metric_group_values:
        mg_name = mg.name
        mg_def = mc.metric_group_definitions[mg_name]
        print("  Metric group: {}".format(mg_name))
        for ov in mg.object_values:
            print("    Resource: {}".format(ov.resource_uri))
            print("    Timestamp: {}".format(ov.timestamp))
            print("    Metric values:")
            for m_name in ov.metrics:
                m_value = ov.metrics[m_name]
                m_def = mg_def.metric_definitions[m_name]
                m_unit = m_def.unit
                m_type = m_def.type
                print("      {:30}  {} {}".
                      format(m_name, m_value, m_unit.encode('utf-8')))
        if not mg.object_values:
            print("    No resources")

    print("Deleting Metrics Context ...")
    mc.delete()

    print("Logging off ...")
    session.logoff()

    if timestats:
        print(session.time_stats_keeper)

    print("Done.")

except zhmcclient.Error as exc:
    print("%s: %s" % (exc.__class__.__name__, exc))
    sys.exit(1)
