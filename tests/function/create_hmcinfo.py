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
Script that creates an "HMC info file" in JSON format from information
retrieved from an HMC.
"""

from __future__ import absolute_import, print_function

import sys
import os
import argparse
from getpass import getpass
from platform import python_version
import requests.packages.urllib3

import zhmcclient
from _hmcinfo import HMCInfo


def parse_args():
    """
    Parse command line arguments and return the parsed args.

    In case of argument errors, print an error message and exit.
    """

    prog = os.path.basename(sys.argv[0])
    version = zhmcclient.__version__
    usage = '%(prog)s [options] hmc [cpcname ...]'
    desc = __doc__
    epilog = """
Example:
  %s -u hmcuser -o hmcinfo.json 9.10.11.12
""" % prog

    argparser = argparse.ArgumentParser(
        prog=prog, usage=usage, description=desc, epilog=epilog,
        add_help=False)

    pos_arggroup = argparser.add_argument_group(
        'Positional arguments')
    pos_arggroup.add_argument(
        'hmc', metavar='hmc',
        help='IP address or hostname of the HMC.')
    pos_arggroup.add_argument(
        'cpcnames', metavar='cpcname', nargs='*',
        help='Name of a CPC to limit the extraction to. Can be repeated. '
             'Default: Extract all CPCs managed by the HMC.')

    general_arggroup = argparser.add_argument_group(
        'Options')
    general_arggroup.add_argument(
        '-o', '--outfile', dest='hmcinfo_file', metavar='hmcinfofile',
        help='Required: File path of HMC info file being created.')
    general_arggroup.add_argument(
        '-u', '--user', dest='user', metavar='user',
        help='Required: User name for authenticating with the HMC.')
    general_arggroup.add_argument(
        '-p', '--password', dest='password', metavar='password',
        help='Password for authenticating with the HMC.\n'
             'Default: Prompt for a password.')
    general_arggroup.add_argument(
        '-t', '--timestats', dest='timestats', action='store_true',
        help='Display time statistics for the HMC operations that were used.')
    version_str = '%s/zhmcclient %s, Python %s' %\
        (prog, version, python_version())
    general_arggroup.add_argument(
        '--version', action='version', version=version_str,
        help='Show the versions of this program etc. and exit')
    general_arggroup.add_argument(
        '-h', '--help', action='help',
        help='Show this help message and exit')

    args = argparser.parse_args()

    if not args.hmc:
        argparser.error('No HMC specified')

    if not args.hmcinfo_file:
        argparser.error('No HMC info file specified (-o/--outfile option)')

    if not args.user:
        argparser.error('No HMC user specified (-u/--user option)')

    if not args.password:
        args.password = getpass('Enter password for %s: ' % args.user)

    return args


def main():

    args = parse_args()

    requests.packages.urllib3.disable_warnings()

    try:
        session = zhmcclient.Session(args.hmc, args.user, args.password)
        client = zhmcclient.Client(session)

        if args.timestats:
            session.time_stats_keeper.enable()

        if args.cpcnames:
            cpcs = []
            for cpcname in args.cpcnames:
                try:
                    cpc = client.cpcs.find(name=cpcname)
                except zhmcclient.NotFound:
                    raise zhmcclient.Error("Could not find CPC %s on HMC %s" %
                                           (cpcname, args.hmc))
                cpcs.append(cpc)
        else:
            cpcs = client.cpcs.list()

        cpc_names = [_cpc.prop('name') for _cpc in cpcs]
        # Note: Naming this '_cpc' avoids flake8 F812

        if args.cpcnames:
            cpc_str = "CPCs: %s" % ', '.join(cpc_names)
        else:
            cpc_str = "all CPCs"

        print("Extracting HMC %s with user %s (%s) " %
              (args.hmc, args.user, cpc_str), end='')
        sys.stdout.flush()

        # This first operation is performed directly through the session, in
        # order to get exceptions raised in case of failure.
        result = session.get('/api/version', logon_required=False)
        print("\nHMC API version: %s.%s" % (result['api-major-version'],
                                            result['api-minor-version']))
        print("HMC version: %s" % result['hmc-version'])
        sys.stdout.flush()

        hmcinfo = HMCInfo(args.hmc, args.user)

        record_get(hmcinfo, session, '/api/version')
        record_get(hmcinfo, session,
                   '/api/sessions/operations/get-notification-topics')

        cpcs_result = record_get(hmcinfo, session, '/api/cpcs')
        for cpc in cpcs_result['cpcs']:
            cpc_name = cpc['name']

            if cpc_name not in cpc_names:
                continue

            print("\nExtracting CPC %s " % cpc_name, end='')

            cpc_uri = cpc['object-uri']
            cpc_props = record_get(hmcinfo, session, cpc_uri)

            try:
                dpm_enabled = cpc_props['dpm-enabled']
            except KeyError:
                dpm_enabled = False
            if dpm_enabled:

                print("\n  CPC is in DPM mode", end='')
                print("\n  Adapters ", end='')
                adapters = record_get(hmcinfo, session, cpc_uri + '/adapters')
                if adapters:
                    for adapter in adapters['adapters']:
                        adapter_uri = adapter['object-uri']
                        record_get(hmcinfo, session, adapter_uri)

                print("\n  Virtual Switches ", end='')
                vswitches = record_get(hmcinfo, session,
                                       cpc_uri + '/virtual-switches')
                if vswitches:
                    for vswitch in vswitches['virtual-switches']:
                        vswitch_uri = vswitch['object-uri']
                        record_get(hmcinfo, session, vswitch_uri)

                print("\n  Partitions ", end='')
                parts = record_get(hmcinfo, session, cpc_uri + '/partitions')
                if parts:
                    for part in parts['partitions']:
                        part_uri = part['object-uri']
                        part_name = part['name']
                        record_get(hmcinfo, session, part_uri)

                        print("\nExtracting Partition %s" % part_name, end='')

                        print("\n  Virtual Functions ", end='')
                        vfs = record_get(hmcinfo, session,
                                         part_uri + '/virtual-functions')
                        if vfs:
                            for vf in vfs['virtual-functions']:
                                vf_uri = vf['object-uri']
                                record_get(hmcinfo, session, vf_uri)

                        print("\n  NICs ", end='')
                        nics = record_get(hmcinfo, session, part_uri + '/nics')
                        if nics:
                            for nic in nics['nics']:
                                nic_uri = nic['object-uri']
                                record_get(hmcinfo, session, nic_uri)

                        print("\n  HBAs ", end='')
                        hbas = record_get(hmcinfo, session, part_uri + '/hbas')
                        if hbas:
                            for hba in hbas['hbas']:
                                hba_uri = hba['object-uri']
                                record_get(hmcinfo, session, hba_uri)
            else:

                print("\n  CPC is in classic mode", end='')

                print("\n  LPARs ", end='')
                lpars = record_get(hmcinfo, session,
                                   cpc_uri + '/logical-partitions')
                if lpars:
                    for lpar in lpars['logical-partitions']:
                        lpar_uri = lpar['object-uri']
                        record_get(hmcinfo, session, lpar_uri)

                print("\n  Reset Profiles ", end='')
                resetprofs = record_get(hmcinfo, session,
                                        cpc_uri + '/reset-activation-profiles')
                if resetprofs:
                    for resetprof in resetprofs['reset-activation-profiles']:
                        resetprof_uri = resetprof['element-uri']
                        record_get(hmcinfo, session, resetprof_uri)

                print("\n  Image Profiles ", end='')
                imageprofs = record_get(hmcinfo, session,
                                        cpc_uri + '/image-activation-profiles')
                if imageprofs:
                    for imageprof in imageprofs['image-activation-profiles']:
                        imageprof_uri = imageprof['element-uri']
                        record_get(hmcinfo, session, imageprof_uri)

                print("\n  Load Profiles ", end='')
                loadprofs = record_get(hmcinfo, session,
                                       cpc_uri + '/load-activation-profiles')
                if loadprofs:
                    for loadprof in loadprofs['load-activation-profiles']:
                        loadprof_uri = loadprof['element-uri']
                        record_get(hmcinfo, session, loadprof_uri)

                print("\n  Group Profiles ", end='')
                groupprofs = record_get(hmcinfo, session,
                                        cpc_uri + '/group-profiles')
                if groupprofs:
                    for groupprof in groupprofs['group-profiles']:
                        groupprof_uri = groupprof['element-uri']
                        record_get(hmcinfo, session, groupprof_uri)

        print("\nLogging off")
        session.logoff()

        print("Writing to HMC info file: %s" % args.hmcinfo_file)
        with open(args.hmcinfo_file, 'w') as fp:
            hmcinfo.dump(fp)

        if args.timestats:
            print(session.time_stats_keeper)

        print("Done.")

    except zhmcclient.Error as exc:
        print("%s: %s" % (exc.__class__.__name__, exc))
        sys.exit(1)


def record_op(hmcinfo, session, method, uri, request_body=None):
    print('.', end='')
    sys.stdout.flush()
    return hmcinfo.record_op(session, method, uri, request_body)


def record_get(hmcinfo, session, uri):
    return record_op(hmcinfo, session, 'get', uri, None)


if __name__ == '__main__':
    main()
