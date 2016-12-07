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
    List the CPCs.

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


def cmd_cpc_list(cmd_ctx):
    """
    List CPCs.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    try:
        cpcs = client.cpcs.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    print_resources(cpcs, cmd_ctx.output_format)


def cmd_cpc_show(cmd_ctx, cpc_name):
    """
    Show details of a CPC.
    In table format, some properties are skipped.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    try:
        cpc = client.cpcs.find(name=cpc_name)
        cpc.pull_full_properties()
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find CPC %s on HMC %s" %
                                   (cpc_name, cmd_ctx.session.host))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    skip_list = ('ec-mcl-description',
                 'cpc-power-saving-state',
                 '@@implementation-errors',
                 'network2-ipv6-info',
                 'network1-ipv6-info',
                 'auto-start-list')
    print_properties(cpc.properties, cmd_ctx.output_format, skip_list)
