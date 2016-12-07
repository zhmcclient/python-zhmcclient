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


@cli.group('session')
def session_group():
    """
    Command group for managing sessions.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """


@session_group.command('create')
@click.pass_obj
def session_create(cmd_ctx):
    """
    Create an HMC session.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_session_create(cmd_ctx))


@session_group.command('delete')
@click.pass_obj
def session_delete(cmd_ctx):
    """
    Delete the current HMC session.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_session_delete(cmd_ctx))


def cmd_session_create(cmd_ctx):
    """Create an HMC session."""
    session = cmd_ctx.session
    try:
        session.logon(verify=True)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    click.echo("export ZHMC_HOST=%s" % session.host)
    click.echo("export ZHMC_USERID=%s" % session.userid)
    click.echo("export ZHMC_SESSION_ID=%s" % session.session_id)


def cmd_session_delete(cmd_ctx):
    """Delete the current HMC session."""
    session = cmd_ctx.session
    try:
        session.logoff()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    click.echo("unset ZHMC_SESSION_ID")
