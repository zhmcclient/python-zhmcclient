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
from ._cmd_partition import find_partition


def find_nic(client, cpc_name, partition_name, nic_name):
    """
    Find a NIC by name and return its resource object.
    """
    partition = find_partition(client, cpc_name, partition_name)
    try:
        nic = partition.nics.find(name=nic_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find NIC %s in partition %s in "
                                   "CPC %s." %
                                   (nic_name, partition_name, cpc_name))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return nic


@cli.group('nic', options_metavar=COMMAND_OPTIONS_METAVAR)
def nic_group():
    """
    Command group for managing NICs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@nic_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--type', is_flag=True, required=False,
              help='Show additional properties for the NIC type.')
@click.option('--uri', is_flag=True, required=False,
              help='Show additional properties for the resource URI.')
@click.pass_obj
def nic_list(cmd_ctx, cpc, partition, **options):
    """
    List the NICs in a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_nic_list(cmd_ctx, cpc, partition, options))


@nic_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('NIC', type=str, metavar='NIC')
@click.pass_obj
def nic_show(cmd_ctx, cpc, partition, nic):
    """
    Show the details of a NIC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_nic_show(cmd_ctx, cpc, partition, nic))


@nic_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--name', type=str, required=True,
              help='The name of the new NIC.')
@click.option('--description', type=str, required=False,
              help='The description of the new NIC. '
              'Default: empty')
@click.option('--adapter', type=str, required=False,
              help='The name of the network adapter with the port backing the '
              'new NIC. '
              'Required for ROCE adapters')
@click.option('--port', type=str, required=False,
              help='The name of the network port backing the new NIC. '
              'Required for ROCE adapters')
@click.option('--virtual-switch', type=str, required=False,
              help='The name of the virtual switch of the network port '
              'backing the new NIC. '
              'Required for OSA and HiperSocket adapters')
@click.option('--device-number', type=str, required=False,
              help='The device number to be used for the new NIC. '
              'Default: auto-generated')
@click.pass_obj
def nic_create(cmd_ctx, cpc, partition, **options):
    """
    Create a NIC in a partition.

    The NIC is backed by a port (jack) on an adapter. For OSA and HiperSocket
    adapters, this backing is defined by associating the NIC with the virtual
    switch of the adapter port. For ROCE adapters, this backing is defined
    by associating the NIC with the network adapter port directly.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_nic_create(cmd_ctx, cpc, partition,
                                               options))


@nic_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('NIC', type=str, metavar='NIC')
@click.option('--name', type=str, required=False,
              help='The new name of the NIC.')
@click.option('--description', type=str, required=False,
              help='The new description of the NIC.')
@click.option('--adapter', type=str, required=False,
              help='The name of the new network adapter with the port backing '
              'the NIC. '
              'Only for ROCE adapters'
              'Default: No change.')
@click.option('--port', type=str, required=False,
              help='The name of the new network port backing the NIC. '
              'Only for ROCE adapters'
              'Default: No change.')
@click.option('--virtual-switch', type=str, required=False,
              help='The name of the virtual switch of the new network port '
              'backing the NIC. '
              'Only for OSA and HiperSocket adapters.')
@click.option('--device-number', type=str, required=False,
              help='The new device number to be used for the NIC.')
@click.pass_obj
def nic_update(cmd_ctx, cpc, partition, nic, **options):
    """
    Update the properties of a NIC.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_nic_update(cmd_ctx, cpc, partition, nic,
                                               options))


@nic_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('NIC', type=str, metavar='NIC')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the NIC.',
              prompt='Are you sure you want to delete this NIC ?')
@click.pass_obj
def nic_delete(cmd_ctx, cpc, partition, nic):
    """
    Delete a NIC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_nic_delete(cmd_ctx, cpc, partition, nic))


