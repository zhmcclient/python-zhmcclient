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


def find_cpc(client, cpc_name):
    """
    Find a CPC by name and return its resource object.
    """
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find CPC %s on HMC %s." %
                                   (cpc_name, client.session.host))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return cpc


@cli.group('cpc', options_metavar=COMMAND_OPTIONS_METAVAR)
def cpc_group():
    """
    Command group for managing CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@cpc_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--type', is_flag=True, required=False,
              help='Show additional properties for CPC mode / type.')
@click.option('--mach', is_flag=True, required=False,
              help='Show additional properties with machine information.')
@click.option('--uri', is_flag=True, required=False,
              help='Show additional properties for the resource URI.')
@click.pass_obj
def cpc_list(cmd_ctx, **options):
    """
    List the CPCs managed by the HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_list(cmd_ctx, options))


@cpc_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def cpc_show(cmd_ctx, cpc):
    """
    Show details of a CPC.

    Limitations:
      * In table format, the following properties are not shown:
        - ec-mcl-description
        - cpc-power-saving-state
        - network2-ipv6-info
        - network1-ipv6-info
        - auto-start-list

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_show(cmd_ctx, cpc))


@cpc_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--description', type=str, required=False,
              help='The new description of the CPC. '
              '(DPM mode only).')
@click.option('--acceptable-status', type=str, required=False,
              help='The new set of acceptable operational status values.')
# TODO: Support multiple values for acceptable-status
@click.option('--next-activation-profile', type=str, required=False,
              help='The name of the new next reset activation profile. '
              '(not in DPM mode).')
@click.option('--processor-time-slice', type=int, required=False,
              help='The new time slice (in ms) for logical processors. '
              'A value of 0 causes the time slice to be dynamically '
              'determined by the system. A positive value causes a constant '
              'time slice to be used. '
              '(not in DPM mode).')
@click.option('--wait-ends-slice/--no-wait-ends-slice', default=None,
              required=False,
              help='The new setting for making logical processors lose their '
              'time slice when they enter a wait state. '
              '(not in DPM mode).')
@click.pass_obj
def cpc_update(cmd_ctx, cpc, **options):
    """
    Update the properties of a CPC.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.

    Limitations:
      * The --acceptable-status option does not support multiple values.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_update(cmd_ctx, cpc, options))


def cmd_cpc_list(cmd_ctx, options):

    client = zhmcclient.Client(cmd_ctx.session)

    try:
        cpcs = client.cpcs.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    show_list = [
        'name',
        'status',
    ]
    if options['type']:
        show_list.extend([
            'iml-mode',
            'dpm-enabled',
            'is-ensemble-member',
        ])
    if options['mach']:
        show_list.extend([
            'machine-type',
            'machine-model',
            'machine-serial-number',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])
    print_resources(cpcs, cmd_ctx.output_format, show_list)


def cmd_cpc_show(cmd_ctx, cpc_name):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    try:
        cpc.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    skip_list = (
        'ec-mcl-description',
        'cpc-power-saving-state',
        'network2-ipv6-info',
        'network1-ipv6-info',
        'auto-start-list',
    )
    print_properties(cpc.properties, cmd_ctx.output_format, skip_list)


def cmd_cpc_update(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    name_map = {
        'next-activation-profile': 'next-activation-profile-name',
        'processor-time-slice': None,
        'wait-ends-slice': None,
        'no-wait-ends-slice': None,
    }
    options = original_options(options)
    properties = options_to_properties(options, name_map)

    time_slice = options['processor-time-slice']
    if time_slice is None:
        # 'processor-running-time*' properties not changed
        pass
    elif time_slice < 0:
        raise click.ClickException("Value for processor-time-slice option "
                                   "must be >= 0")
    elif time_slice == 0:
        properties['processor-running-time-type'] = 'system-determined'
    else:  # time_slice > 0
        properties['processor-running-time-type'] = 'user-determined'
        properties['processor-running-time'] = time_slice

    if options['wait-ends-slice'] is not None:
        properties['does-wait-state-end-time-slice'] = \
            options['wait-ends-slice']

    if not properties:
        click.echo("No properties specified for updating CPC %s." % cpc_name)
        return

    try:
        cpc.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    # Name changes are not supported for CPCs.
    click.echo("CPC %s has been updated." % cpc_name)
