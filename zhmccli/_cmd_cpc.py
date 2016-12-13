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
from ._helper import print_properties, print_resources


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


@cli.group('cpc')
def cpc_group():
    """
    Command group for managing CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """


@cpc_group.command('list')
@click.pass_obj
def cpc_list(cmd_ctx):
    """
    List the CPCs managed by the HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_list(cmd_ctx))


@cpc_group.command('show')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.pass_obj
def cpc_show(cmd_ctx, cpc_name):
    """
    Show details of a CPC.

    In table format, some properties are skipped.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_show(cmd_ctx, cpc_name))


@cpc_group.command('update')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.option('--description', type=str, required=False,
              help='The new description of the CPC '
              '(DPM mode only). '
              'Default: No change.')
@click.option('--acceptable-status', type=str, required=False,
              help='The new set of acceptable operational status values. '
              'Default: No change.')
# TODO: Support multiple values for acceptable-status
@click.option('--next-activation-profile', type=str, required=False,
              help='The name of the new next reset activation profile '
              '(not in DPM mode). '
              'Default: No change.')
@click.option('--processor-time-slice', type=int, required=False,
              help='The new time slice (in ms) for logical processors. '
              'A value of 0 causes the time slice to be dynamically '
              'determined by the system. A positive value causes a constant '
              'time slice to be used. '
              '(not in DPM mode). '
              'Default: No change.')
@click.option('--wait-ends-slice/--no-wait-ends-slice', required=False,
              help='The new setting for making logical processors lose their '
              'time slice when they enter a wait state. '
              '(not in DPM mode). '
              'Default: No change.')
@click.pass_obj
def cpc_update(cmd_ctx, cpc_name, **options):
    """
    Update the properties of a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_update(cmd_ctx, cpc_name,
                                                     options))


def _find_cpc(client, cpc_name):
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find CPC %s on HMC %s." %
                                   (cpc_name, client.session.host))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return cpc


def cmd_cpc_list(cmd_ctx):
    client = zhmcclient.Client(cmd_ctx.session)
    try:
        cpcs = client.cpcs.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    print_resources(cpcs, cmd_ctx.output_format)


def cmd_cpc_show(cmd_ctx, cpc_name):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = _find_cpc(client, cpc_name)

    try:
        cpc.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    skip_list = (
        'ec-mcl-description',
        'cpc-power-saving-state',
        'network2-ipv6-info',
        'network1-ipv6-info',
        'auto-start-list')
    print_properties(cpc.properties, cmd_ctx.output_format, skip_list)


def cmd_cpc_update(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = _find_cpc(client, cpc_name)

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

    if options['wait-ends-slice']:
        properties['does-wait-state-end-time-slice'] = True
    elif options['no-wait-ends-slice']:
        properties['does-wait-state-end-time-slice'] = False

    if not properties:
        click.echo("No properties specified for updating CPC %s." % cpc_name)
        return

    try:
        cpc.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    # Name changes are not supported for CPCs.
    click.echo("CPC %s has been updated." % cpc_name)
