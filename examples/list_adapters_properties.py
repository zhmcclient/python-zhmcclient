#!/usr/bin/env python
# Copyright 2026 IBM Corp. All Rights Reserved.
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
Example that lists adapters with additional properties.
"""

import sys
import logging

import urllib3

import zhmcclient
from zhmcclient.testutils import hmc_definitions, setup_hmc_session


# Flag to control logging of the HTTP interactions with the HMC to stderr.
ENABLE_LOGGING = False


def main():
    "Main function of the script"

    urllib3.disable_warnings()

    if ENABLE_LOGGING:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

    print(__doc__)

    if len(sys.argv) not in (2, 3):
        print(f"Usage: {sys.argv[0]} CPC [PROPS]")
        print("Where:")
        print("  CPC        Name of the CPC")
        print("  PROPS      Optional: Comma-saparated list of additional "
              "property names")
        return 2

    cpc_name = sys.argv[1]
    try:
        additional_properties = sys.argv[2].split(",")
    except IndexError:
        additional_properties = []

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

        cpc = client.cpcs.find(name=cpc_name)
        print(f"Using CPC {cpc.name}")

        print("\nListing adapters with additional_properties="
              f"{additional_properties} ...")
        adapters = cpc.adapters.list(
            additional_properties=additional_properties)
        print("Resulting adapters (sorted):")
        for ad in sorted(adapters, key=lambda p: p.name):
            print(f"  {dict(ad.properties)}")

        return 0

    finally:
        print("Logging off ...")
        session.logoff()


if __name__ == '__main__':
    sys.exit(main())
