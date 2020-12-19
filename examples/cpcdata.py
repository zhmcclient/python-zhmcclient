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
Display information about CPCs and their basic resources in the data center.
"""

from __future__ import absolute_import, print_function

import os
import platform
import sys
import logging
import argparse
from datetime import datetime
from platform import python_version
from requests.packages import urllib3
import yaml

import zhmcclient


MYNAME = 'cpcdata'

# Model information:
MACH_TYPE_INFO = {

    # mach-type: (name, max-partitions)

    '2064': ('z900', 15),
    '2084': ('z990', 30),
    '2094': ('z9 EC', 60),
    '2097': ('z10 EC', 60),
    '2817': ('z196', 60),
    '2827': ('zEC12', 60),
    '2964': ('z13', 85),  # Also LinuxONE Emperor
    '3906': ('z14', 85),  # Also LinuxONE Emperor II
    '3907': ('z14-ZR1', 40),  # Also LinuxONE Rockhopper II

    '2066': ('z800', 15),
    '2086': ('z890', 30),
    '2096': ('z9 BC', 30),  # Some models have only 15 partitions
    '2098': ('z10 BC', 30),
    '2818': ('z114', 30),
    '2828': ('zBC12', 30),
    '2965': ('z13s', 40),  # Also LinuxONE Rockhopper
}


# Status values for "running" partitions:
PARTITION_RUNNING_STATI = (
    'starting',
    'active',
    'stopping',
    'degraded',
    'reservation-error',
    'paused',
)
LPAR_RUNNING_STATI = (
    'operating',
    'exceptions',
)


# Defines order of columns in CSV output.
# The names are used both as column headings in the CSV output, and as
# names in the cpc_info dictionary.
CSV_FIELDS = (
    'timestamp',
    'hmc',
    'name',
    'description',
    'machine-type',
    'machine-model',
    'machine-type-name',
    'dpm-enabled',
    'is-ensemble-member',
    'iml-mode',
    'processors-ifl',
    'processors-cp',
    'memory-total',
    'memory-available',
    'partitions-maximum',
    'partitions-defined',
    'partitions-running',
)


def main():
    """
    Main function.
    """
    urllib3.disable_warnings()
    args = parse_args()
    config_file = args.config_file

    with open(args.config_file, 'r') as fp:
        config_root = yaml.load(fp)

    config_this = config_root.get(MYNAME, None)
    if config_this is None:
        raise ConfigError("'%s' item not found in config file %s" %
                          (MYNAME, config_file))

    config_hmcs = config_this.get("hmcs", None)
    if config_hmcs is None:
        raise ConfigError("'%s' / 'hmcs' item not found in config "
                          "file %s" % (MYNAME, config_file))

    config = argparse.Namespace()
    config.loglevel = config_this.get("loglevel", None)
    config.logmodule = config_this.get("logmodule", 'zhmcclient')
    config.timestats = config_this.get("timestats", False)
    config.verbose = args.verbose
    config.csv_file = args.csv_file
    config.timestamp = datetime.now().replace(second=0, microsecond=0)

    if config.loglevel is not None:
        level = getattr(logging, config.loglevel.upper(), None)
        if level is None:
            raise ConfigError("Invalid value for 'loglevel' item in "
                              "config file %s: %s" %
                              (config_file, config.loglevel))
        logmodule = config.logmodule
        if config.logmodule is None:
            config.logmodule = ''  # root logger
        handler = logging.StreamHandler()  # log to stdout
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        handler.setFormatter(logging.Formatter(format_string))
        logger = logging.getLogger(logmodule)
        logger.addHandler(handler)
        logger.setLevel(level)

        if config.verbose:
            print("Logging to stdout for module %s with level %s" %
                  (config.logmodule, config.loglevel))

    try:

        print_csv_header(config)

        for hmc_host in config_hmcs:

            config_hmc = config_root.get(hmc_host, None)
            if config_hmc is None:
                raise ConfigError("'%s' item (credentials for that HMC) not "
                                  "found in config file %s" % config_file)

            hmc_userid = config_hmc.get('userid', None)
            if hmc_userid is None:
                raise ConfigError("'%s' / 'userid' item not found in config "
                                  "file %s" % config_file)

            hmc_password = config_hmc.get('password', None)
            if hmc_password is None:
                raise ConfigError("'%s' / 'password' item not found in config "
                                  "file %s" % config_file)

            process_hmc(config, hmc_host, hmc_userid, hmc_password)

    except zhmcclient.Error as exc:
        print("%s: %s" % (exc.__class__.__name__, exc))
        # traceback.print_exc()
        sys.exit(1)
    except ConfigError as exc:
        print("%s: %s" % (exc.__class__.__name__, exc))
        sys.exit(1)


def process_hmc(config, hmc_host, hmc_userid, hmc_password):
    """
    Process the HMC and display info about it.
    """
    if config.verbose:
        print("Processing HMC %s" % hmc_host)

    # Test whether we can ping the HMC
    if config.verbose:
        print("Attempting to ping HMC ...")
    reachable = ping(hmc_host)
    if not reachable:
        print("Warning: Cannot ping HMC %s" % hmc_host)
        return

    try:

        session = zhmcclient.Session(hmc_host, hmc_userid, hmc_password)
        client = zhmcclient.Client(session)

        if config.timestats:
            session.time_stats_keeper.enable()

        # Test whether we can use an operation that does not require logon
        try:

            if config.verbose:
                print("Attempting to get HMC version ...")
            client.version_info()

        except zhmcclient.ConnectionError:
            print("Warning: Cannot connect to API on HMC %s" % hmc_host)
            return

        # This is the first operation that requires logon
        if config.verbose:
            print("Attempting to list managed CPCs ...")
        cpcs = client.cpcs.list()

        for cpc in sorted(cpcs, key=lambda cpc: cpc.prop('name', '')):
            process_cpc(config, cpc, hmc_host)

        session.logoff()

        if config.timestats:
            print(session.time_stats_keeper)

    except zhmcclient.Error as exc:
        print("Warning: %s on HMC %s: %s" %
              (exc.__class__.__name__, hmc_host, exc))
        return


def process_cpc(config, cpc, hmc_host):
    """
    Process the CPC and display info about it.
    """

    if config.verbose:
        print("Attempting to list partitions on CPC %s ..." % cpc.prop('name'))
    if cpc.dpm_enabled:
        partitions = cpc.partitions.list()
    else:
        partitions = cpc.lpars.list()

    if config.verbose:
        print("Attempting to retrieve properties of CPC %s ..." %
              cpc.prop('name'))

    cpc_info = {}
    cpc_info['timestamp'] = config.timestamp
    cpc_info['hmc'] = hmc_host
    cpc_info['name'] = cpc.prop('name')
    cpc_info['description'] = cpc.prop('description')
    cpc_info['status'] = cpc.prop('status')
    cpc_info['machine-type'] = cpc.prop('machine-type')
    cpc_info['machine-model'] = cpc.prop('machine-model')
    cpc_info['machine-type-name'] = model_name(cpc)
    cpc_info['dpm-enabled'] = cpc.prop('dpm-enabled', False)
    cpc_info['is-ensemble-member'] = cpc.prop('is-ensemble-member', False)
    cpc_info['iml-mode'] = cpc.prop('iml-mode')
    cpc_info['processors-ifl'] = cpc.prop('processor-count-ifl')
    cpc_info['processors-cp'] = cpc.prop('processor-count-general-purpose')
    # in MiB, may be None on older models:
    cpc_info['memory-total'] = cpc.prop('storage-customer', None)
    # in MiB, may be None on older models:
    cpc_info['memory-available'] = cpc.prop('storage-customer-available', None)
    # may be None if unknown:
    cpc_info['partitions-maximum'] = max_partitions(cpc)
    cpc_info['partitions-defined'] = defined_partitions(partitions)
    cpc_info['partitions-running'] = running_partitions(partitions)

    print_cpc_as_text(config, cpc_info)
    print_cpc_as_csv(config, cpc_info)


def print_cpc_as_text(config, cpc_info):
    # pylint: disable=unused-argument
    """
    Print info about the CPC as text.
    """

    print("CPC {name} managed by HMC {hmc}:".format(**cpc_info))

    print("  Description:  {description}".format(**cpc_info))
    print("  Machine:  {machine-type}-{machine-model} ({machine-type-name})".
          format(**cpc_info))
    print("  DPM enabled: {dpm-enabled}".format(**cpc_info))
    print("  Member of ensemble: {is-ensemble-member}".format(**cpc_info))
    print("  IML mode: {iml-mode}".format(**cpc_info))
    print("  Status: {status}".format(**cpc_info))

    print("  Processors: CPs: {processors-cp}, IFLs: {processors-ifl}".
          format(**cpc_info))

    mem_total = ("{} GiB".format(cpc_info['memory-total'] / 1024)) \
        if cpc_info['memory-total'] else "N/A"
    mem_avail = ("{} GiB".format(cpc_info['memory-available'] / 1024)) \
        if cpc_info['memory-available'] else "N/A"
    print("  Memory for partitions: total: {}, available: {}".
          format(mem_total, mem_avail))

    print("  Partitions: max-active: {}, defined: {}, running: {}".
          format(cpc_info['partitions-maximum'] or "N/A",
                 cpc_info['partitions-defined'] or "N/A",
                 cpc_info['partitions-running'] or "N/A"))


def print_cpc_as_csv(config, cpc_info):
    """
    Print info about the CPC as CSV.
    """

    if config.csv_file:
        with open(config.csv_file, "a") as fp:
            data_line = ','.join(
                ['"{}"'.format(cpc_info[col]) for col in CSV_FIELDS])
            fp.write(data_line)
            fp.write('\n')


def print_csv_header(config):
    """
    Print CSV header.
    """

    if config.csv_file:
        if not os.path.isfile(config.csv_file):
            if config.verbose:
                print("Creating new CSV output file: %s" % config.csv_file)
            with open(config.csv_file, "w") as fp:
                header_line = ','.join(
                    ['"{}"'.format(col) for col in CSV_FIELDS])
                fp.write(header_line)
                fp.write('\n')
        else:
            if config.verbose:
                print("Appending to existing CSV output file: %s" %
                      config.csv_file)


def parse_args():
    """
    Parse command line arguments and return the parsed args.

    In case of argument errors, print an error message and exit.
    """

    version = zhmcclient.__version__  # pylint: disable=no-member
    usage = "%(prog)s [options] CONFIGFILE"
    desc = "Gather data about all CPCs managed by a set of HMCs. The data " \
        "is displayed and optionally written to a CSV-formatted spreadsheet."
    epilog = ""

    argparser = argparse.ArgumentParser(
        prog=MYNAME, usage=usage, description=desc, epilog=epilog,
        add_help=False)

    pos_arggroup = argparser.add_argument_group(
        'Positional arguments')
    pos_arggroup.add_argument(
        'config_file', metavar='CONFIGFILE', nargs='?', default=None,
        help='File path of config file for this tool. See --help-config '
        'for details about the config file format.')

    general_arggroup = argparser.add_argument_group('Options')
    version_str = '%s/zhmcclient %s, Python %s' %\
        (MYNAME, version, python_version())
    general_arggroup.add_argument(
        '--csv', dest='csv_file', metavar='CSVFILE',
        help='Write/append data to a CSV spreadsheet file.')
    general_arggroup.add_argument(
        '-v', '--verbose', dest='verbose', action='store_true',
        help='Show more messages while processing.')
    general_arggroup.add_argument(
        '--version', action='version', version=version_str,
        help='Show the relevant versions and exit.')
    general_arggroup.add_argument(
        '-h', '--help', action='help',
        help='Show this help message and exit.')
    general_arggroup.add_argument(
        '-hc', '--help-config', dest='help_config', action='store_true',
        help='Show help about the config file format and exit.')

    args = argparser.parse_args()

    if args.help_config:
        help_config()

    if not args.config_file:
        argparser.error('No config file specified (--help-config for details)')

    return args


def help_config():
    """
    Displpay help about the config file.
    """
    print("""
