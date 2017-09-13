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

from __future__ import absolute_import
from __future__ import print_function

import os

import logging
import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    part_console, raise_click_exception
from ._cmd_cpc import find_cpc


# Defaults for partition creation
DEFAULT_IFL_PROCESSORS = 1
DEFAULT_INITIAL_MEMORY_MB = 1024
DEFAULT_MAXIMUM_MEMORY_MB = 1024
DEFAULT_PROCESSOR_MODE = 'shared'
PARTITION_TYPES = ['ssc', 'linux', 'zvm']
DEFAULT_PARTITION_TYPE = 'linux'
DEFAULT_SSC_BOOT = 'installer'
DEFAULT_PROCESSING_WEIGHT = 100
MIN_PROCESSING_WEIGHT = 1
MAX_PROCESSING_WEIGHT = 999


def find_partition(cmd_ctx, client, cpc_name, partition_name):
    """
    Find a partition by name and return its resource object.
    """
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    # The CPC must be in DPM mode. We don't check that because it would
    # cause a GET to the CPC resource that we otherwise don't need.
    try:
        partition = cpc.partitions.find(name=partition_name)
    except zhmcclient.Error as exc:
        raise_click_exception(exc, cmd_ctx.error_format)
    return partition


@cli.group('partition', options_metavar=COMMAND_OPTIONS_METAVAR)
def partition_group():
    """
    Command group for managing partitions.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@partition_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--type', is_flag=True, required=False,
              help='Show additional properties indicating the partition and '
              'OS type.')
@click.option('--uri', is_flag=True, required=False,
              help='Show additional properties for the resource URI.')
@click.pass_obj
def partition_list(cmd_ctx, cpc, **options):
    """
    List the partitions in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_list(cmd_ctx, cpc, options))


@partition_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.pass_obj
def partition_show(cmd_ctx, cpc, partition):
    """
    Show the details of a partition in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_show(cmd_ctx, cpc, partition))


@partition_group.command('start', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.pass_obj
def partition_start(cmd_ctx, cpc, partition):
    """
    Start a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_start(cmd_ctx, cpc, partition))


