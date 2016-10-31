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

import sys
import time
import click
import zhmcclient
import click_spinner

from _cmd_helper import *

def find_lpar(client, cpc_name, lpar_name):
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.NotFound:
        click.echo("Could not find CPC %s on HMC %s."
                   % (cpc_name, client.session.host))
        sys.exit(1)
    try:
        lpar = cpc.lpars.find(name=lpar_name)
        return lpar
    except zhmcclient.NotFound:
        click.echo("Could not find LPAR %s on HMC %s."
                   % (lpar_name, client.session.host))
        sys.exit(1)


def cmd_lpar_list(cmd_ctx, cpc_name):
    """
    Lists the LPARs for a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.NotFound:
        click.echo("Could not find CPC %s on HMC %s" %
                   (cpc_name, cmd_ctx.session.host))
    try:
        with click_spinner.spinner():
            lpars = cpc.lpars.list()
        if cmd_ctx.output_format == 'table':
            print_list_in_table(lpars)
        else:
            for lpar in lpars:
                click.echo(lpar.properties)
    except zhmcclient.HTTPError:
        if cpc.dpm_enabled:
            click.echo("CPC %s is in DPM mode. No LPARs configured." % cpc_name)
        else:
            click.echo("%s: %s" % (exc.__class__.__name__, exc))
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))


def cmd_lpar_show(cmd_ctx, cpc_name, lpar_name):
    """
    Shows the LPAR details for a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    try:
        with click_spinner.spinner():
            lpar = find_lpar(client, cpc_name, lpar_name)
            skip_list = list(['program-status-word-information'])
            lpar.pull_full_properties()
        if cmd_ctx.output_format == 'table':
            print_properties_in_table(lpar.properties, skip_list)
        else:
            click.echo(lpar.properties)
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))


def cmd_lpar_activate(cmd_ctx, cpc_name, lpar_name):
    """
    Activates the LPAR for a CPC.
    """
    session = cmd_ctx.session
    client = zhmcclient.Client(session)
    try:
        with click_spinner.spinner():
            lpar = find_lpar(client, cpc_name, lpar_name)
            status = lpar.activate(wait_for_completion=False)
            job = session.query_job_status(status['job-uri'])
            while job['status'] != 'complete':
                time.sleep(1)
                job = session.query_job_status(status['job-uri'])
            session.delete_completed_job_status(status['job-uri'])
        click.echo('Activation of LPAR %s completed.' % lpar_name)

    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))


def cmd_lpar_deactivate(cmd_ctx, cpc_name, lpar_name):
    """
    Deactivates the LPAR for a CPC.
    """
    session = cmd_ctx.session
    client = zhmcclient.Client(session)
    try:
        with click_spinner.spinner():
            lpar = find_lpar(client, cpc_name, lpar_name)
            status = lpar.deactivate(wait_for_completion=False)
            job = session.query_job_status(status['job-uri'])
            while job['status'] != 'complete':
                time.sleep(1)
                job = session.query_job_status(status['job-uri'])
            session.delete_completed_job_status(status['job-uri'])
        click.echo('Deactivation of LPAR %s completed.' % lpar_name)

    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))


def cmd_lpar_load(cmd_ctx, cpc_name, lpar_name, load_address):
    """
    Loads the LPAR for a CPC.
    """
    session = cmd_ctx.session
    client = zhmcclient.Client(session)
    try:
        with click_spinner.spinner():
            lpar = find_lpar(client, cpc_name, lpar_name)
            status = lpar.load(load_address, wait_for_completion=False)
            job = session.query_job_status(status['job-uri'])
            while job['status'] != 'complete':
                time.sleep(1)
                job = session.query_job_status(status['job-uri'])
            session.delete_completed_job_status(status['job-uri'])
        click.echo('Loading of LPAR %s completed.' % lpar_name)

    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))

