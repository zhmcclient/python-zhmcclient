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
import requests.packages.urllib3
import click
import click_repl
from prompt_toolkit.history import FileHistory
import logging
from logging.handlers import SysLogHandler
from logging import StreamHandler
import platform

import zhmcclient
from ._helper import CmdContext, GENERAL_OPTIONS_METAVAR, REPL_HISTORY_FILE, \
    REPL_PROMPT, TABLE_FORMATS, LOG_LEVELS, LOG_COMPONENTS, LOG_DESTINATIONS, \
    SYSLOG_FACILITIES, raise_click_exception

requests.packages.urllib3.disable_warnings()


# Default values for some options
DEFAULT_OUTPUT_FORMAT = 'table'
DEFAULT_ERROR_FORMAT = 'msg'
DEFAULT_TIMESTATS = False
DEFAULT_LOG = 'all=warning'
DEFAULT_LOG_DESTINATION = 'stderr'
DEFAULT_SYSLOG_FACILITY = 'user'

ERROR_FORMATS = ['msg', 'def']

SYSLOG_ADDRESSES = {
    'Linux': '/dev/log',
    'Darwin': '/var/run/syslog',  # OS-X
    'Windows': ('localhost', 514),
}


@click.group(invoke_without_command=True,
             options_metavar=GENERAL_OPTIONS_METAVAR)
@click.option('-h', '--host', type=str, envvar='ZHMC_HOST',
              help="Hostname or IP address of the HMC "
                   "(Default: ZHMC_HOST environment variable).")
@click.option('-u', '--userid', type=str, envvar='ZHMC_USERID',
              help="Username for the HMC "
                   "(Default: ZHMC_USERID environment variable).")
@click.option('-p', '--password', type=str, envvar='ZHMC_PASSWORD',
              help="Password for the HMC "
                   "(Default: ZHMC_PASSWORD environment variable).")
@click.option('-o', '--output-format', type=click.Choice(TABLE_FORMATS +
              ['json']),
              help='Output format (Default: {of}).'.
              format(of=DEFAULT_OUTPUT_FORMAT))
@click.option('-x', '--transpose', type=str, is_flag=True,
              help='Transpose the output table for metrics.')
@click.option('-e', '--error-format', type=click.Choice(ERROR_FORMATS),
              help='Error message format (Default: {ef}).'.
              format(ef=DEFAULT_ERROR_FORMAT))
@click.option('-t', '--timestats', type=str, is_flag=True,
              help='Show time statistics of HMC operations.')
@click.option('--log', type=str, metavar='COMP=LEVEL,...',
              help="Set a component to a log level (COMP: [{c}], "
              "LEVEL: [{l}], Default: {d}).".
              format(c='|'.join(LOG_COMPONENTS),
                     l='|'.join(LOG_LEVELS),
                     d=DEFAULT_LOG))
@click.option('--log-dest', type=click.Choice(LOG_DESTINATIONS),
              help="Log destination for this command (Default: {ld}).".
              format(ld=DEFAULT_LOG_DESTINATION))
@click.option('--syslog-facility', type=click.Choice(SYSLOG_FACILITIES),
              help="Syslog facility when logging to the syslog "
              "(Default: {slf}).".
              format(slf=DEFAULT_SYSLOG_FACILITY))
