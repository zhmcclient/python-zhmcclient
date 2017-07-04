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
Example showing the free crypto domains of a set of crypto adapters in a CPC.
"""

import sys
import logging
import yaml
import json
import requests.packages.urllib3
import operator
import itertools

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

list_free_crypto_domains = examples.get("list_free_crypto_domains", None)
if list_free_crypto_domains is None:
    print("list_free_crypto_domains not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = list_free_crypto_domains.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = list_free_crypto_domains["hmc"]
cpcname = list_free_crypto_domains["cpcname"]
crypto_adapter_names = list_free_crypto_domains["crypto_adapter_names"]

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

timestats = list_free_crypto_domains.get("timestats", False)
if timestats:
    session.time_stats_keeper.enable()

cpc = cl.cpcs.find(name=cpcname)

if crypto_adapter_names:
    crypto_adapters = [cpc.adapters.find(name=ca_name)
                       for ca_name in crypto_adapter_names]
else:
    crypto_adapters = cpc.adapters.findall(type='crypto')
    crypto_adapter_names = [ca.name for ca in crypto_adapters]

print("Determining crypto configurations of all partitions on CPC %r ..." %
      cpc.name)
for partition in cpc.partitions.list(full_properties=True):
    crypto_config = partition.get_property('crypto-configuration')
    if crypto_config:
        print("Partition %r has crypto configuration:" % partition.name)
        print(json.dumps(crypto_config, indent=4))

print("Determining free crypto domains on all of the crypto adapters %r on "
      "CPC %r ..." % (crypto_adapter_names, cpc.name))
free_domains = cpc.get_free_crypto_domains(crypto_adapters)

# Convert this list of numbers into better readable number ranges:
ranges = []
for k, g in itertools.groupby(enumerate(free_domains), lambda (i, x): i - x):
    group = map(operator.itemgetter(1), g)
    if group[0] == group[-1]:
        ranges.append("{}".format(group[0]))
    else:
        ranges.append("{}-{}".format(group[0], group[-1]))
free_domains_str = ', '.join(ranges)

print("Free domains: %s" % free_domains_str)

print("Logging off ...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