Format of config file.

The config file is a YAML file with the following entries. Unknown entries
are ignored. This format is compatible to the HMC credential file format
used by the zhmcclient examples, so the same file can be used.

The following template shows the format. Anything in angle brackets <> is
meant to be replaced by a real value::

    {myname}:
       hmcs:
          - "<hmc-host-1>"
          - "<hmc-host-2>"
          - ...
       loglevel: <null|info|warning|error|debug>
       logmodule: <zhmcclient|...>
       timestats: <no|yes>

    "<hmc-host-1>":
       userid: <userid for hmc-host-1>
       password: <password for hmc-host-1>

    "<hmc-host-2>":
       userid: <userid for hmc-host-1>
       password: <password for hmc-host-1>

    ...

Notes:
- HMC hosts can be specified as IP v4/v6 addresses or long or short host names.
- The "hmcs" entry defines which HMCs are contacted. All CPCs managed by these
  HMCs are shown.
- If multiple choices are shown (e.g. for loglevel), the first choice is always
  the default.
""".format(myname=MYNAME))
    sys.exit(2)


class ConfigError(Exception):
    """
    Indicates an issue in the config file.
    """
    pass


def ping(host, timeout=10):
    """
    Ping a host with one ICMP packet and return whether it responded to the
    ping request.

    Parameters:

      host (string): IP address or host name.

      timeout (integer): Timeout in seconds.

    Returns:

      bool: Host has responded.
    """
    if platform.system() == "Windows":
        ping_options = "-n 1 -w %d" % (timeout * 1000)
        ping_drop_output = ">nul 2>&1"
    else:  # Linux or OS-X
        ping_options = "-c 1 -W %d" % timeout
        ping_drop_output = ">/dev/null 2>&1"
    rc = os.system("ping %s %s %s" % (ping_options, host, ping_drop_output))
    return rc == 0


def model_name(cpc):
    """
    Return the model name for a CPC.
    """
    mach_type = cpc.prop('machine-type')
    try:
        _model_name = MACH_TYPE_INFO[mach_type][0]
    except KeyError:
        _model_name = None
    if _model_name:
        return _model_name
    return "unknown"


def max_partitions(cpc):
    """
    Return the maxiumum number of user partitions or LPARs for a CPC.
    """
    mach_type = cpc.prop('machine-type')
    try:
        max_parts = MACH_TYPE_INFO[mach_type][1]
    except KeyError:
        max_parts = None
    if max_parts:
        return max_parts
    return "?"


def defined_partitions(partitions):
    """
    Return the defined number of user partitions or LPARs.
    """
    return len(partitions)


def running_partitions(partitions):
    """
    Return the number of running user partitions or LPARs.
    """
    count = 0
    for p in partitions:
        if isinstance(p, zhmcclient.Partition):
            running_stati = PARTITION_RUNNING_STATI
        else:
            running_stati = LPAR_RUNNING_STATI
        if p.prop('status') in running_stati:
            count += 1
    return count


if __name__ == '__main__':
    main()
