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

import os, sys
import click

from _cmd_client import *
from _cmd_session import *
from _cmd_cpc import *
from _cmd_lpar import *
from _cmd_partition import *
from _cmd_helper import *
from click_repl import register_repl

import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@click.group()
@click.version_option()
@click.option('-t', '--timestats', type=str, is_flag=True, default=False,
              help='Enable time statistics for commands.')
@click.option('-o', '--output-format', type=click.Choice(['table', 'json']), default='table',
              help='Output format (default: table)')
#@click.option('-h', '--host', type=str, envvar='ZHMC_HOST',
@click.option('-h', '--host', type=str,
              help='Hostname HMC.')
#@click.option('-u', '--userid', type=str, envvar='ZHMC_USERID',
@click.option('-u', '--userid', type=str,
              help='User id.')
@click.pass_context
def cli(ctx, timestats, output_format, host, userid):
    """command line client for the zhmcclient.

    zhmc is a command line client for interacting with the Web Services API
    of the Hardware Management Console (HMC) of z Systems or LinuxONE machines.
    It allows management of LPARs, partitions and much more.

    \b
    The command line tool can be used in xxxxtwo modes:
    - Interactive shell (Read-eval-print loop)
    - Using a session
    - Always provide credentials
     a) Example interactive shell:
     $ zhmc -h zhmc.example.com -u hmcuser repl
     <Provide password>
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
     b) Example with a session:
     $ eval $(zhmc -h zhmc.example.com -u hmcuser session create)
     <Provide password>
     $ zhmc cpc list
     $ zhmc lpar list P0000P99
     $ zhmc lpar deactivate P0000P99 PART8 --yes
     $ zhmc --timestats lpar activate P0000P99 PART8
     $ zhmc lpar load P0000P99 PART8 5172
     $ zhmc lpar show P0000P99 PART8
     $ zhmc -o json lpar show P0000P30 PART8
     $ eval $(zhmc session delete --yes)
     The host, userid and session_id are stored in environment variables:
         ZHMC_HOST, ZHMC_USERID, ZHMC_SESSION_ID.
    c) Example for always provide credentials:
    $ zhmc -h zhmc.example.com -u hmcuser cpc list
    $ zhmc -h zhmc.exampe.com api-version
    To get a list of available commands and options run:
    $ zhmc --help
    To get a list of sub-commands of commands and options run:
    $ zhmc session --help
    $ zhmc lpar --help
    $ zhmc partition --help
    """
    if ctx.obj is not None:
        return

    if ctx.invoked_subcommand not in ['api-version', 'info'] and \
       'ZHMC_SESSION_ID' not in os.environ or \
       (host is not None and userid is not None):
        password = click.prompt('Please enter password', hide_input=True,
            confirmation_prompt=False, type=str, err=True)
    else:
        password = None

    if host is None:
        if 'ZHMC_HOST' not in os.environ:
            click.echo('host not set.')
            ctx.abort()
        else:
            host = os.environ['ZHMC_HOST']

    if userid is None:
        if 'ZHMC_USERID' not in os.environ and \
           ctx.invoked_subcommand not in ['api-version', 'info']:
            click.echo('userid not set.')
            ctx.abort()

    cmd_ctx = CmdContext(host, userid, password, output_format)
    if timestats:
        cmd_ctx.session.time_stats_keeper.enable()
    ctx.obj = cmd_ctx

@cli.command('info')
@click.argument('host', required=False, type=str)
@click.pass_obj
def info(cmd_ctx, host):
    """Shows zhmcclient info."""
    if host is not None:
        cmd_info(cmd_ctx, host)
    elif cmd_ctx.execute_cmd(lambda: cmd_info(cmd_ctx, cmd_ctx.session.host)):
        pass
    else:
        click.echo('Create a session or provide a host to this command.')

@cli.command('api-version')
@click.argument('host', required=False, type=str)
@click.pass_obj
def apiversion(cmd_ctx, host):
    """Queries API version."""
    if host is not None:
        cmd_api_version(cmd_ctx, host)
    elif cmd_ctx.execute_cmd(lambda:
            cmd_api_version(cmd_ctx, cmd_ctx.session.host)):
        pass
    else:
        click.echo('Create a session or provide a host to this command.')


@cli.group('session')
def session():
    """Manages Sessions."""

@session.command('create')
@click.pass_obj
def session_create(cmd_ctx):
    """Creates zhmcclient session."""
    cmd_session_create(cmd_ctx)

@session.command('delete')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Confirm deletion of session.',
              prompt='Are you sure you want to delete this session ?')
@click.pass_obj
def session_delete(cmd_ctx):
    """Deletes zhmcclient session."""
    cmd_ctx.execute_cmd(lambda: cmd_session_delete(cmd_ctx))


@cli.group('cpc')
def cpc():
    """Manages CPCs."""

