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
Example that retrieves certain resource classes from the inventory.
"""

import sys
import urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions, setup_hmc_session


def main():
    "Main function of the script"

    urllib3.disable_warnings()

    print(__doc__)

    # Get HMC info from HMC inventory and vault files
    hmc_def = hmc_definitions()[0]
    host = hmc_def.host
    print(f"Creating a session with the HMC at {host} ...")
    try:
        session = setup_hmc_session(hmc_def)
    except zhmcclient.Error as exc:
        print(f"Error: Cannot establish session with HMC {host}: "
              f"{exc.__class__.__name__}: {exc}")
        return 1

    try:
        client = zhmcclient.Client(session)

        resource_classes = ['cpc', 'partition', 'adapter']
        rc_str = ', '.join(resource_classes)
        print(f"Retrieving inventory for resource classes: {rc_str} ...")
        resources = client.get_inventory(resource_classes)

        print("Returned resources with a subset of properties in the returned "
              "order:")
        format_str = "{:<24s} {:<24s} {}"
        print(format_str.format("Class", "Name", "URI"))
        for res in resources:
            name = res.get('name', '<no name>')
            uri = res.get('object-uri') or res.get('element-uri')
            line = format_str.format(res['class'], name, uri)
            print(line)

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
