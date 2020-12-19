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
Display information about a CPC.
"""

from __future__ import absolute_import, print_function

import sys
import argparse
from getpass import getpass
from datetime import datetime
from platform import python_version
from requests.packages import urllib3
from tabulate import tabulate
import progressbar

import zhmcclient


def parse_args():
    """
    Parse command line arguments and return the parsed args.

    In case of argument errors, print an error message and exit.
    """

    prog = "cpcinfo"  # Name of this program, used for help etc.
    version = zhmcclient.__version__  # pylint: disable=no-member
    usage = '%(prog)s [options] hmc [cpcname ...]'
    desc = 'Display information about CPCs.'
    epilog = """
Example:
  %s -u ensadmin -p 1234 9.152.150.65 P0000P30
""" % prog

    argparser = argparse.ArgumentParser(
        prog=prog, usage=usage, description=desc, epilog=epilog,
        add_help=False)

    pos_arggroup = argparser.add_argument_group(
        'Positional arguments')
    pos_arggroup.add_argument(
        'hmc', metavar='hmc',
        help='IP address or hostname of the HMC managing the CPCs.')
    pos_arggroup.add_argument(
        'cpcnames', metavar='cpcname', nargs='*',
        help='Name of the CPC. Can be repeated. '
             'Default: All CPCs managed by the HMC.')

    general_arggroup = argparser.add_argument_group(
        'Options')
    general_arggroup.add_argument(
        '-u', '--user', dest='user', metavar='user',
        help='Required: User name for authenticating with the HMC.')
    general_arggroup.add_argument(
        '-p', '--password', dest='password', metavar='password',
        help='Password for authenticating with the HMC.\n'
             'Default: Prompt for a password.')
    pos_arggroup.add_argument(
        '-m', '--mcl', dest='mcl', action='store_true',
        help='Add information about the MCL level of each component.')
    pos_arggroup.add_argument(
        '-a', '--adapters', dest='adapters', action='store_true',
        help='Add information about the adapters in the CPC.')
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

    if not args.user:
        argparser.error('No HMC userid specified (-u/--userid option)')

    if not args.password:
        args.password = getpass('Enter password for %s: ' % args.user)

    return args


class ProgressBar(object):
    """
    A progress bar, based upon the progressbar2 package.
    """

    def __init__(self, max_value):
        self._max = max_value
        self._current = 0
        self._widgets = [progressbar.Percentage(),
                         ' ', progressbar.Bar(),
                         ' ', progressbar.ETA()]
        self._bar = progressbar.ProgressBar(widgets=self._widgets,
                                            max_value=max_value)

    def progress(self):
        """
        Function called to advance the progress bar one step.
        """
        self._current += 1
        self._bar.update(self._current)

    @property
    def current_value(self):
        """
        The current value of the progress bar.
        """
        return self._current

    def change_max(self, max_value):
        """
        Adjust the max value of the progress bar.
        """
        self._max = max_value
        self._bar = progressbar.ProgressBar(widgets=self._widgets,
                                            initial_value=self._current,
                                            max_value=self._max)

    def start(self):
        """
        Start the progress bar.
        """
        self._bar.start()

    def finish(self):
        """
        Finish the progress bar.
        """
        self._bar.finish()


def main():
    """
    Main routine.
    """

    args = parse_args()

    urllib3.disable_warnings()

    try:
        print("Using HMC %s with userid %s" % (args.hmc, args.user))

        session = zhmcclient.Session(args.hmc, args.user, args.password)
        client = zhmcclient.Client(session)

        if args.timestats:
            session.time_stats_keeper.enable()

        dt_start = datetime.now()

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

        for cpc in sorted(cpcs, key=lambda cpc: cpc.prop('name', '')):

            print("\nRetrieving CPC %s ..." % cpc.prop('name'))
            sys.stdout.flush()

            probar = ProgressBar(max_value=30)
            probar.start()

            if cpc.dpm_enabled:
                probar.progress()  # dpm_enabled performs "Get CPC Properties"
                partitions_kind = "Partitions"
                partition_header = ("Name", "Status", "OS Type", "OS Version")
                partitions = cpc.partitions.list()
                probar.progress()
                probar.change_max(probar.current_value +  # noqa: W504
                                  len(partitions) + 1 +  # noqa: W504
                                  (1 if args.adapters else 0))
                partition_rows = []
                for partition in sorted(partitions,
                                        key=lambda p: p.prop('name', '')):
                    row = (partition.prop('name'),
                           partition.prop('status'),
                           partition.prop('os-type'),
                           partition.prop('os-version'))
                    probar.progress()
                    partition_rows.append(row)
            else:
                probar.progress()
                partitions_kind = "LPARs"
                partition_header = ("Name", "Status", "OS Type", "OS Level")
                partitions = cpc.lpars.list()
                probar.progress()
                probar.change_max(probar.current_value +  # noqa: W504
                                  len(partitions) + 1 +  # noqa: W504
                                  (1 if args.adapters else 0))
                partition_rows = []
                for partition in sorted(partitions,
                                        key=lambda p: p.prop('name', '')):
                    row = (partition.prop('name'),
                           partition.prop('status'),
                           partition.prop('os-type'),
                           partition.prop('os-level'))
                    probar.progress()
                    partition_rows.append(row)

            machine_gen = "z" + cpc.prop('se-version').split('.')[1]
            probar.progress()

            if args.adapters:
                adapter_header = ("Location", "Card", "Type", "Ports")
                adapters = cpc.adapters.list()
                probar.progress()
                adapter_rows = []
                for adapter in sorted(adapters,
                                      key=lambda p: p.prop('card-location',
                                                           '')):
                    row = (adapter.prop('card-location'),
                           adapter.prop('detected-card-type'),
                           adapter.prop('type'),
                           adapter.prop('port-count'))
                    adapter_rows.append(row)

            probar.finish()

            print("CPC %s" % cpc.prop('name'))
            print("  Machine:  %s-%s (%s)" % (cpc.prop('machine-type'),
                                              cpc.prop('machine-model'),
                                              machine_gen))
            print("  IML mode: %s" % cpc.prop('iml-mode'))

            print("\nCPUs:")
            print("  CP:  %s" %
                  cpc.prop('processor-count-general-purpose'))
            print("  IFL: %s" %
                  cpc.prop('processor-count-ifl'))
            print("  IIP: %s" %
                  cpc.prop('processor-count-iip'))
            print("  AAP: %s" %
                  cpc.prop('processor-count-aap'))
            print("  ICF: %s" %
                  cpc.prop('processor-count-icf'))
            print("  SAP: %s" %
                  cpc.prop('processor-count-service-assist'))
            print("  spare: %s" %
                  cpc.prop('processor-count-spare'))
            print("  defective: %s" %
                  cpc.prop('processor-count-defective'))

            mem_cust = int(cpc.prop('storage-customer', '0')) / 1024
            mem_hsa = int(cpc.prop('storage-hardware-system-area', '0')) /\
                1024
            print("\nMemory:")
            print("  Customer:  %d GB" % mem_cust)
            print("  HSA:       %d GB" % mem_hsa)

            if args.mcl:
                mc_desc = cpc.prop('ec-mcl-description')
                mc_header = ["Component", "Level"]
                mc_rows = []
                for ec in sorted(mc_desc['ec'],
                                 key=lambda ec: ec['description']):
                    mc_component = ec['description']
                    mc_level = 'unknown'
                    for mcl in ec['mcl']:
                        if mcl['type'] == 'activated':
                            mc_level = mcl['level']
                            break
                    mc_rows.append((mc_component, mc_level))

                print("\nActive microcode levels:")
                print(tabulate(mc_rows, mc_header))

            if args.adapters:
                print("\nAdapters:")
                print(tabulate(adapter_rows, adapter_header))

            print("\n%s:" % partitions_kind)
            print(tabulate(partition_rows, partition_header))

        session.logoff()

        dt_end = datetime.now()
        delta = dt_end - dt_start
        print("Total time for retrieving the information: %d s" %
              delta.total_seconds())

        if args.timestats:
            print(session.time_stats_keeper)

    except zhmcclient.Error as exc:
        print("%s: %s" % (exc.__class__.__name__, exc))
        sys.exit(1)


if __name__ == '__main__':
    main()