@cpc.command('list')
@click.pass_obj
def cpc_list(cmd_ctx):
    """Lists the CPCs."""
    cmd_ctx.execute_cmd( lambda: cmd_cpc_list(cmd_ctx))

@cpc.command('show')
@click.argument('cpc', type=str, metavar='<cpc name>')
@click.pass_obj
def cpc_show(cmd_ctx, cpc):
    """Shows details of a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_cpc_show(cmd_ctx, cpc))


@cli.group('lpar')
def lpar():
    """Manages LPARs."""

@lpar.command('list')
@click.argument('cpc', type=str, metavar='<cpc name>')
@click.pass_obj
def lpar_list(cmd_ctx, cpc):
    """Lists the LPARs for a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_lpar_list(cmd_ctx, cpc))

@lpar.command('show')
@click.argument('cpc', type=str, metavar='<cpc name>')
@click.argument('lpar', type=str, metavar='<lpar name>')
@click.pass_obj
def lpar_show(cmd_ctx, cpc, lpar):
    """Shows the LPAR details for a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_lpar_show(cmd_ctx, cpc, lpar))

@lpar.command('activate')
@click.argument('cpc', type=str, metavar='<cpc name>')
@click.argument('lpar', type=str, metavar='<lpar name>')
@click.pass_obj
def lpar_activate(cmd_ctx, cpc, lpar):
    """Activates an LPAR for a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_lpar_activate(cmd_ctx, cpc, lpar))

@lpar.command('deactivate')
@click.argument('cpc', type=str, metavar='<cpc name>')
@click.argument('lpar', type=str, metavar='<lpar name>')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Confirm deactivation of LPAR.',
              prompt='Are you sure you want to deactivate the LPAR ?')
@click.pass_obj
def lpar_deactivate(cmd_ctx, cpc, lpar):
    """Deactivates an LPAR for a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_lpar_deactivate(cmd_ctx, cpc, lpar))

@lpar.command('load')
@click.argument('cpc', type=str, metavar='<cpc name>')
@click.argument('lpar', type=str, metavar='<lpar name>')
@click.argument('load_address', type=str)
@click.pass_obj
def lpar_load(cmd_ctx, cpc, lpar, load_address):
    """Loads an LPAR for a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_lpar_load(cmd_ctx, cpc, lpar,
                load_address))


@cli.group('partition')
def partition():
    """Manages Partitions."""

@partition.command('list')
@click.argument('cpc', type=str, metavar='<cpc name>')
@click.pass_obj
def partition_list(cmd_ctx, cpc):
    """Lists the partitions for a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_list(cmd_ctx, cpc))

@partition.command('create')
@click.argument('cpc', type=str, metavar='<cpc name>')
@click.option('--name', type=str, required=True,
              help='The name of the partition.')
@click.option('--description', type=str, required=False,
              help='The description associated with this partition.')
@click.option('--cp-processors', type=int, required=True,
              help='Defines the number of general purpose processors (CP).')
@click.option('--initial-memory', type=int, required=True,
              help='The initial amount of memory when the partition is started.')
@click.option('--maximum-memory', type=int, required=True,
              help='The maximum size while the partition is running.')
@click.option('--processor-mode', type=str, required=True,
              help='Defines how processors are allocated to the partition.')
@click.option('--boot-device', type=str, required=True,
              help='The type of device from which the partition is booted.')
@click.pass_context
def partition_create(ctx, cpc, **options):
    """Creates a partition on the CPC."""
    properties = options_to_properties(options)
    cmd_ctx = ctx.obj
    cmd_ctx.execute_cmd(lambda: cmd_partition_create(cmd_ctx, cpc, properties))

@partition.command('show')
@click.argument('cpc', type=str, metavar='<cpc name>')
@click.argument('partition', type=str, metavar='<partition name>')
@click.pass_obj
def partition_show(cmd_ctx, cpc, partition):
    """Shows the partition details for a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_show(cmd_ctx, cpc, partition))

@partition.command('start')
@click.argument('cpc', type=str, metavar='<cpc name>')
@click.argument('partition', type=str, metavar='<partition name>')
@click.pass_obj
def partition_start(cmd_ctx, cpc, partition):
    """Starts the partition of a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_start(cmd_ctx, cpc, partition))

@partition.command('stop')
@click.argument('cpc', type=str, metavar='<cpc name>')
@click.argument('partition', type=str, metavar='<partition name>')
@click.pass_obj
def partition_stop(cmd_ctx, cpc, partition):
    """Stops the partition of a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_stop(cmd_ctx, cpc, partition))

@partition.command('delete')
@click.argument('cpc', type=str, metavar='<cpc name>')
@click.argument('partition', type=str, metavar='<partition name>')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Confirm deletion of partition.',
              prompt='Are you sure you want to delete this partition ?')
@click.pass_obj
def partition_delete(cmd_ctx, cpc, partition):
    """Deletes the partition of a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_delete(cmd_ctx, cpc, partition))

register_repl(cli)
