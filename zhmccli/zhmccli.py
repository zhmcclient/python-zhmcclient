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

import os
import sys
import click
import click_spinner
from click_repl import register_repl, repl
import requests.packages.urllib3

from ._cmd_client import *
from ._cmd_session import *
from ._cmd_cpc import *
from ._cmd_lpar import *
from ._cmd_partition import *
from ._cmd_helper import *


# TODO: Rename _cmd_client.py to _cmd_info.py
# TODO: Rename _cmd_helper.py to _helper.py
# TODO: Move functions for sub-commands from zhmccli.py to _cmd_*.py
# TODO: Automated tests for zhmc cli
# TODO: Find a way to clarify in the sub-command help texts that the global
#       options can be used.


requests.packages.urllib3.disable_warnings()

# Default values for some options
DEFAULT_OUTPUT_FORMAT = 'table'
DEFAULT_TIMESTATS = False


def abort_if_false(ctx, param, value):
    if not value:
        raise click.ClickException("Aborted.")


@click.group(invoke_without_command=True)
@click.option('-h', '--host', type=str, envvar='ZHMC_HOST',
              help="Hostname or IP address of the HMC "
                   "(Default: ZHMC_HOST environment variable).")
@click.option('-u', '--userid', type=str, envvar='ZHMC_USERID',
              help="Username for the HMC "
                   "(Default: ZHMC_USERID environment variable).")
@click.option('-o', '--output-format', type=click.Choice(['table', 'json']),
              help='Output format (Default: {of}).'
                   .format(of=DEFAULT_OUTPUT_FORMAT))
@click.option('-t', '--timestats', type=str, is_flag=True,
              help='Show time statistics of HMC operations.')
@click.version_option(help="Show the version of this command and exit.")
@click.pass_context
def cli(ctx, host, userid, output_format, timestats):
    """
    Command line interface for the z Systems HMC.

    zhmc is a command line interface for interacting with the Web Services API
    of the Hardware Management Console (HMC) of z Systems or LinuxONE machines.
    It allows management of LPARs, partitions and much more.

    \b
    The zhmc command line interface can be used in these modes:
    - Interactive - an interactive shell
    - Command-Session - command mode that prompts for a password only once and
      stores the session-id in an environment variable
    - Command-Prompt - command mode that prompts for a password every time

    Example for interactive mode:

       \b
       $ zhmc -h zhmc.example.com -u hmcuser
       Enter password: <password>
       > cpc list
       > partition list JLSE1
       > partition create JLSE1 --name TESTPART_JL --description "blablabla"
       --cp-processors 1 --initial-memory 4096 --maximum-memory 4096
       --processor-mode shared --boot-device test-operating-system
       > partition show JLSE1 TESTPART_JL
       > partition start JLSE1 TESTPART_JL
       > partition stop JLSE1 TESTPART_JL
       > partition delete JLSE1 TESTPART_JL --yes
       > :q

    Example for command-session mode:

       \b
       $ eval $(zhmc -h zhmc.example.com -u hmcuser session create)
       Enter password: <password>
       $ zhmc cpc list
       $ zhmc lpar list P0000P99
       $ zhmc lpar deactivate P0000P99 PART8 --yes
       $ zhmc --timestats lpar activate P0000P99 PART8
       $ zhmc lpar load P0000P99 PART8 5172
       $ zhmc lpar show P0000P99 PART8
       $ zhmc -o json lpar show P0000P30 PART8
       $ eval $(zhmc session delete --yes)

    Example for command-prompt mode:

       \b
       $ zhmc -h zhmc.example.com -u hmcuser cpc list
       Enter password: <password>
       $ zhmc -h zhmc.example.com info
       Enter password: <password>

    To get overall help:

       \b
       $ zhmc --help

    To get help for a specific command (or command group):

       \b
       $ zhmc <command> --help

    To enable bash completion in the current shell:

       \b
       $ eval "$(_ZHMC_COMPLETE=source zhmc)"

    To use bash completion:

       \b
       $ zhmc --<TAB><TAB>
       ... shows the global options to select from ...
       $ zhmc <TAB><TAB>
       ... shows the commands to select from ...
    """

    # Concept: In interactive mode, the global options specified in the command
    # line are used as defaults for the commands that are issued interactively.
    # The interactive commands may override these options.
    # This requires being able to determine for each option whether it has been
    # specified. This is the reason the options don't define defaults in the
    # decorators that define them.

    if ctx.obj is None:
        # We are in command mode or are processing the command line options in
        # interactive mode.
        # We apply the documented option defaults.
        if output_format is None:
            output_format = DEFAULT_OUTPUT_FORMAT
        if timestats is None:
            timestats = DEFAULT_TIMESTATS
    else:
        # We are processing an interactive command.
        # We apply the option defaults from the command line options.
        if host is None:
            host = ctx.obj.host
        if userid is None:
            userid = ctx.obj.userid
        if output_format is None:
            output_format = ctx.obj.output_format
        if timestats is None:
            timestats = ctx.obj.timestats

    # Now we have the effective values for the options as they should be used
    # by the current command, regardless of the mode.

    session_id = os.environ.get('ZHMC_SESSION_ID', None)

    def password_prompt():
        if userid is not None and host is not None:
            spinner_running = (ctx.obj.spinner is not None)
            if spinner_running:
                ctx.obj.spinner_stop()
            password = click.prompt(
                "Enter password (for user {userid} at HMC {host})"
                .format(userid=userid, host=host), hide_input=True,
                confirmation_prompt=False, type=str, err=True)
            if spinner_running:
                ctx.obj.spinner_start()
            return password
        else:
            raise click.ClickException("{cmd} command requires logon, but "
                                       "no session-id or userid provided."
                                       .format(cmd=ctx.invoked_subcommand))

    # We create a command context for each command: An interactive command has
    # its own command context different from the command context for the
    # command line.
    ctx.obj = CmdContext(host, userid, output_format, timestats, session_id,
                         password_prompt)

    # Invoke default command
    if ctx.invoked_subcommand is None:
        repl(ctx)


