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

from ._helper import *


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
        lpar = cpc.partitions.find(name=partition_name)
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
