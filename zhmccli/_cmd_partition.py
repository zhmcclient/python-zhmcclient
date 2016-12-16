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

from __future__ import absolute_import

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR
from ._cmd_cpc import find_cpc


def find_partition(client, cpc_name, partition_name):
    """
    Find a partition by name and return its resource object.
    """
    cpc = find_cpc(client, cpc_name)
    # The CPC must be in DPM mode. We don't check that because it would
    # cause a GET to the CPC resource that we otherwise don't need.
    try:
        partition = cpc.partitions.find(name=partition_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find partition %s in CPC %s." %
                                   (partition_name, cpc_name))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
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
              'Default: 0')
@click.option('--ifl-processors', type=int, required=False,
              help='The number of IFL processors. '
              'Default: 0')
@click.option('--processor-mode', type=click.Choice(['dedicated', 'shared']),
              required=False,
              help='The sharing mode for processors. '
              'Default: shared')
@click.option('--initial-memory', type=int, required=False,
              help='The initial amount of memory (in MiB) when the partition '
              'is started. '
              'Default: 1024 MiB')
@click.option('--maximum-memory', type=int, required=False,
              help='The maximum amount of memory (in MiB) while the partition '
              'is running. '
              'Default: 1024 MiB')
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
@click.option('--yes', is_flag=True, callback=abort_if_false,
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


def cmd_partition_list(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    try:
        partitions = cpc.partitions.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

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
    print_resources(partitions, cmd_ctx.output_format, show_list)


def cmd_partition_show(cmd_ctx, cpc_name, partition_name):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(client, cpc_name, partition_name)

    try:
        partition.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    print_properties(partition.properties, cmd_ctx.output_format)


def cmd_partition_start(cmd_ctx, cpc_name, partition_name):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(client, cpc_name, partition_name)

    try:
        partition.start(wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    click.echo('Partition %s has been started.' % partition_name)


def cmd_partition_stop(cmd_ctx, cpc_name, partition_name):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(client, cpc_name, partition_name)

    try:
        partition.stop(wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    click.echo('Partition %s has been stopped.' % partition_name)


def cmd_partition_create(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

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
            raise click.ClickException("Boot from FTP server specified, but "
                                       "misses the following options: %s" %
                                       ', '.join(missing_option_names))
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

    try:
        new_partition = cpc.partitions.create(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    click.echo("New partition %s has been created." %
               new_partition.properties['name'])


def cmd_partition_update(cmd_ctx, cpc_name, partition_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(client, cpc_name, partition_name)

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
            raise click.ClickException("Boot from FCP LUN specified, but "
                                       "misses the following options: %s" %
                                       ', '.join(missing_option_names))
        hba_name = options['boot-storage-hba']
        try:
            hba = partition.hbas.find(name=hba_name)
        except zhmcclient.NotFound:
            raise click.ClickException("Could not find HBA %s in partition "
                                       "%s in CPC %s." %
                                       (hba_name, partition_name, cpc_name))
        properties['boot-device'] = 'storage-adapter'
        properties['boot-storage-device'] = hba.uri
        properties['boot-logical-unit-number'] = options['boot-storage-lun']
        properties['boot-world-wide-port-name'] = options['boot-storage-wwpn']
    elif options['boot-network-nic'] is not None:
        nic_name = options['boot-network-nic']
        try:
            nic = partition.nics.find(name=nic_name)
        except zhmcclient.NotFound:
            raise click.ClickException("Could not find NIC %s in partition "
                                       "%s in CPC %s." %
                                       (nic_name, partition_name, cpc_name))
        properties['boot-device'] = 'network-adapter'
        properties['boot-network-device'] = nic.uri
    elif any([options[name] for name in required_ftp_option_names]):
        missing_option_names = [name for name in required_ftp_option_names
                                if options[name] is None]
        if missing_option_names:
            raise click.ClickException("Boot from FTP server specified, but "
                                       "misses the following options: %s" %
                                       ', '.join(missing_option_names))
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

    if not properties:
        click.echo("No properties specified for updating partition %s." %
                   partition_name)
        return

    try:
        partition.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    if 'name' in properties and properties['name'] != partition_name:
        click.echo("Partition %s has been renamed to %s and was updated." %
                   (partition_name, properties['name']))
    else:
        click.echo("Partition %s has been updated." % partition_name)


def cmd_partition_delete(cmd_ctx, cpc_name, partition_name):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(client, cpc_name, partition_name)

    try:
        partition.delete()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    click.echo('Partition %s has been deleted.' % partition_name)
