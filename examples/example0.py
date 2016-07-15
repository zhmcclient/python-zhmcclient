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

#
# Example for showing the API version of an HMC.
#

import sys
import yaml
import requests.packages.urllib3

import zhmcclient

HMC = "9.152.150.65"         # HMC to use

requests.packages.urllib3.disable_warnings()

if len(sys.argv) != 1:
    print("Usage: %s" % sys.argv[0])
    sys.exit(2)

print("Using HMC %s without any userid ..." % HMC)
session = zhmcclient.Session(HMC)
cl = zhmcclient.Client(session)

vi = cl.version_info()
print("HMC API version: {}.{}".format(vi[0], vi[1]))