@partition_group.command('stop', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.pass_obj
def partition_stop(cmd_ctx, cpc, partition):
    """
    Stop a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_stop(cmd_ctx, cpc, partition))


@partition_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--name', type=str, required=True,
              help='The name of the new partition.')
@click.option('--description', type=str, required=False,
              help='The description of the new partition.')
@click.option('--cp-processors', type=int, required=False,
              help='The number of general purpose (CP) processors. '
              'Default: No CP processors')
@click.option('--ifl-processors', type=int, required=False,
              help='The number of IFL processors. '
              'Default: {}, if no CP processors have been specified'.
              format(DEFAULT_IFL_PROCESSORS))
@click.option('--processor-mode', type=click.Choice(['dedicated', 'shared']),
              required=False, default=DEFAULT_PROCESSOR_MODE,
              help='The sharing mode for processors. '
              'Default: {}'.format(DEFAULT_PROCESSOR_MODE))
@click.option('--initial-memory', type=int, required=False,
              default=DEFAULT_INITIAL_MEMORY_MB,
              help='The initial amount of memory (in MiB) when the partition '
              'is started. '
              'Default: {} MiB'.format(DEFAULT_INITIAL_MEMORY_MB))
@click.option('--maximum-memory', type=int, required=False,
              default=DEFAULT_MAXIMUM_MEMORY_MB,
              help='The maximum amount of memory (in MiB) while the partition '
              'is running. '
              'Default: {} MiB'.format(DEFAULT_MAXIMUM_MEMORY_MB))
@click.option('--boot-ftp-host', type=str, required=False,
              help='Boot from an FTP server: The hostname or IP address of '
              'the FTP server.')
@click.option('--boot-ftp-username', type=str, required=False,
              help='Boot from an FTP server: The user name on the FTP server.')
@click.option('--boot-ftp-password', type=str, required=False,
              help='Boot from an FTP server: The password on the FTP server.')
@click.option('--boot-ftp-insfile', type=str, required=False,
              help='Boot from an FTP server: The path to the INS-file on the '
              'FTP server.')
@click.option('--boot-media-file', type=str, required=False,
              help='Boot from removable media on the HMC: The path to the '
              'image file on the HMC.')
@click.option('--access-global-performance-data', type=bool, required=False,
              help='Indicates if global performance data authorization '
              'control is requested. Default: False')
@click.option('--permit-cross-partition-commands', type=bool, required=False,
              help='Indicates if cross partition commands authorization is'
              'requested. Default: False')
@click.option('--access-basic-counter-set', type=bool, required=False,
              help='Indicates if basic counter set authorization control is '
              'requested. Default: False')
@click.option('--access-problem-state-counter-set', type=bool, required=False,
              help='Indicates if problem state counter set authorization '
              'is requested. Default: False')
@click.option('--access-crypto-activity-counter-set',
              type=bool, required=False,
              help='Indicates is crypto activity counter set authorization '
              'control is requested. Default: False')
@click.option('--access-extended-counter-set', type=bool, required=False,
              help='Indicates if extended counter set authorization control '
              'is requested. Default: False')
@click.option('--access-coprocessor-group-set', type=bool, required=False,
              help='Indicates if coprocessor group set authorization control '
              'is requested. Default: False')
@click.option('--access-basic-sampling', type=bool, required=False,
              help='Indicates if basic CPU sampling authorization control is '
              'requested. Default: False')
@click.option('--access-diagnostic-sampling', type=bool, required=False,
              help='Indicates if diagnostic sampling authorization control '
              'is requested. Default: False')
@click.option('--type', type=click.Choice(PARTITION_TYPES), required=False,
              help='Defines the type of the partition (Default: {pd}).'.
              format(pd=DEFAULT_PARTITION_TYPE))
@click.option('--ssc-host-name', type=str, required=False,
              help='Secure Service Container host name. '
              'Only applicable to and required for ssc type partitions.')
@click.option('--ssc-ipv4-gateway', type=str, required=False,
              help='Default IPv4 Gateway to be used. '
              'Only applicable to ssc type partitions.')
@click.option('--ssc-dns-servers', type=str, required=False,
              help='DNS IP address information. '
              'Only applicable to ssc type partitions.')
@click.option('--ssc-master-userid', type=str, required=False,
              help='Secure Service Container master user ID. '
              'Only applicable to and required for ssc type partitions.')
@click.option('--ssc-master-pw', type=str, required=False,
              help='Secure Service Container master user password. '
              'Only applicable to and required for ssc type partitions.')
@click.option('--initial-cp-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT),
              required=False, default=DEFAULT_PROCESSING_WEIGHT,
              help='Defines the initial processing weight of CP processors. '
              'Default: {}'.format(DEFAULT_PROCESSING_WEIGHT))
@click.option('--initial-ifl-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT),
              required=False, default=DEFAULT_PROCESSING_WEIGHT,
              help='Defines the initial processing weight of IFL processors. '
              'Default: {}'.format(DEFAULT_PROCESSING_WEIGHT))
@click.option('--minimum-ifl-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT),
              required=False, default=MIN_PROCESSING_WEIGHT,
              help='Represents the minimum amount of IFL processor '
              'resources allocated to the partition. '
              'Default: {}'.format(MIN_PROCESSING_WEIGHT))
@click.option('--minimum-cp-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT),
              required=False, default=MIN_PROCESSING_WEIGHT,
              help='Represents the minimum amount of general purpose '
              'processor resources allocated to the partition. '
              'Default: {}'.format(MIN_PROCESSING_WEIGHT))
@click.option('--maximum-ifl-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT),
              required=False, default=MAX_PROCESSING_WEIGHT,
              help='Represents the maximum amount of IFL processor '
              'resources allocated to the partition. '
              'Default: {}'.format(MAX_PROCESSING_WEIGHT))
@click.option('--maximum-cp-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT),
              required=False, default=MAX_PROCESSING_WEIGHT,
              help='Represents the maximum amount of general purpose '
              'processor resources allocated to the partition. '
              'Default: {}'.format(MAX_PROCESSING_WEIGHT))
@click.pass_obj
def partition_create(cmd_ctx, cpc, **options):
    """
    Create a partition in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_create(cmd_ctx, cpc, options))


