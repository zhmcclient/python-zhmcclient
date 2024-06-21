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
Example that creates a metrics context, retrieves metrics and deletes the
metrics context.
"""

import sys
import time
import requests.packages.urllib3

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

    try:
        metric_groups = [

            # Please edit this section so it contains only the metric groups
            # that mnatch the operational mode of the targeted CPC.

            'cpc-usage-overview',  # Only in classic mode
            'logical-partition-usage',  # Only in classic mode
            'channel-usage',  # Only in classic mode

            'dpm-system-usage-overview',  # Only in DPM mode
            'partition-usage',  # Only in DPM mode
            'adapter-usage',  # Only in DPM mode
            'crypto-usage',  # Only in DPM mode
            'flash-memory-usage',  # Only in DPM mode
            'roce-usage',  # Only in DPM mode

            # 'environmental-power-status',  # In any mode, starting with z15

            # 'virtualization-host-cpu-memory-usage',  # Only in ensemble mode

        ]

        print("Creating Metrics Context ...")
        mc = client.metrics_contexts.create(
            {'anticipated-frequency-seconds': 15,
             'metric-groups': metric_groups})

        sleep_time = 15  # seconds

        print(f"Sleeping for {sleep_time} seconds ...")
        time.sleep(sleep_time)

        print("Retrieving the current metric values ...")
        mr_str = mc.get_metrics()

        print("Current metric values:")
        mr = zhmcclient.MetricsResponse(mc, mr_str)
        for mg in mr.metric_group_values:
            mg_name = mg.name
            mg_def = mc.metric_group_definitions[mg_name]
            print(f"  Metric group: {mg_name}")
            for ov in mg.object_values:
                print(f"    Resource: {ov.resource_uri}")
                print(f"    Timestamp: {ov.timestamp}")
                print("    Metric values:")
                for m_name in ov.metrics:
                    m_value = ov.metrics[m_name]
                    m_def = mg_def.metric_definitions[m_name]
                    m_unit = m_def.unit or ''
                    print(f"      {m_name:30}  {m_value} {m_unit}")
            if not mg.object_values:
                print("    No resources")

        print("Deleting Metrics Context ...")
        mc.delete()

    except zhmcclient.Error as exc:
        print(f"{exc.__class__.__name__}: {exc}")
        sys.exit(1)

finally:
    print("Logging off ...")
    session.logoff()
