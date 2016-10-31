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

import click
import zhmcclient
import click_spinner
from _cmd_helper import *

def cmd_cpc_list(cmd_ctx):
    """
    Lists CPCs.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    try:
        with click_spinner.spinner():
            cpcs = client.cpcs.list()
        if cmd_ctx.output_format == 'table':
            print_list_in_table(cpcs)
        else:
            for cpc in cpcs:
                click.echo(cpc.properties)
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))

def cmd_cpc_show(cmd_ctx, cpc_name):
    """
    Shows details of CPC.
    """
    session = cmd_ctx.session
    client = zhmcclient.Client(session)
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.NotFound:
        click.echo("Could not find CPC %s on HMC %s" %
                   (cpc_name, session.host))
        return
    try:
        with click_spinner.spinner():
            cpc.pull_full_properties()
        skip_list = list(['ec-mcl-description',
                         'cpc-power-saving-state',
                         '@@implementation-errors',
                         'network2-ipv6-info',
                         'network1-ipv6-info',
                         'auto-start-list'])
        if cmd_ctx.output_format == 'table':
            print_properties_in_table(cpc.properties, skip_list)
        else:
            click.echo(cpc.properties)
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))