@partition_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--name', type=str, required=False,
              help='The new name of the partition.')
@click.option('--description', type=str, required=False,
              help='The new description of the partition.')
@click.option('--cp-processors', type=int, required=False,
              help='The new number of general purpose (CP) processors.')
@click.option('--ifl-processors', type=int, required=False,
              help='The new number of IFL processors.')
@click.option('--processor-mode', type=click.Choice(['dedicated', 'shared']),
              required=False,
              help='The new sharing mode for processors.')
@click.option('--initial-memory', type=int, required=False,
              help='The new initial amount of memory (in MiB) when the '
              'partition is started.')
@click.option('--maximum-memory', type=int, required=False,
              help='The new maximum amount of memory (in MiB) while the '
              'partition is running.')
@click.option('--boot-storage-hba', type=str, required=False,
              help='Boot from an FCP LUN: The name of the HBA to be used.')
@click.option('--boot-storage-lun', type=str, required=False,
              help='Boot from an FCP LUN: The LUN to boot from.')
@click.option('--boot-storage-wwpn', type=str, required=False,
              help='Boot from an FCP LUN: The WWPN of the storage '
              'controller exposing the LUN.')
@click.option('--boot-network-nic', type=str, required=False,
              help='Boot from a PXE server: The name of the NIC to be used.')
@click.option('--boot-ftp-host', type=str, required=False,
              help='Boot from an FTP server: The hostname or IP address of '
              'the FTP server.')
@click.option('--boot-ftp-username', type=str, required=False,
              help='Boot from an FTP server: The user name on the FTP server.')
@click.option('--boot-ftp-password', type=str, required=False,
              help='Boot from an FTP server: The password on the FTP server.')
@click.option('--boot-ftp-insfile', type=str, required=False,
              help='Boot from an FTP server: The path to the INS-file on the '
              'FTP server.')
@click.option('--boot-media-file', type=str, required=False,
              help='Boot from removable media on the HMC: The path to the '
              'image file on the HMC.')
@click.option('--boot-iso', type=str, required=False,
              help='Boot from an ISO image mounted to this partition.')
@click.option('--access-global-performance-data', type=bool, required=False,
              help='Indicates if global performance data authorization '
              'control is requested. Default: False')
@click.option('--permit-cross-partition-commands', type=bool, required=False,
              help='Indicates if cross partition commands authorization is'
              'requested. Default: False')
@click.option('--access-basic-counter-set', type=bool, required=False,
              help='Indicates if basic counter set authorization control is '
              'requested. Default: False')
@click.option('--access-problem-state-counter-set', type=bool, required=False,
              help='Indicates if problem state counter set authorization '
              'is requested. Default: False')
@click.option('--access-crypto-activity-counter-set',
              type=bool, required=False,
              help='Indicates is crypto activity counter set authorization '
              'control is requested. Default: False')
@click.option('--access-extended-counter-set', type=bool, required=False,
              help='Indicates if extended counter set authorization control '
              'is requested. Default: False')
@click.option('--access-coprocessor-group-set', type=bool, required=False,
              help='Indicates if coprocessor group set authorization control '
              'is requested. Default: False')
@click.option('--access-basic-sampling', type=bool, required=False,
              help='Indicates if basic CPU sampling authorization control is '
              'requested. Default: False')
