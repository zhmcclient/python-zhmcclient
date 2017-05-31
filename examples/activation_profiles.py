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
Example shows Activation Profiles handling.
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

activation_profiles = examples.get("activation_profiles", None)
if activation_profiles is None:
    print("activation_profiles not found in credentials file %s" % \
          (hmccreds_file))
    sys.exit(1)

loglevel = activation_profiles.get("loglevel", None)
if loglevel is not None:
    level = getattr(logging, loglevel.upper(), None)
    if level is None:
        print("Invalid value for loglevel in credentials file %s: %s" % \
              (hmccreds_file, loglevel))
        sys.exit(1)
    logging.basicConfig(level=level)

hmc = activation_profiles["hmc"]
cpcname = activation_profiles["cpcname"]
lparname = activation_profiles["lparname"]

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

timestats = activation_profiles.get("timestats", False)
if timestats:
    session.time_stats_keeper.enable()

print("Listing CPCs ...")
cpcs = cl.cpcs.list()
for cpc in cpcs:
    print(cpc.name, cpc.get_property('status'), cpc.uri)

print("Finding CPC by name=%s ..." % cpcname)
try:
    cpc = cl.cpcs.find(name=cpcname)
except zhmcclient.NotFound:
    print("Could not find CPC %s on HMC %s" % (cpcname, hmc))
    sys.exit(1)

print("Checking if DPM is enabled on CPC %s..." % cpcname)
if cpc.dpm_enabled:
    print("CPC %s is in DPM mode." % cpcname)
    sys.exit(1)

managers = {'reset': 'reset_activation_profiles',
           'image' : 'image_activation_profiles',
           'load' : 'load_activation_profiles'}

for profile_type, manager in managers.items():
    profiles = getattr(cpc, manager).list()

    print("Listing %d %s Activation Profiles ..."
            % (len(profiles), profile_type.capitalize()))

    for profile in profiles:
        print(profile.name, profile.get_property('element-uri'))

    if profile_type == 'image':

        print("Finding %s Activation Profile by name=%s ..."
            % (profile_type.capitalize(), lparname))
        profile = getattr(cpc, manager).find(name=lparname)

        print("Printing info properties:")
        print(profile.properties)

#                print("Printing full properties:")
#                profile.pull_full_properties()
#                print(profile.properties)
        original_description = profile.get_property('description')
        print("description: %s" % original_description)
        updated_properties = dict()
        updated_properties["description"] = "Test Test Test"
        profile.update_properties(updated_properties)
        print("Pull full properties of Image Activation Profile %s ..." % lparname)
        profile.pull_full_properties()
        print("Updated description of Image Activation Profile %s: %s" % (lparname, profile.get_property('description')))
        print("Re-setting description ...")
        original_properties = dict()
        original_properties["description"] = original_description
#                original_properties["description"] = "OpenStack zKVM"
        profile.update_properties(original_properties)
        profile.pull_full_properties()
        print("Updated description of Image Activation Profile %s: %s" % (lparname, profile.get_property('description')))

print("Logging off ...")
session.logoff()

if timestats:
    print(session.time_stats_keeper)

print("Done.")
