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
import requests.packages.urllib3
import click
from click_repl import register_repl, repl

from ._helper import CmdContext


# TODO: Documentation for zhmc cli
# TODO: Automated tests for zhmc cli
# TODO: Find a way to clarify in the sub-command help texts that the global
#       options can be used.


requests.packages.urllib3.disable_warnings()

# Default values for some options
DEFAULT_OUTPUT_FORMAT = 'table'
DEFAULT_TIMESTATS = False


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


register_repl(cli)