@click.option('--access-diagnostic-sampling', type=bool, required=False,
              help='Indicates if diagnostic sampling authorization control '
              'is requested. Default: False')
@click.option('--ssc-host-name', type=str, required=False,
              help='Secure Service Container host name.')
@click.option('--ssc-boot-selection',
              type=click.Choice(['installer']), required=False,
              help='Set the boot mode of the Secure Service Container '
              'to run the SSC Appliance Installer again upon next '
              'partition start. Only applicable to ssc type partitions.')
@click.option('--ssc-ipv4-gateway', type=str, required=False,
              help='Default IPv4 Gateway to be used. '
              'Only applicable to ssc type partitions.')
@click.option('--ssc-dns-servers', type=str, required=False,
              help='DNS IP address information. '
              'Only applicable to ssc type partitions.')
@click.option('--ssc-master-userid', type=str, required=False,
              help='Secure Service Container master user ID. '
              'Only applicable to ssc type partitions.')
@click.option('--ssc-master-pw', type=str, required=False,
              help='Secure Service Container master user password. '
              'Only applicable to ssc type partitions.')
@click.option('--initial-cp-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT), required=False,
              help='Defines the initial processing weight of CP processors.')
@click.option('--initial-ifl-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT), required=False,
              help='Defines the initial processing weight of IFL processors.')
@click.option('--minimum-ifl-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT), required=False,
              help='Represents the minimum amount of IFL processor '
              'resources allocated to the partition.')
@click.option('--minimum-cp-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT), required=False,
              help='Represents the minimum amount of general purpose '
              'processor resources allocated to the partition.')
@click.option('--maximum-ifl-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT), required=False,
              help='Represents the maximum amount of IFL processor '
              'resources allocated to the partition.')
@click.option('--maximum-cp-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT), required=False,
              help='Represents the maximum amount of general purpose '
              'processor resources allocated to the partition.')
@click.pass_obj
def partition_update(cmd_ctx, cpc, partition, **options):
    """
    Update the properties of a partition.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_update(cmd_ctx, cpc, partition,
                                                     options))


@partition_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the partition.',
              prompt='Are you sure you want to delete this partition ?')
@click.pass_obj
def partition_delete(cmd_ctx, cpc, partition):
    """
    Delete a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_delete(cmd_ctx, cpc, partition))


@partition_group.command('console', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--refresh', is_flag=True, required=False,
              help='Include refresh messages.')
@click.pass_obj
def partition_console(cmd_ctx, cpc, partition, **options):
    """
    Establish an interactive session with the console of the operating system
    running in a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_console(cmd_ctx, cpc, partition,
                                                      options))


@partition_group.command('mountiso', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--imagefile', type=str, required=True,
              help='The file path of the ISO imagei file.')
@click.option('--imageinsfile', type=str, required=True,
              help='The file path of the INS file (within the file system '
              'of the ISO image file).')
@click.option('--boot', '-b', is_flag=True, required=False,
              help='Set boot-device property to iso-image.')
@click.pass_obj
def partition_mount_iso(cmd_ctx, cpc, partition, **options):
    """
    Mount an ISO image to a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_mount_iso(cmd_ctx, cpc,
                                                        partition, options))