def cmd_nic_list(cmd_ctx, cpc_name, partition_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(client, cpc_name, partition_name)

    try:
        nics = partition.nics.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    show_list = [
        'name',
    ]
    if options['type']:
        show_list.extend([
            'type',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])
    print_resources(nics, cmd_ctx.output_format, show_list)


def cmd_nic_show(cmd_ctx, cpc_name, partition_name, nic_name):

    client = zhmcclient.Client(cmd_ctx.session)
    nic = find_nic(client, cpc_name, partition_name, nic_name)

    try:
        nic.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    print_properties(nic.properties, cmd_ctx.output_format)


def cmd_nic_create(cmd_ctx, cpc_name, partition_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(client, cpc_name, partition_name)

    name_map = {
        # The following options are handled in this function:
        'adapter': None,
        'port': None,
        'virtual-switch': None,
    }
    options = original_options(options)
    properties = options_to_properties(options, name_map)

    required_roce_option_names = (
        'adapter',
        'port')
    if any([options[name] for name in required_roce_option_names]):
        missing_option_names = [name for name in required_roce_option_names
                                if options[name] is None]
        if missing_option_names:
            raise click.ClickException("ROCE adapter specified, but "
                                       "misses the following options: %s" %
                                       ', '.join(missing_option_names))

        adapter_name = options['adapter']
        try:
            adapter = partition.cpc.adapters.find(name=adapter_name)
        except zhmcclient.NotFound:
            raise click.ClickException("Could not find adapter %s in CPC %s." %
                                       (adapter_name, cpc_name))
        port_name = options['port']
        try:
            port = adapter.ports.find(name=port_name)
        except zhmcclient.NotFound:
            raise click.ClickException("Could not find port %s on adapter %s "
                                       "in CPC %s." %
                                       (port_name, adapter_name, cpc_name))
        properties['network-adapter-port-uri'] = port.uri

    elif options['virtual-switch'] is not None:
        vswitch_name = options['virtual-switch']
        try:
            vswitch = partition.cpc.virtual_switches.find(name=vswitch_name)
        except zhmcclient.NotFound:
            raise click.ClickException("Could not find virtual switch %s "
                                       "in CPC %s." %
                                       (vswitch_name, cpc_name))
        properties['virtual-switch-uri'] = vswitch.uri
    else:
        raise click.ClickException("No backing adapter port or virtual switch "
                                   "specified.")

    try:
        new_nic = partition.nics.create(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    click.echo("New NIC %s has been created." %
               new_nic.properties['name'])


def cmd_nic_update(cmd_ctx, cpc_name, partition_name, nic_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    nic = find_nic(client, cpc_name, partition_name, nic_name)

    name_map = {
        # The following options are handled in this function:
        'adapter': None,
        'port': None,
        'virtual-switch': None,
    }
    options = original_options(options)
    properties = options_to_properties(options, name_map)

    required_roce_option_names = (
        'adapter',
        'port')
    if any([options[name] for name in required_roce_option_names]):
        missing_option_names = [name for name in required_roce_option_names
                                if options[name] is None]
        if missing_option_names:
            raise click.ClickException("ROCE adapter specified, but "
                                       "misses the following options: %s" %
                                       ', '.join(missing_option_names))

        adapter_name = options['adapter']
        try:
            adapter = nic.partition.cpc.adapters.find(name=adapter_name)
        except zhmcclient.NotFound:
            raise click.ClickException("Could not find adapter %s in CPC %s." %
                                       (adapter_name, cpc_name))
        port_name = options['port']
        try:
            port = adapter.ports.find(name=port_name)
        except zhmcclient.NotFound:
            raise click.ClickException("Could not find port %s on adapter %s "
                                       "in CPC %s." %
                                       (port_name, adapter_name, cpc_name))
        properties['network-adapter-port-uri'] = port.uri

    elif options['virtual-switch'] is not None:
        vswitch_name = options['virtual-switch']
        try:
            vswitch = nic.partition.cpc.virtual_switches.find(
                name=vswitch_name)
        except zhmcclient.NotFound:
            raise click.ClickException("Could not find virtual switch %s "
                                       "in CPC %s." %
                                       (vswitch_name, cpc_name))
        properties['virtual-switch-uri'] = vswitch.uri
    else:
        # The backing adapter port or virtual switch is not being updated.
        pass

    if not properties:
        click.echo("No properties specified for updating NIC %s." % nic_name)
        return

    try:
        nic.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    if 'name' in properties and properties['name'] != nic_name:
        click.echo("NIC %s has been renamed to %s and was updated." %
                   (nic_name, properties['name']))
    else:
        click.echo("NIC %s has been updated." % nic_name)


def cmd_nic_delete(cmd_ctx, cpc_name, partition_name, nic_name):

    client = zhmcclient.Client(cmd_ctx.session)
    nic = find_nic(client, cpc_name, partition_name, nic_name)

    try:
        nic.delete()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    click.echo('NIC %s has been deleted.' % nic_name)
