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
    options_to_properties, original_options
from ._cmd_adapter import find_adapter


# TODO: Add "update" using new approach from partition.


def find_port(client, cpc_name, adapter_name, port_name):
    """
    Find a port by name and return its resource object.
    """
    adapter = find_adapter(client, cpc_name, adapter_name)
    try:
        port = adapter.ports.find(name=port_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find port %s in adapter %s in "
                                   "CPC %s." %
                                   (port_name, adapter_name, cpc_name))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return port


@cli.group('port')
def port_group():
    """
    Command group for managing adapter ports.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """


@port_group.command('list')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('ADAPTER-NAME', type=str, metavar='ADAPTER-NAME')
@click.pass_obj
def port_list(cmd_ctx, cpc_name, adapter_name):
    """
    List the ports of an adapter.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_port_list(cmd_ctx, cpc_name, adapter_name))


@port_group.command('show')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('ADAPTER-NAME', type=str, metavar='ADAPTER-NAME')
@click.argument('PORT-NAME', type=str, metavar='PORT-NAME')
@click.pass_obj
def port_show(cmd_ctx, cpc_name, adapter_name, port_name):
    """
    Show the details of an adapter port.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_port_show(cmd_ctx, cpc_name, adapter_name,
                                              port_name))


@port_group.command('update')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('ADAPTER-NAME', type=str, metavar='ADAPTER-NAME')
@click.argument('PORT-NAME', type=str, metavar='PORT-NAME')
@click.option('--description', type=str, required=False,
              help='The new description of the port.')
@click.pass_obj
def port_update(cmd_ctx, cpc_name, adapter_name, port_name, **options):
    """
    Update the properties of an adapter port.

    The port may be on a physical adapter (e.g. a discovered OSA card) or a
    logical adapter (e.g. HiperSockets).

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_port_update(
                        cmd_ctx, cpc_name, adapter_name, port_name, options))


def cmd_port_list(cmd_ctx, cpc_name, adapter_name):
    client = zhmcclient.Client(cmd_ctx.session)
    adapter = _find_adapter(client, cpc_name, adapter_name)
    try:
        ports = adapter.ports.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    print_resources(ports, cmd_ctx.output_format)


def cmd_port_show(cmd_ctx, cpc_name, adapter_name, port_name):
    client = zhmcclient.Client(cmd_ctx.session)
    port = _find_port(client, cpc_name, adapter_name, port_name)
    try:
        port.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    skip_list = ()
    print_properties(port.properties, cmd_ctx.output_format, skip_list)


def cmd_port_update(cmd_ctx, cpc_name, adapter_name, port_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    port = find_port(client, cpc_name, adapter_name, port_name)

    options = original_options(options)
    properties = options_to_properties(options)

    if not properties:
        click.echo("No properties specified for updating port %s." % port_name)
        return

    try:
        port.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    # Adapter ports cannot be renamed.
    click.echo("Port %s has been updated." % port_name)