@partition_group.command('unmountiso', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.pass_obj
def partition_unmount_iso(cmd_ctx, cpc, partition):
    """
    Unmount an ISO image from a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_unmount_iso(cmd_ctx, cpc,
                                                          partition))


def cmd_partition_list(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    try:
        partitions = cpc.partitions.list()
    except zhmcclient.Error as exc:
        raise_click_exception(exc, cmd_ctx.error_format)
        raise_click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
        'status',
    ]
    if options['type']:
        show_list.extend([
            'partition-type',
            'os-type',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    cmd_ctx.spinner.stop()
    print_resources(partitions, cmd_ctx.output_format, show_list)


def cmd_partition_show(cmd_ctx, cpc_name, partition_name):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    try:
        partition.pull_full_properties()
    except zhmcclient.Error as exc:
        raise_click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    print_properties(partition.properties, cmd_ctx.output_format)


def cmd_partition_start(cmd_ctx, cpc_name, partition_name):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    try:
        partition.start(wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise_click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo('Partition %s has been started.' % partition_name)


def cmd_partition_stop(cmd_ctx, cpc_name, partition_name):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    try:
        partition.stop(wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise_click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo('Partition %s has been stopped.' % partition_name)


def cmd_partition_create(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    name_map = {
        # The following options are handled in this function:
        'boot-ftp-host': None,
        'boot-ftp-username': None,
        'boot-ftp-password': None,
        'boot-ftp-insfile': None,
        'boot-media-file': None,
    }
    options = original_options(options)
    properties = options_to_properties(options, name_map)

    required_ftp_option_names = (
        'boot-ftp-host',
        'boot-ftp-username',
        'boot-ftp-password',
        'boot-ftp-insfile')
    if any([options[name] for name in required_ftp_option_names]):
        missing_option_names = [name for name in required_ftp_option_names
                                if options[name] is None]
        if missing_option_names:
            raise_click_exception("Boot from FTP server specified, but misses "
                                  "the following options: %s" %
                                  ', '.join(missing_option_names),
                                  cmd_ctx.error_format)
        properties['boot-device'] = 'ftp'
        properties['boot-ftp-host'] = options['boot-ftp-host']
        properties['boot-ftp-username'] = options['boot-ftp-username']
        properties['boot-ftp-password'] = options['boot-ftp-password']
        properties['boot-ftp-insfile'] = options['boot-ftp-insfile']
    elif options['boot-media-file'] is not None:
        properties['boot-device'] = 'removable-media'
        properties['boot-removable-media'] = options['boot-media-file']
    else:
        # boot-device="none" is the default
        pass

    # Default for the number of processors
    if 'ifl-processors' not in properties and \
            'cp-processors' not in properties:
        properties['ifl-processors'] = DEFAULT_IFL_PROCESSORS

    if options['ssc-dns-servers'] is not None:
        properties['ssc-dns-servers'] = options['ssc-dns-servers'].split(',')

    try:
        new_partition = cpc.partitions.create(properties)
    except zhmcclient.Error as exc:
        raise_click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New partition %s has been created." %
               new_partition.properties['name'])


def cmd_partition_update(cmd_ctx, cpc_name, partition_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    name_map = {
        # The following options are handled in this function:
        'boot-storage-hba': None,
        'boot-storage-lun': None,
        'boot-storage-wwpn': None,
        'boot-network-nic': None,
        'boot-ftp-host': None,
        'boot-ftp-username': None,
        'boot-ftp-password': None,
        'boot-ftp-insfile': None,
        'boot-media-file': None,
        'boot-iso': None,
    }
    options = original_options(options)
    properties = options_to_properties(options, name_map)

    required_storage_option_names = (
        'boot-storage-hba',
        'boot-storage-lun',
        'boot-storage-wwpn')
    required_ftp_option_names = (
        'boot-ftp-host',
        'boot-ftp-username',
        'boot-ftp-password',
        'boot-ftp-insfile')
    if any([options[name] for name in required_storage_option_names]):
        missing_option_names = [name for name in required_storage_option_names
                                if options[name] is None]
        if missing_option_names:
            raise_click_exception("Boot from FCP LUN specified, but misses "
                                  "the following options: %s" %
                                  ', '.join(missing_option_names),
                                  cmd_ctx.error_format)
        hba_name = options['boot-storage-hba']
        try:
            hba = partition.hbas.find(name=hba_name)
        except zhmcclient.NotFound:
            raise_click_exception("Could not find HBA %s in partition %s in "
                                  "CPC %s." %
                                  (hba_name, partition_name, cpc_name),
                                  cmd_ctx.error_format)
        properties['boot-device'] = 'storage-adapter'
        properties['boot-storage-device'] = hba.uri
        properties['boot-logical-unit-number'] = options['boot-storage-lun']
        properties['boot-world-wide-port-name'] = options['boot-storage-wwpn']
    elif options['boot-network-nic'] is not None:
        nic_name = options['boot-network-nic']
        try:
            nic = partition.nics.find(name=nic_name)
        except zhmcclient.NotFound:
            raise_click_exception("Could not find NIC %s in partition %s in "
                                  "CPC %s." %
                                  (nic_name, partition_name, cpc_name),
                                  cmd_ctx.error_format)
        properties['boot-device'] = 'network-adapter'
        properties['boot-network-device'] = nic.uri
    elif any([options[name] for name in required_ftp_option_names]):
        missing_option_names = [name for name in required_ftp_option_names
                                if options[name] is None]
        if missing_option_names:
            raise_click_exception("Boot from FTP server specified, but misses "
                                  "the following options: %s" %
                                  ', '.join(missing_option_names),
                                  cmd_ctx.error_format)
        properties['boot-device'] = 'ftp'
        properties['boot-ftp-host'] = options['boot-ftp-host']
        properties['boot-ftp-username'] = options['boot-ftp-username']
        properties['boot-ftp-password'] = options['boot-ftp-password']
        properties['boot-ftp-insfile'] = options['boot-ftp-insfile']
    elif options['boot-media-file'] is not None:
        properties['boot-device'] = 'removable-media'
        properties['boot-removable-media'] = options['boot-media-file']
    elif options['boot-iso'] is not None:
        properties['boot-device'] = 'iso-image'
    else:
        # boot-device="none" is the default
        pass

    if options['ssc-dns-servers'] is not None:
        properties['ssc-dns-servers'] = options['ssc-dns-servers'].split(',')

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating partition %s." %
                   partition_name)
        return

    try:
        partition.update_properties(properties)
    except zhmcclient.Error as exc:
        raise_click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != partition_name:
        click.echo("Partition %s has been renamed to %s and was updated." %
                   (partition_name, properties['name']))
    else:
        click.echo("Partition %s has been updated." % partition_name)


def cmd_partition_delete(cmd_ctx, cpc_name, partition_name):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    try:
        partition.delete()
    except zhmcclient.Error as exc:
        raise_click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo('Partition %s has been deleted.' % partition_name)


def cmd_partition_console(cmd_ctx, cpc_name, partition_name, options):

    logger = logging.getLogger(zhmcclient.CONSOLE_LOGGER_NAME)

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    refresh = options['refresh']

    cmd_ctx.spinner.stop()

    try:
        part_console(cmd_ctx.session, partition, refresh, logger)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))


def cmd_partition_mount_iso(cmd_ctx, cpc_name, partition_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    image_file = options['imagefile']
    image_fp = open(image_file, 'rb')
    path, image_name = os.path.split(image_file)
    partition.mount_iso_image(image_fp, image_name, options['imageinsfile'])
    if options['boot']:
        partition.update_properties({'boot-device': 'iso-image'})
    cmd_ctx.spinner.stop()
    click.echo('ISO image %s has been mounted to Partition %s.' %
               (image_name, partition.name))


def cmd_partition_unmount_iso(cmd_ctx, cpc_name, partition_name):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    partition.pull_full_properties()
    image_name = partition.get_property('boot-iso-image-name')
    if image_name:
        boot_device = partition.get_property('boot-device')
        if boot_device == 'iso-image':
            partition.update_properties({'boot-device': 'none'})
        partition.unmount_iso_image()
        cmd_ctx.spinner.stop()
        click.echo('ISO image %s has been unmounted from Partition %s.' %
                   (image_name, partition.name))
    else:
        cmd_ctx.spinner.stop()
        click.echo('No ISO image is mounted to Partition %s.' % partition.name)
