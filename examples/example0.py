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
Example 0: Show the API version of an HMC.
"""

import sys
import logging
import yaml
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
    print("examples not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

example0 = examples.get("example0", None)
if example0 is None:
    print("example0 not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = example0.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = example0["hmc"]

print(__doc__)

print("Using HMC %s with an unauthenticated session ..." % hmc)
session = zhmcclient.Session(hmc)
cl = zhmcclient.Client(session)

vi = cl.version_info()
print("HMC API version: {}.{}".format(vi[0], vi[1]))
