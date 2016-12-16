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


def find_adapter(client, cpc_name, adapter_name):
    """
    Find an adapter by name and return its resource object.
    """
    cpc = find_cpc(client, cpc_name)
    # The CPC must be in DPM mode. We don't check that because it would
    # cause a GET to the CPC resource that we otherwise don't need.
    try:
        adapter = cpc.adapters.find(name=adapter_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find adapter %s in CPC %s." %
                                   (adapter_name, cpc_name))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return adapter


@cli.group('adapter', options_metavar=COMMAND_OPTIONS_METAVAR)
def adapter_group():
    """
    Command group for managing adapters.

    Physical adapters (e.g. OSA, FICON) are auto-discovered and cannot be
    created. Logical adapters (HiperSockets) can be created and deleted.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@adapter_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--type', is_flag=True, required=False,
              help='Show additional properties for the adapter family and '
              'type.')
@click.option('--uri', is_flag=True, required=False,
              help='Show additional properties for the resource URI.')
@click.pass_obj
def adapter_list(cmd_ctx, cpc, **options):
    """
    List the adapters in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_adapter_list(cmd_ctx, cpc, options))


@adapter_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('ADAPTER', type=str, metavar='ADAPTER')
@click.pass_obj
def adapter_show(cmd_ctx, cpc, adapter):
    """
    Show the details of an adapter.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_adapter_show(cmd_ctx, cpc, adapter))


@adapter_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('ADAPTER', type=str, metavar='ADAPTER')
@click.option('--name', type=str, required=False,
              help='The new name of the adapter.')
@click.option('--description', type=str, required=False,
              help='The new description of the adapter.')
@click.option('--port-description', type=str, required=False,
              help='The new description of the single port of the adapter.')
@click.option('--mtu-size', type=click.Choice(['8', '16', '32', '56']),
              required=False,
              help='The new MTU size of the adapter in KiB. '
              '(HiperSockets only).')
@click.option('--allowed-capacity', type=int, required=False,
              help='The maximum number of HBAs per partition. '
              '(FCP only).')
@click.option('--chpid', type=str, required=False,
              help='Channel path ID (CHPID, 2 hex chars) used by the '
              'adapter\'s port. '
              '(OSA, FICON, HiperSockets only).')
@click.option('--crypto-number', type=int, required=False,
              help='Identifier of the crypto adapter in the range 0-15 '
              'Must be unique within the CPC. '
              '(Crypto only).')
@click.option('--crypto-tke/--no-crypto-tke', default=None, required=False,
              help='Permit TKE commands on the crypto adapter. '
              '(Crypto only).')
@click.pass_obj
def adapter_update(cmd_ctx, cpc, adapter, **options):
    """
    Update the properties of an adapter.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    The adapter may be a physical adapter (e.g. a discovered OSA card) or a
    logical adapter (e.g. HiperSockets).

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_adapter_update(cmd_ctx, cpc, adapter,
                                                   options))


@adapter_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--name', type=str, required=True,
              help='The name of the new adapter.')
@click.option('--description', type=str, required=False,
              help='The description of the new adapter.')
@click.option('--port-description', type=str, required=False,
              help='The description of the (single) port of the new adapter.')
@click.option('--mtu-size', type=click.Choice(['8', '16', '32', '56']),
              required=False,
              help='The MTU size of the new adapter in KiB.')
@click.pass_obj
def adapter_create_hipersocket(cmd_ctx, cpc, **options):
    """
    Create a HiperSockets adapter in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.

    Some more properties of the new HiperSockets adapter can be set via
    adapter update.
    """
    cmd_ctx.execute_cmd(lambda: cmd_adapter_create_hipersocket(
                        cmd_ctx, cpc, options))


@adapter_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('ADAPTER', type=str, metavar='ADAPTER')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the adapter.',
              prompt='Are you sure you want to delete this adapter ?')
@click.pass_obj
def adapter_delete_hipersocket(cmd_ctx, cpc, adapter):
    """
    Delete a HiperSockets adapter.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_adapter_delete_hipersocket(
                        cmd_ctx, cpc, adapter))


def cmd_adapter_list(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    try:
        adapters = cpc.adapters.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    show_list = [
        'name',
        'adapter-id',
        'status',
    ]
    if options['type']:
        show_list.extend([
            'adapter-family',
            'type',
            'detected-card-type',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])
    print_resources(adapters, cmd_ctx.output_format, show_list)


def cmd_adapter_show(cmd_ctx, cpc_name, adapter_name):

    client = zhmcclient.Client(cmd_ctx.session)
    adapter = find_adapter(client, cpc_name, adapter_name)

    try:
        adapter.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    print_properties(adapter.properties, cmd_ctx.output_format)


def cmd_adapter_update(cmd_ctx, cpc_name, adapter_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    adapter = find_adapter(client, cpc_name, adapter_name)

    name_map = {
        'mtu-size': 'maximum-transmission-unit-size',
        'chpid': 'channel-path-id',
        'crypto-tke': 'tke-commands-enabled',
    }
    options = original_options(options)
    properties = options_to_properties(options, name_map)

    if not properties:
        click.echo("No properties specified for updating adapter %s." %
                   adapter_name)
        return

    try:
        adapter.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    if 'name' in properties and properties['name'] != adapter_name:
        click.echo("Adapter %s has been renamed to %s and was updated." %
                   (adapter_name, properties['name']))
    else:
        click.echo("Adapter %s has been updated." % adapter_name)


def cmd_adapter_create_hipersocket(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    name_map = {
        'mtu-size': 'maximum-transmission-unit-size',
    }
    options = original_options(options)
    properties = options_to_properties(options, name_map)

    try:
        new_adapter = cpc.adapters.create_hipersocket(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    click.echo("New HiperSockets adapter %s has been created." %
               new_adapter.properties['name'])


def cmd_adapter_delete_hipersocket(cmd_ctx, cpc_name, adapter_name):

    client = zhmcclient.Client(cmd_ctx.session)
    adapter = find_adapter(client, cpc_name, adapter_name)

    try:
        adapter.delete()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    click.echo('HiperSockets adapter %s has been deleted.' % adapter_name)