@cli.command('info')
@click.pass_obj
def info(cmd_ctx):
    """
    Show information about the HMC.
    """
    cmd_ctx.execute_cmd(lambda: cmd_info(cmd_ctx))


@cli.group('session')
def session():
    """Command group for managing sessions."""


@session.command('create')
@click.pass_obj
def session_create(cmd_ctx):
    """Create a HMC session."""
    cmd_ctx.execute_cmd(lambda: cmd_session_create(cmd_ctx))


@session.command('delete')
@click.pass_obj
def session_delete(cmd_ctx):
    """Delete a HMC session."""
    cmd_ctx.execute_cmd(lambda: cmd_session_delete(cmd_ctx))


@cli.group('cpc')
def cpc():
    """Command group for managing CPCs."""

@cpc.command('list')
@click.pass_obj
def cpc_list(cmd_ctx):
    """List the CPCs."""
    cmd_ctx.execute_cmd(lambda: cmd_cpc_list(cmd_ctx))

@cpc.command('show')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.pass_obj
def cpc_show(cmd_ctx, cpc_name):
    """Show details of a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_cpc_show(cmd_ctx, cpc_name))


@cli.group('lpar')
def lpar():
    """Command group for managing LPARs."""

@lpar.command('list')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.pass_obj
def lpar_list(cmd_ctx, cpc_name):
    """List the LPARs in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_lpar_list(cmd_ctx, cpc_name))

@lpar.command('show')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('LPAR-NAME', type=str, metavar='LPAR-NAME')
@click.pass_obj
def lpar_show(cmd_ctx, cpc_name, lpar_name):
    """Show details of an LPAR in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_lpar_show(cmd_ctx, cpc_name, lpar_name))

@lpar.command('activate')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('LPAR-NAME', type=str, metavar='LPAR-NAME')
@click.pass_obj
def lpar_activate(cmd_ctx, cpc_name, lpar_name):
    """Activate an LPAR in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_lpar_activate(cmd_ctx, cpc_name,
                                                  lpar_name))

@lpar.command('deactivate')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('LPAR-NAME', type=str, metavar='LPAR-NAME')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deactivation of the LPAR.',
              prompt='Are you sure you want to deactivate the LPAR ?')
@click.pass_obj
def lpar_deactivate(cmd_ctx, cpc_name, lpar_name):
    """Deactivate an LPAR in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_lpar_deactivate(cmd_ctx, cpc_name,
                                                    lpar_name))

@lpar.command('load')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('LPAR-NAME', type=str, metavar='LPAR-NAME')
@click.argument('LOAD-ADDRESS', type=str, metavar='LOAD-ADDRESS')
@click.pass_obj
def lpar_load(cmd_ctx, cpc_name, lpar_name, load_address):
    """Load an LPAR in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_lpar_load(cmd_ctx, cpc_name, lpar_name,
                                              load_address))


@cli.group('partition')
def partition():
    """Command group for managing partitions."""

@partition.command('list')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.pass_obj
def partition_list(cmd_ctx, cpc_name):
    """List the partitions in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_list(cmd_ctx, cpc_name))

@partition.command('create')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.option('--name', type=str, required=True,
              help='The name of the partition.')
@click.option('--description', type=str, required=False,
              help='The description associated with this partition.')
@click.option('--cp-processors', type=int, required=True,
              help='Defines the number of general purpose processors (CP).')
@click.option('--initial-memory', type=int, required=True,
              help='The initial amount of memory when the partition is '
                   'started.')
@click.option('--maximum-memory', type=int, required=True,
              help='The maximum size while the partition is running.')
@click.option('--processor-mode', type=str, required=True,
              help='Defines how processors are allocated to the partition.')
@click.option('--boot-device', type=str, required=True,
              help='The type of device from which the partition is booted.')
@click.pass_context
def partition_create(ctx, cpc_name, **options):
    """Create a partition in a CPC."""
    properties = options_to_properties(options)
    cmd_ctx = ctx.obj
    cmd_ctx.execute_cmd(lambda: cmd_partition_create(cmd_ctx, cpc_name,
                                                     properties))

@partition.command('show')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('PARTITION-NAME', type=str, metavar='PARTITION-NAME')
@click.pass_obj
def partition_show(cmd_ctx, cpc_name, partition_name):
    """Show the details of a partition in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_show(cmd_ctx, cpc_name,
                                                   partition_name))

@partition.command('start')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('PARTITION-NAME', type=str, metavar='PARTITION-NAME')
@click.pass_obj
def partition_start(cmd_ctx, cpc_name, partition_name):
    """Start a partition in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_start(cmd_ctx, cpc_name,
                                                    partition_name))

@partition.command('stop')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('PARTITION-NAME', type=str, metavar='PARTITION-NAME')
@click.pass_obj
def partition_stop(cmd_ctx, cpc_name, partition_name):
    """Stop a partition in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_stop(cmd_ctx, cpc_name,
                                                   partition_name))

@partition.command('delete')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('PARTITION-NAME', type=str, metavar='PARTITION-NAME')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the partition.',
              prompt='Are you sure you want to delete this partition ?')
@click.pass_obj
def partition_delete(cmd_ctx, cpc_name, partition_name):
    """Delete a partition in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_delete(cmd_ctx, cpc_name,
                                                     partition_name))

register_repl(cli)
