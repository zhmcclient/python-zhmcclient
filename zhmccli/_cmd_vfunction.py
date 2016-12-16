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


def find_vfunction(client, cpc_name, partition_name, vfunction_name):
    """
    Find a virtual function by name and return its resource object.
    """
    partition = find_partition(client, cpc_name, partition_name)
    try:
        vfunction = partition.virtual_functions.find(name=vfunction_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find virtual function %s in "
                                   "partition %s in CPC %s." %
                                   (vfunction_name, partition_name, cpc_name))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return vfunction


@cli.group('vfunction', options_metavar=COMMAND_OPTIONS_METAVAR)
def vfunction_group():
    """
    Command group for managing virtual functions.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@vfunction_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--uri', is_flag=True, required=False,
              help='Show additional properties for the resource URI.')
@click.pass_obj
def vfunction_list(cmd_ctx, cpc, partition, **options):
    """
    List the virtual functions in a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vfunction_list(cmd_ctx, cpc, partition,
                                                   options))


@vfunction_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('VFUNCTION', type=str, metavar='VFUNCTION')
@click.pass_obj
def vfunction_show(cmd_ctx, cpc, partition, vfunction):
    """
    Show the details of a virtual function.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vfunction_show(cmd_ctx, cpc, partition,
                                                   vfunction))


@vfunction_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--name', type=str, required=True,
              help='The name of the new virtual function. Must be unique '
              'within the virtual functions of the partition')
@click.option('--description', type=str, required=False,
              help='The description of the new virtual function. '
              'Default: empty')
@click.option('--adapter', type=str, required=True,
              help='The name of the adapter backing the virtual function.')
@click.option('--device-number', type=str, required=False,
              help='The device number to be used for the new virtual '
              'function. Default: auto-generated')
@click.pass_obj
def vfunction_create(cmd_ctx, cpc, partition, **options):
    """
    Create a virtual function in a partition.

    This assigns a virtual function of an adapter to a partition, creating
    a named virtual function resource within that partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vfunction_create(cmd_ctx, cpc, partition,
                                                     options))


@vfunction_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('VFUNCTION', type=str, metavar='VFUNCTION')
@click.option('--name', type=str, required=False,
              help='The new name of the virtual function. Must be unique '
              'within the virtual functions of the partition.')
@click.option('--description', type=str, required=False,
              help='The new description of the virtual function.')
@click.option('--adapter', type=str, required=False,
              help='The name of the new adapter (in the same CPC) that will '
              'back the virtual function.')
@click.option('--device-number', type=str, required=False,
              help='The new device number to be used for the virtual '
              'function.')
@click.pass_obj
def vfunction_update(cmd_ctx, cpc, partition, vfunction, **options):
    """
    Update the properties of a virtual function.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vfunction_update(cmd_ctx, cpc, partition,
                                                     vfunction, options))


@vfunction_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('VFUNCTION', type=str, metavar='VFUNCTION')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the virtual function.',
              prompt='Are you sure you want to delete this virtual function ?')
@click.pass_obj
def vfunction_delete(cmd_ctx, cpc, partition, vfunction):
    """
    Delete a virtual function.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vfunction_delete(cmd_ctx, cpc, partition,
                                                     vfunction))


def cmd_vfunction_list(cmd_ctx, cpc_name, partition_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(client, cpc_name, partition_name)

    try:
        vfunctions = partition.virtual_functions.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    show_list = [
        'name',
    ]
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])
    print_resources(vfunctions, cmd_ctx.output_format, show_list)


def cmd_vfunction_show(cmd_ctx, cpc_name, partition_name, vfunction_name):

    client = zhmcclient.Client(cmd_ctx.session)
    vfunction = find_vfunction(client, cpc_name, partition_name,
                               vfunction_name)

    try:
        vfunction.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    print_properties(vfunction.properties, cmd_ctx.output_format)


def cmd_vfunction_create(cmd_ctx, cpc_name, partition_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(client, cpc_name, partition_name)

    name_map = {
        # The following options are handled in this function:
        'adapter': None,
    }
    options = original_options(options)
    properties = options_to_properties(options, name_map)

    adapter_name = options['adapter']
    try:
        adapter = partition.cpc.adapters.find(name=adapter_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find adapter %s in CPC %s." %
                                   (adapter_name, cpc_name))
    properties['adapter-uri'] = adapter.uri

    try:
        new_vfunction = partition.virtual_functions.create(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    click.echo("New virtual function %s has been created." %
               new_vfunction.properties['name'])


def cmd_vfunction_update(cmd_ctx, cpc_name, partition_name, vfunction_name,
                         options):

    client = zhmcclient.Client(cmd_ctx.session)
    vfunction = find_vfunction(client, cpc_name, partition_name,
                               vfunction_name)

    name_map = {
        # The following options are handled in this function:
        'adapter': None,
    }
    options = original_options(options)
    properties = options_to_properties(options, name_map)

    if options['adapter'] is not None:
        adapter_name = options['adapter']
        try:
            adapter = vfunction.partition.cpc.adapters.find(name=adapter_name)
        except zhmcclient.NotFound:
            raise click.ClickException("Could not find adapter %s in CPC %s." %
                                       (adapter_name, cpc_name))
        properties['adapter-uri'] = adapter.uri

    if not properties:
        click.echo("No properties specified for updating virtual function "
                   "%s." % vfunction_name)
        return

    try:
        vfunction.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    if 'name' in properties and properties['name'] != vfunction_name:
        click.echo("Virtual function %s has been renamed to %s and was "
                   "updated." % (vfunction_name, properties['name']))
    else:
        click.echo("Virtual function %s has been updated." % vfunction_name)


def cmd_vfunction_delete(cmd_ctx, cpc_name, partition_name, vfunction_name):

    client = zhmcclient.Client(cmd_ctx.session)
    vfunction = find_vfunction(client, cpc_name, partition_name,
                               vfunction_name)

    try:
        vfunction.delete()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    click.echo('Virtual function %s has been deleted.' % vfunction_name)
