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
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties


@cli.group('partition')
def partition_group():
    """Command group for managing partitions."""


@partition_group.command('list')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.pass_obj
def partition_list(cmd_ctx, cpc_name):
    """List the partitions in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_list(cmd_ctx, cpc_name))


@partition_group.command('create')
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


@partition_group.command('show')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('PARTITION-NAME', type=str, metavar='PARTITION-NAME')
@click.pass_obj
def partition_show(cmd_ctx, cpc_name, partition_name):
    """Show the details of a partition in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_show(cmd_ctx, cpc_name,
                                                   partition_name))


@partition_group.command('start')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('PARTITION-NAME', type=str, metavar='PARTITION-NAME')
@click.pass_obj
def partition_start(cmd_ctx, cpc_name, partition_name):
    """Start a partition in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_start(cmd_ctx, cpc_name,
                                                    partition_name))


@partition_group.command('stop')
@click.argument('CPC-NAME', type=str, metavar='CPC-NAME')
@click.argument('PARTITION-NAME', type=str, metavar='PARTITION-NAME')
@click.pass_obj
def partition_stop(cmd_ctx, cpc_name, partition_name):
    """Stop a partition in a CPC."""
    cmd_ctx.execute_cmd(lambda: cmd_partition_stop(cmd_ctx, cpc_name,
                                                   partition_name))


@partition_group.command('delete')
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


def _find_cpc(client, cpc_name):
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find CPC %s on HMC %s." %
                                   (cpc_name, client.session.host))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return cpc


def _find_partition(client, cpc_name, partition_name):
    cpc = _find_cpc(client, cpc_name)
    if not cpc.dpm_enabled:
        raise click.ClickException("CPC %s is not in DPM mode." % cpc_name)
    try:
        partition = cpc.partitions.find(name=partition_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find partition %s in CPC %s." %
                                   (partition_name, cpc_name))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return partition


def cmd_partition_list(cmd_ctx, cpc_name):
    """
    List the partitions in a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = _find_cpc(client, cpc_name)
    if not cpc.dpm_enabled:
        raise click.ClickException("CPC %s is not in DPM mode." % cpc_name)
    try:
        partitions = cpc.partitions.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    print_resources(partitions, cmd_ctx.output_format)


def cmd_partition_show(cmd_ctx, cpc_name, partition_name):
    """
    Show the details of a partition in a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    partition = _find_partition(client, cpc_name, partition_name)
    try:
        partition.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    skip_list = ('nic-uris')
    print_properties(partition.properties, cmd_ctx.output_format, skip_list)


def cmd_partition_start(cmd_ctx, cpc_name, partition_name):
    """
    Start a partition in a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    partition = _find_partition(client, cpc_name, partition_name)
    try:
        partition.start(wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    click.echo('Partition %s has been started.' % partition_name)


def cmd_partition_stop(cmd_ctx, cpc_name, partition_name):
    """
    Stop a partition in a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    partition = _find_partition(client, cpc_name, partition_name)
    try:
        partition.stop(wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    click.echo('Partition %s has been stopped.' % partition_name)


def cmd_partition_create(cmd_ctx, cpc_name, properties):
    """
    Create a new partition in a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = _find_cpc(client, cpc_name)
    if not cpc.dpm_enabled:
        raise click.ClickException("CPC %s is not in DPM mode." % cpc_name)
    try:
        new_partition = cpc.partitions.create(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    click.echo("New partition %s has been created." %
               new_partition.properties['name'])


def cmd_partition_delete(cmd_ctx, cpc_name, partition_name):
    """
    Delete a partition in a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    partition = _find_partition(client, cpc_name, partition_name)
    try:
        partition.delete()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    click.echo('Partition %s has been deleted.' % partition_name)
