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
from ._helper import print_properties, print_resources, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR
from ._cmd_cpc import find_cpc


def find_vswitch(client, cpc_name, vswitch_name):
    """
    Find a virtual switch by name and return its resource object.
    """
    cpc = find_cpc(client, cpc_name)
    # The CPC must be in DPM mode. We don't check that because it would
    # cause a GET to the CPC resource that we otherwise don't need.
    try:
        vswitch = cpc.virtual_switches.find(name=vswitch_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find virtual switch %s in "
                                   "CPC %s." % (vswitch_name, cpc_name))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return vswitch


@cli.group('vswitch', options_metavar=COMMAND_OPTIONS_METAVAR)
def vswitch_group():
    """
    Command group for managing virtual switches.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@vswitch_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--adapter', is_flag=True, required=False,
              help='Show additional properties for the backing adapter.')
@click.option('--uri', is_flag=True, required=False,
              help='Show additional properties for the resource URI.')
@click.pass_obj
def vswitch_list(cmd_ctx, cpc, **options):
    """
    List the virtual switches in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vswitch_list(cmd_ctx, cpc, options))


@vswitch_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('VSWITCH', type=str, metavar='VSWITCH')
@click.pass_obj
def vswitch_show(cmd_ctx, cpc, vswitch):
    """
    Show the details of a virtual switch.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vswitch_show(cmd_ctx, cpc, vswitch))


@vswitch_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('VSWITCH', type=str, metavar='VSWITCH')
@click.option('--name', type=str, required=False,
              help='The new name of the virtual switch.')
@click.option('--description', type=str, required=False,
              help='The new description of the virtual switch.')
@click.pass_obj
def vswitch_update(cmd_ctx, cpc, vswitch, **options):
    """
    Update the properties of a virtual switch.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vswitch_update(cmd_ctx, cpc, vswitch,
                                                   options))


def cmd_vswitch_list(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    try:
        vswitches = cpc.virtual_switches.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    show_list = [
        'name',
    ]
    if options['adapter']:
        show_list.extend([
            'type',  # part of list()
            'port',  # needs to be retrieved
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])
    print_resources(vswitches, cmd_ctx.output_format, show_list)


def cmd_vswitch_show(cmd_ctx, cpc_name, vswitch_name):

    client = zhmcclient.Client(cmd_ctx.session)
    vswitch = find_vswitch(client, cpc_name, vswitch_name)

    try:
        vswitch.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    print_properties(vswitch.properties, cmd_ctx.output_format)


def cmd_vswitch_update(cmd_ctx, cpc_name, vswitch_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    vswitch = find_vswitch(client, cpc_name, vswitch_name)

    options = original_options(options)
    properties = options_to_properties(options)

    if not properties:
        click.echo("No properties specified for updating virtual switch %s." %
                   vswitch_name)
        return

    try:
        vswitch.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    if 'name' in properties and properties['name'] != vswitch_name:
        click.echo("Virtual switch %s has been renamed to %s and was "
                   "updated." % (vswitch_name, properties['name']))
    else:
        click.echo("Virtual switch %s has been updated." % vswitch_name)