@click.version_option(help="Show the version of this command and exit.")
@click.pass_context
def cli(ctx, host, userid, password, output_format, transpose, error_format,
        timestats, log, log_dest, syslog_facility):
    """
    Command line interface for the IBM Z HMC.

    The options shown in this help text are general options that can also
    be specified on any of the (sub-)commands.

    Parameters:

      ctx (:class:`click.Context`): The click context object. Created by the
        ``@click.pass_context`` decorator.

      : The remaining parameters are defined by the ``@click.option``
        decorators.
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
        if transpose is None:
            transpose = False
        if error_format is None:
            error_format = DEFAULT_ERROR_FORMAT
        if timestats is None:
            timestats = DEFAULT_TIMESTATS
    else:
        # We are processing an interactive command.
        # We apply the option defaults from the command line options.
        if host is None:
            host = ctx.obj.host
        if userid is None:
            userid = ctx.obj.userid
        if password is None:
            password = ctx.obj._password
        if output_format is None:
            output_format = ctx.obj.output_format
        if transpose is None:
            transpose = ctx.obj.transpose
        if error_format is None:
            error_format = ctx.obj.error_format
        if timestats is None:
            timestats = ctx.obj.timestats

    if transpose and output_format == 'json':
        raise_click_exception(
            "Transposing output tables (-x / --transpose) conflicts with "
            "non-table output format (-o / --output-format): {}".
            format(output_format),
            error_format)

    # TODO: Add context support for the following options:
    if log is None:
        log = DEFAULT_LOG
    if log_dest is None:
        log_dest = DEFAULT_LOG_DESTINATION
    if syslog_facility is None:
        syslog_facility = DEFAULT_SYSLOG_FACILITY

    # Now we have the effective values for the options as they should be used
    # by the current command, regardless of the mode.

    # Set up logging
    if log_dest == 'syslog':
        # The choices in SYSLOG_FACILITIES have been validated by click
        # so we don't need to further check them.
        facility = SysLogHandler.facility_names[syslog_facility]
        system = platform.system()
        try:
            address = SYSLOG_ADDRESSES[system]
        except KeyError:
            raise NotImplementedError(
                "Logging to syslog is not supported on this platform: {}".
                format(system))
        handler = SysLogHandler(address=address, facility=facility)
        format_string = '%(levelname)s %(name)s: %(message)s'
    elif log_dest == 'stderr':
        handler = StreamHandler(stream=sys.stderr)
        format_string = '%(levelname)s %(name)s: %(message)s'
    else:
        # The choices in LOG_DESTINATIONS have been validated by click
        assert log_dest == 'none'
        handler = None
        format_string = None

    log_specs = log.split(',')
    for log_spec in log_specs:

        # ignore extra ',' at begin, end or in between
        if log_spec == '':
            continue

        try:
            log_comp, log_level = log_spec.split('=', 1)
        except ValueError:
            raise_click_exception("Missing '=' in COMP=LEVEL specification in "
                                  "--log option: {ls}".format(ls=log_spec),
                                  error_format)

        level = getattr(logging, log_level.upper(), None)
        if level is None:
            raise_click_exception("Invalid log level in COMP=LEVEL "
                                  "specification in --log option: {ls}".
                                  format(ls=log_spec),
                                  error_format)

        if log_comp not in LOG_COMPONENTS:
            raise_click_exception("Invalid log component in COMP=LEVEL "
                                  "specification in --log option: {ls}".
                                  format(ls=log_spec), error_format)

        if handler:
            handler.setFormatter(logging.Formatter(format_string))
            if log_comp == 'all':
                logger = logging.getLogger('')
                logger.addHandler(handler)
                logger.setLevel(level)
            else:
                if log_comp == 'api':
                    logger = logging.getLogger(zhmcclient.API_LOGGER_NAME)
                    logger.addHandler(handler)
                    logger.setLevel(level)
                if log_comp == 'hmc':
                    logger = logging.getLogger(zhmcclient.HMC_LOGGER_NAME)
                    logger.addHandler(handler)
                    logger.setLevel(level)
                if log_comp == 'console':
                    logger = logging.getLogger(zhmcclient.CONSOLE_LOGGER_NAME)
                    logger.addHandler(handler)
                    logger.setLevel(level)

    session_id = os.environ.get('ZHMC_SESSION_ID', None)

    def get_password_via_prompt(host, userid):
        """
        Password retrieval function that prompts for the password.

        It follows the interface defined in
        :func:`~zhmcclient.get_password_interface` and needs access to the
        click context (ctx).
        """
        if userid is not None and host is not None:
            ctx.obj.spinner.stop()
            password = click.prompt(
                "Enter password (for user {userid} at HMC {host})".
                format(userid=userid, host=host), hide_input=True,
                confirmation_prompt=False, type=str, err=True)
            ctx.obj.spinner.start()
            return password
        else:
            raise raise_click_exception("{cmd} command requires logon, but no "
                                        "session-id or userid provided.".
                                        format(cmd=ctx.invoked_subcommand),
                                        error_format)

    # We create a command context for each command: An interactive command has
    # its own command context different from the command context for the
    # command line.
    ctx.obj = CmdContext(host, userid, password, output_format, transpose,
                         error_format, timestats, session_id,
                         get_password_via_prompt)

    # Invoke default command
    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


@cli.command('help')
@click.pass_context
def repl_help(ctx):
    """
    Show help message for interactive mode.

    Parameters:

      ctx (:class:`click.Context`): The click context object. Created by the
        ``@click.pass_context`` decorator.
    """
    print("""
The following can be entered in interactive mode:

  <zhmc-cmd>                  Execute zhmc command <zhmc-cmd>.
  !<shell-cmd>                Execute shell command <shell-cmd>.

  <CTRL-D>, :q, :quit, :exit  Exit interactive mode.

  <TAB>                       Tab completion (can be used anywhere).
  --help                      Show zhmc general help message, including a list
                              of zhmc commands.
  <zhmc-cmd> --help           Show help message for zhmc command <zhmc-cmd>.
  help                        Show this help message.
  :?, :h, :help               Show (incomplete) help message about interactive
                              mode.
""")


@cli.command('repl')
@click.pass_context
def repl(ctx):
    """
    Enter interactive (REPL) mode (default).

    Parameters:

      ctx (:class:`click.Context`): The click context object. Created by the
        ``@click.pass_context`` decorator.
    """

    history_file = REPL_HISTORY_FILE
    if history_file.startswith('~'):
        history_file = os.path.expanduser(history_file)

    print("Enter 'help' for help, <CTRL-D> or ':q' to exit.")

    prompt_kwargs = {
        'message': REPL_PROMPT,
        'history': FileHistory(history_file),
    }
    click_repl.repl(ctx, prompt_kwargs=prompt_kwargs)


# TODO: Apparently registering is not needed, clarify that.
# click_repl.register_repl(repl)
