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

import sys
import time
import click
import zhmcclient
import click_spinner

from ._cmd_helper import *


def _find_cpc(client, cpc_name):
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find CPC %s on HMC %s." %
                                   (cpc_name, client.session.host))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return cpc


def _find_lpar(client, cpc_name, lpar_name):
    cpc = _find_cpc(client, cpc_name)
    if cpc.dpm_enabled:
        raise click.ClickException("CPC %s is in DPM mode." % cpc_name)
    try:
        lpar = cpc.lpars.find(name=lpar_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find LPAR %s in CPC %s." %
                                   (lpar_name, cpc_name))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return lpar


def cmd_lpar_list(cmd_ctx, cpc_name):
    """
    List the LPARs in a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = _find_cpc(client, cpc_name)
    if cpc.dpm_enabled:
        raise click.ClickException("CPC %s is in DPM mode." % cpc_name)
    try:
        lpars = cpc.lpars.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    print_resources(lpars, cmd_ctx.output_format)


def cmd_lpar_show(cmd_ctx, cpc_name, lpar_name):
    """
    Show the details of an LPAR in a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    lpar = _find_lpar(client, cpc_name, lpar_name)
    try:
        lpar.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    skip_list = ('program-status-word-information')
    print_properties(lpar.properties, cmd_ctx.output_format, skip_list)


def cmd_lpar_activate(cmd_ctx, cpc_name, lpar_name):
    """
    Activate an LPAR in a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    lpar = _find_lpar(client, cpc_name, lpar_name)
    try:
        lpar.activate(wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    click.echo('Activation of LPAR %s is complete.' % lpar_name)


def cmd_lpar_deactivate(cmd_ctx, cpc_name, lpar_name):
    """
    Deactivate an LPAR in a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    lpar = _find_lpar(client, cpc_name, lpar_name)
    try:
        lpar.deactivate(wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    click.echo('Deactivation of LPAR %s is complete.' % lpar_name)


def cmd_lpar_load(cmd_ctx, cpc_name, lpar_name, load_address):
    """
    Load an LPAR in a CPC from a load address.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    lpar = _find_lpar(client, cpc_name, lpar_name)
    try:
        lpar.load(load_address, wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    click.echo('Loading of LPAR %s is complete.' % lpar_name)
