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
Example showing the Get Inventory operation.
"""

import sys
import logging
import yaml
import json
import requests.packages.urllib3
from pprint import pprint
import contextlib
from collections import OrderedDict

import zhmcclient


@contextlib.contextmanager
def pprint_for_ordereddict():
    """
    Context manager that causes pprint() to print OrderedDict objects as nicely
    as standard Python dictionary objects.
    """
    od_saved = OrderedDict.__repr__
    try:
        OrderedDict.__repr__ = dict.__repr__
        yield
    finally:
        OrderedDict.__repr__ = od_saved


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

get_inventory = examples.get("get_inventory", None)
if get_inventory is None:
    print("get_inventory not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = get_inventory.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = get_inventory["hmc"]
resources = get_inventory["resources"]

cred = hmccreds.get(hmc, None)
if cred is None:
    print("Credentials for HMC %s not found in credentials file %s" % \
          (hmc, hmccreds_file))
    sys.exit(1)

userid = cred["userid"]
password = cred["password"]

print(__doc__)

print("Using HMC %s with userid %s ..." % (hmc, userid))
session = zhmcclient.Session(hmc, userid, password)
cl = zhmcclient.Client(session)

timestats = get_inventory.get("timestats", False)
if timestats:
    session.time_stats_keeper.enable()

print("Invoking get_inventory() for resources: %r" % resources)
result = cl.get_inventory(resources)

if True:
    print("List of returned resources, with subset of properties:")
    format_str = "%-26.26s %-32.32s %s"
    print(format_str % ("Class", "Name", "URI"))
    for res in result:
        uri = res.get('object-uri') or \
            res.get('element-uri') or \
            '???'
        line = format_str % (res['class'], res.get('name', '???'), uri)
        if 'adapter-family' in res:
            line += " adapter-family=%s" % res['adapter-family']
        print(line)

if False:
    print("Full dump of returned result:")
    with pprint_for_ordereddict():
        pprint(result)

print("Logging off ...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
