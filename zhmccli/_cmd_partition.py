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

def find_partition(client, cpc_name, partition_name):
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.NotFound:
        click.echo("Could not find CPC %s on HMC %s."
                   % (cpc_name, client.session.host))
        sys.exit(1)
    try:
        partition = cpc.partitions.find(name=partition_name)
        return partition
    except zhmcclient.NotFound:
        click.echo("Could not find Partition %s on HMC %s."
                   % (partition_name, client.session.host))
        sys.exit(1)


def cmd_partition_list(cmd_ctx, cpc_name):
    """
    Lists the partitions for a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.NotFound:
        click.echo("Could not find CPC %s on HMC %s" % (cpc, session.host))
    try:
        with click_spinner.spinner():
            partitions = cpc.partitions.list()
        if cmd_ctx.output_format == 'table':
            print_list_in_table(partitions)
        else:
            for partition in partitions:
                click.echo(partition.properties)
    except zhmcclient.HTTPError:
        if not cpc.dpm_enabled:
            click.echo("CPC %s is not in DPM mode. No partitions configured." % cpc_name)
        else:
            click.echo("%s: %s" % (exc.__class__.__name__, exc))
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))


def cmd_partition_show(cmd_ctx, cpc_name, partition_name):
    """
    Shows the partition details for a CPC.
    """
    client = zhmcclient.Client(cmd_ctx.session)
    try:
        with click_spinner.spinner():
            partition = find_partition(client, cpc_name, partition_name)
            partition.pull_full_properties()
            skip_list = list(['nic-uris'])
            partition.pull_full_properties()
        if cmd_ctx.output_format == 'table':
            print_properties_in_table(partition.properties, skip_list)
        else:
            click.echo(partition.properties)
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))


def cmd_partition_start(cmd_ctx, cpc_name, partition_name):
    """
    Starts the partition for a CPC.
    """
    session = cmd_ctx.session
    client = zhmcclient.Client(session)
    try:
        with click_spinner.spinner():
            partition = find_partition(client, cpc_name, partition_name)
            status = partition.start(wait_for_completion=False)
            job = session.query_job_status(status['job-uri'])
            while job['status'] != 'complete':
                time.sleep(1)
                job = session.query_job_status(status['job-uri'])
            session.delete_completed_job_status(status['job-uri'])
        click.echo('Starting of partition %s completed.' % partition_name)
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))


def cmd_partition_stop(cmd_ctx, cpc_name, partition_name):
    """
    Stops the partition for a CPC.
    """
    session = cmd_ctx.session
    client = zhmcclient.Client(session)
    try:
        with click_spinner.spinner():
            partition = find_partition(client, cpc_name, partition_name)
            status = partition.stop(wait_for_completion=False)
            job = session.query_job_status(status['job-uri'])
            while job['status'] != 'complete':
                time.sleep(1)
                job = session.query_job_status(status['job-uri'])
            session.delete_completed_job_status(status['job-uri'])
        click.echo('Stopping of partition %s completed.' % partition_name)
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))


def cmd_partition_create(cmd_ctx, cpc_name, properties):
    """
    Creates the partition for a CPC.
    """
    session = cmd_ctx.session
    client = zhmcclient.Client(session)
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.NotFound:
        click.echo("Could not find CPC %s on HMC %s."
                   % (cpc_name, client.session.host))
        sys.exit(1)
    try:
        with click_spinner.spinner():
            new_partition = cpc.partitions.create(properties)
        click.echo("New partition %s with uri %s created."
                   % (new_partition.properties['name'], new_partition.uri))
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))


def cmd_partition_delete(cmd_ctx, cpc_name, partition_name):
    """
    Deletes the partition for a CPC.
    """
    session = cmd_ctx.session
    client = zhmcclient.Client(session)
    try:
        with click_spinner.spinner():
            partition = find_partition(client, cpc_name, partition_name)
            status = partition.delete()
        click.echo('Deleting of partition %s completed.' % partition_name)
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))
