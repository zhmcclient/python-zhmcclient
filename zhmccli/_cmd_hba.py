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


def find_hba(client, cpc_name, partition_name, hba_name):
    """
    Find an HBA by name and return its resource object.
    """
    partition = find_partition(client, cpc_name, partition_name)
    try:
        hba = partition.hbas.find(name=hba_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find HBA %s in partition %s in "
                                   "CPC %s." %
                                   (hba_name, partition_name, cpc_name))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return hba


@cli.group('hba', options_metavar=COMMAND_OPTIONS_METAVAR)
def hba_group():
    """
    Command group for managing HBAs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@hba_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--uri', is_flag=True, required=False,
              help='Show additional properties for the resource URI.')
@click.pass_obj
def hba_list(cmd_ctx, cpc, partition, **options):
    """
    List the HBAs in a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_hba_list(cmd_ctx, cpc, partition, options))


@hba_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('HBA', type=str, metavar='HBA')
@click.pass_obj
def hba_show(cmd_ctx, cpc, partition, hba):
    """
    Show the details of an HBA.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_hba_show(cmd_ctx, cpc, partition, hba))


@hba_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--name', type=str, required=True,
              help='The name of the new HBA.')
@click.option('--description', type=str, required=False,
              help='The description of the new HBA. '
              'Default: empty')
@click.option('--adapter', type=str, required=True,
              help='The name of the backing FCP adapter.')
@click.option('--port', type=str, required=True,
              help='The name of the port on the backing FCP adapter.')
@click.option('--device-number', type=str, required=False,
              help='The device number to be used for the new HBA. '
              'Default: auto-generated')
@click.pass_obj
def hba_create(cmd_ctx, cpc, partition, **options):
    """
    Create an HBA in a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_hba_create(cmd_ctx, cpc, partition,
                                               options))


@hba_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('HBA', type=str, metavar='HBA')
@click.option('--name', type=str, required=False,
              help='The new name of the HBA.')
@click.option('--description', type=str, required=False,
              help='The new description of the HBA.')
@click.option('--device-number', type=str, required=False,
              help='The new device number to be used for the HBA.')
@click.pass_obj
def hba_update(cmd_ctx, cpc, partition, hba, **options):
    """
    Update the properties of an HBA.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_hba_update(cmd_ctx, cpc, partition, hba,
                                               options))


@hba_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('HBA', type=str, metavar='HBA')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the HBA.',
              prompt='Are you sure you want to delete this HBA ?')
@click.pass_obj
def hba_delete(cmd_ctx, cpc, partition, hba):
    """
    Delete an HBA.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_hba_delete(cmd_ctx, cpc, partition, hba))


def cmd_hba_list(cmd_ctx, cpc_name, partition_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(client, cpc_name, partition_name)

    try:
        hbas = partition.hbas.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    show_list = [
        'name',
    ]
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])
    print_resources(hbas, cmd_ctx.output_format, show_list)


def cmd_hba_show(cmd_ctx, cpc_name, partition_name, hba_name):

    client = zhmcclient.Client(cmd_ctx.session)
    hba = find_hba(client, cpc_name, partition_name, hba_name)

    try:
        hba.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    print_properties(hba.properties, cmd_ctx.output_format)


def cmd_hba_create(cmd_ctx, cpc_name, partition_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(client, cpc_name, partition_name)

    name_map = {
        # The following options are handled in this function:
        'adapter': None,
        'port': None,
    }
    options = original_options(options)
    properties = options_to_properties(options, name_map)

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
    properties['adapter-port'] = port.uri

    try:
        new_hba = partition.hbas.create(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    click.echo("New HBA %s has been created." %
               new_hba.properties['name'])


def cmd_hba_update(cmd_ctx, cpc_name, partition_name, hba_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    hba = find_hba(client, cpc_name, partition_name, hba_name)

    options = original_options(options)
    properties = options_to_properties(options)

    if not properties:
        click.echo("No properties specified for updating HBA %s." % hba_name)
        return

    try:
        hba.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    if 'name' in properties and properties['name'] != hba_name:
        click.echo("HBA %s has been renamed to %s and was updated." %
                   (hba_name, properties['name']))
    else:
        click.echo("HBA %s has been updated." % hba_name)


def cmd_hba_delete(cmd_ctx, cpc_name, partition_name, hba_name):

    client = zhmcclient.Client(cmd_ctx.session)
    hba = find_hba(client, cpc_name, partition_name, hba_name)

    try:
        hba.delete()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    click.echo('HBA %s has been deleted.' % hba_name)
