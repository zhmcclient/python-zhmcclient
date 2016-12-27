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

from ._helper import CmdContext, GENERAL_OPTIONS_METAVAR


requests.packages.urllib3.disable_warnings()

# Default values for some options
DEFAULT_OUTPUT_FORMAT = 'table'
DEFAULT_TIMESTATS = False


@click.group(invoke_without_command=True,
             options_metavar=GENERAL_OPTIONS_METAVAR)
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

    The options shown in this help text are general options that can also
    be specified on any of the (sub-)commands.
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
            ctx.obj.spinner.stop()
            password = click.prompt(
                "Enter password (for user {userid} at HMC {host})"
                .format(userid=userid, host=host), hide_input=True,
                confirmation_prompt=False, type=str, err=True)
            ctx.obj.spinner.start()
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
