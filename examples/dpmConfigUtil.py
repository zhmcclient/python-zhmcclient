#!/usr/bin/env python
# Copyright 2016-2022 IBM Corp. All Rights Reserved.
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
Enhanced example: HMC Web Services API DPM configuration import/export utility

A utility that relies on the zhmcclient python library to either
* EXPORT a DPM configuration as file
* IMPORT such a file to a CPC running in DPM mode.
"""

import argparse
import datetime
import getpass
import json
import logging
import re
import sys

import requests.packages.urllib3

import zhmcclient

global logger


def main(argv):
    args = parse_arguments(argv)
    global logger
    logger = init_logger()
    dpm_config = {}
    if args.command == 'import':
        dpm_config = read_config(args)
    (session, client) = create_session(args)
    cpc = get_cpc(client, args)

    try:
        if args.command == 'export':
            logger.info('now EXPORTING dpm configuration from {}'.format(args.ip))
            export_configuration(cpc, args)
        if args.command == 'import':
            logger.info('now IMPORTING dpm configuration from {}'.format(args.dpm_config))
            import_configuration(cpc, dpm_config)
        logger.info('all done, logging off')
        session.logoff()
    except zhmcclient.Error as e:
        logger.error('command execution failed with exception!')
        logger.error(e)


def export_configuration(cpc, args):
    logger.info('exporting ...')
    output = cpc.export_dpm_configuration()
    write_json_to_file(output, args.cpc)
    dump_config(output)


def import_configuration(cpc, config):
    dump_config(config)
    output_details = cpc.import_dpm_configuration(config)
    if output_details is None:
        logger.info('Configuration was imported COMPLETELY')
    else:
        logger.warning('Configuration was imported PARTIALLY')
        logger.info(json.dumps(output_details, indent=2, sort_keys=True))


def parse_arguments(argv):
    parser = argparse.ArgumentParser(description='''
    A zhmcclient script that either EXPORTS the DPM configuration data for a given CPC to a file,
    or IMPORTS such configuration data from a file.
    In both modes, you have to specify the target HMC IP address, the user name plus corresponding password
    and the name of the target CPC.

    command=export --- no arguments required/allowed
    command=import --- requires --dpm-config, allows --adapter-mapping, --preserve-uris, --preserve-wwpns
    where
    --dpm-config      points to a file containing the JSON object to pass to the import call
    --adapter-mapping points to a file containing raw text (old pchid, new pchid) like:
    100,200
    10A,20F
    ...
    (lines beginning with # will be ignored)

    ''', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('command',
                        help='the command to execute',
                        choices=['export', 'import'], nargs='?')

    # arguments required for establishing the zhmcclient session
    parser.add_argument('-i', '--ip', type=str, required=True,
                        help='the IP address of the HMC to connect to')
    parser.add_argument('-u', '--user', type=str, required=True,
                        help='the HMC user used for the HMC Web Services API')
    parser.add_argument('-p', '--password', type=str,
                        help='the corresponding password (will be read from stdin if not provided as argument)')
    parser.add_argument('-n', '--no-verify', help='Do not verify the HMC certificate', action='store_true',
                        default=False)

    # CPC selection
    parser.add_argument('-c', '--cpc', type=str, required=True,
                        help='the name of the CPC attached to the HMC that is used for targeting')

    # import
    parser.add_argument('-d', '--dpm-config', type=str,
                        help='the name of the file with the DPM configuration data to import')
    parser.add_argument('-a', '--adapter-mapping', type=str,
                        help='the name of the file with raw adapter mapping information to use')
    parser.add_argument('--preserve-uris', action='store_true', help='force Object/Element ID preservation')
    parser.add_argument('--preserve-wwpns', action='store_true', help='force HBA WWPNs to be preserved')

    args = parser.parse_args(argv)
    check_arguments(args)

    return args


def check_arguments(args):
    fail_on(args.command is None, 'Mandatory COMMAND is missing.')
    fail_on(args.command == 'export' and args.dpm_config, '--dpm-config not allowed for command export')
    fail_on(args.command == 'export' and args.adapter_mapping, '--adapter-mapping not allowed for command export')
    fail_on(args.command == 'export' and args.preserve_uris, '--preserve-uris not allowed for command export')
    fail_on(args.command == 'export' and args.preserve_wwpns, '--preserve-wwpns not allowed for command export')
    fail_on(args.command == 'import' and not args.dpm_config, '--dpm-config required for command import')


def fail_on(condition, message):
    if condition:
        logger.error(message)
        sys.exit(2)


def create_session(args):
    if args.password:
        password = args.password
    else:
        password = getpass.getpass('Enter the password for user {}:'.format(args.user))
    try:
        if args.no_verify:
            session = zhmcclient.Session(args.ip, args.user, password, verify_cert=False)
        else:
            session = zhmcclient.Session(args.ip, args.user, password)

        requests.packages.urllib3.disable_warnings()
        session.logon()
        logger.info('Logon to {} successful as {}'.format(args.ip, args.user))

        return session, zhmcclient.Client(session)
    except Exception as e:
        logger.error('Logon to {} failed'.format(args.ip), e)
        sys.exit(2)


def get_cpc(client, args):
    try:
        cpc = client.cpcs.find(name=args.cpc)
        return cpc
    except Exception as e:
        logger.exception('Cpc {} does not exist on HMC {}'.format(args.cpc, args.ip), e)
        sys.exit(2)


def dump_config(config):
    for k in sorted(config.keys()):
        if isinstance(config[k], list):
            logger.info('{:>3} {} resource(s)'.format(len(config[k]), k))


def write_json_to_file(json_data, cpc_name):
    outfile_name = cpc_name + '.dpm.json'
    with open(outfile_name, 'w') as outfile:
        json.dump(json_data, outfile, indent=2, sort_keys=True)
    logger.info('Dpm resources ({0} objects ) written to file {1}'.format(len(json_data), outfile_name))


def read_config(args):
    with open(args.dpm_config) as f:
        dpm_config = json.load(f)
    logger.info('read {}'.format(args.dpm_config))

    args_dict = vars(args)

    add_configuration_element_with_check(dpm_config, args_dict, 'adapter-mapping', parse_mappings(args))
    add_configuration_element_with_check(dpm_config, args_dict, 'preserve-uris', True)
    add_configuration_element_with_check(dpm_config, args_dict, 'preserve-wwpns', True)
    return dpm_config


def add_configuration_element_with_check(dpm_config, args, wsapi_key, content):
    dict_key = wsapi_key.replace('-', '_')
    if not args[dict_key]:
        return

    fail_on(wsapi_key in dpm_config.keys(),
            'command line uses {}, but {} already contains that field'.format(wsapi_key,
                                                                              args['dpm_config']))
    dpm_config[wsapi_key] = content
    logger.info('updated import configuration data for key: {}'.format(wsapi_key))


def parse_mappings(args):
    if not args.adapter_mapping:
        return []

    lines = []
    with open(args.adapter_mapping) as f:
        for line in f:
            stripped = ''.join(line.split()).upper()
            if not stripped or stripped.startswith('#'):
                continue
            match = re.match('([0-9A-F]{3}),([0-9A-F]{3})', stripped)
            fail_on(not match, 'Failed to parse adapter mapping line: <{}>'.format(line.rstrip()))
            lines.append({'old-adapter-id': match.group(1), 'new-adapter-id': match.group(2), })

    for mapping in lines:
        logger.info('mapping: {}'.format(mapping))
    return lines


def init_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s]  {%(filename)s:%(lineno)d}  %(levelname)s - %(message)s',
        filename='configutil-{}.log'.format(
            # the current time in ISO format, without trailing milliseconds and - instead of :
            datetime.datetime.now().isoformat().split('.', 1)[0].replace(':', '-')),
        filemode='w')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    return logging.getLogger('')


if __name__ == '__main__':
    main(sys.argv[1:])
