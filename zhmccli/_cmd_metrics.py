# Copyright 2017 IBM Corp. All Rights Reserved.
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
import time

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, \
    COMMAND_OPTIONS_METAVAR
from ._cmd_cpc import find_cpc

# The number of seconds the client anticipates will elapse between Get
# Metrics calls against this context. The minimum accepted value is 15.

MIN_ANTICIPATED_FREQUENCY = 15


@cli.group('metrics', options_metavar=COMMAND_OPTIONS_METAVAR)
def metrics_group():
    """
    Command group for reporting metrics.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@metrics_group.command('cpc', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def metrics_cpc(cmd_ctx, cpc, **options):
    """
    Report CPC specific metrics.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_cpc(cmd_ctx, cpc, options))


@metrics_group.command('partition', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def metrics_partition(cmd_ctx, cpc, **options):
    """
    Report Partitions specific metrics.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_partition(cmd_ctx, cpc, options))


@metrics_group.command('lpar', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def metrics_lpar(cmd_ctx, cpc, **options):
    """
    Report LPARs specific metrics.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_lpar(cmd_ctx, cpc, options))


@metrics_group.command('env', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def metrics_env(cmd_ctx, cpc, **options):
    """
    Report environmental data and power consumption for the CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_env(cmd_ctx, cpc, options))


@metrics_group.command('proc', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def metrics_proc(cmd_ctx, cpc, **options):
    """
    Report the processor usage for each physical CPC processor on the CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_proc(cmd_ctx, cpc, options))


@metrics_group.command('crypto', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def metrics_crypto(cmd_ctx, cpc, **options):
    """
    Report the adapter usage for each crypto on the CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_crypto(cmd_ctx, cpc, options))


@metrics_group.command('adapter', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def metrics_adapter(cmd_ctx, cpc, **options):
    """
    Report the adapter usage for each adapter on the DPM enabled CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_adapter(cmd_ctx, cpc, options))


@metrics_group.command('channel', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def metrics_channel(cmd_ctx, cpc, **options):
    """
    Report the channel usage for each channel on the CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_channel(cmd_ctx, cpc, options))


@metrics_group.command('flash', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def metrics_flash(cmd_ctx, cpc, **options):
    """
    Report the adapter usage for each Flash memory (Flash Express) adapter
    on the CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_flash(cmd_ctx, cpc, options))


@metrics_group.command('roce', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def metrics_roce(cmd_ctx, cpc, **options):
    """
    Report the adapter usage for each RoCE adapter on the CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_roce(cmd_ctx, cpc, options))


def cmd_metrics_cpc(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    properties = {'anticipated-frequency-seconds': MIN_ANTICIPATED_FREQUENCY}
    if cpc.dpm_enabled:
        properties['metric-groups'] = ['dpm-system-usage-overview']
    else:
        properties['metric-groups'] = ['cpc-usage-overview']

    mc = client.metrics_contexts.create(properties)
    time.sleep(properties['anticipated-frequency-seconds'] + 1)
    metrics_values = mc.get_metrics()
    cv = zhmcclient.CollectedMetrics(mc, metrics_values)
    for metrics in cv.metrics:
        if metrics.uri == cpc.uri:
            cmd_ctx.spinner.stop()
            print_properties(metrics.properties, cmd_ctx.output_format)
            break
    mc.delete()


def cmd_metrics_partition(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    if cpc.dpm_enabled:
        properties = {
            'anticipated-frequency-seconds': MIN_ANTICIPATED_FREQUENCY,
            'metric-groups': ['partition-usage']
        }
        mc = client.metrics_contexts.create(properties)
        time.sleep(properties['anticipated-frequency-seconds'] + 1)
        metrics_rawdata = mc.get_metrics()
        cv = zhmcclient.CollectedMetrics(mc, metrics_rawdata)
        show_list = ['name']
        for idx, metrics in enumerate(cv.metrics):
            if idx == 0:
                show_list += metrics.properties.keys()
            metrics.properties['name'] = metrics.managed_object.name
        cmd_ctx.spinner.stop()
        # print(metrics_rawdata)
        print_resources(cv.metrics, cmd_ctx.output_format, show_list)
        mc.delete()
    else:
        cmd_ctx.spinner.stop()
        click.echo("CPC is not in DPM mode.")


def cmd_metrics_lpar(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    if not cpc.dpm_enabled:
        properties = {
            'anticipated-frequency-seconds': MIN_ANTICIPATED_FREQUENCY,
            'metric-groups': ['logical-partition-usage']
        }
        mc = client.metrics_contexts.create(properties)
        time.sleep(properties['anticipated-frequency-seconds'] + 1)
        metrics_rawdata = mc.get_metrics()
        cv = zhmcclient.CollectedMetrics(mc, metrics_rawdata)
        show_list = ['name']
        for idx, metrics in enumerate(cv.metrics):
            if idx == 0:
                show_list += metrics.properties.keys()
            metrics.properties['name'] = metrics.managed_object.name
        cmd_ctx.spinner.stop()
        print_resources(cv.metrics, cmd_ctx.output_format, show_list)
        mc.delete()
    else:
        cmd_ctx.spinner.stop()
        click.echo("CPC is in DPM mode.")


def cmd_metrics_env(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    properties = {'anticipated-frequency-seconds': MIN_ANTICIPATED_FREQUENCY,
                  'metric-groups': ['zcpc-environmentals-and-power']}
    mc = client.metrics_contexts.create(properties)
    time.sleep(properties['anticipated-frequency-seconds'] + 1)
    metrics_rawdata = mc.get_metrics()
    cv = zhmcclient.CollectedMetrics(mc, metrics_rawdata)
    for metrics in cv.metrics:
        if metrics.uri == cpc.uri:
            cmd_ctx.spinner.stop()
            print_properties(metrics.properties, cmd_ctx.output_format)
            break
    mc.delete()


def cmd_metrics_proc(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    properties = {'anticipated-frequency-seconds': MIN_ANTICIPATED_FREQUENCY,
                  'metric-groups': ['zcpc-processor-usage']}
    mc = client.metrics_contexts.create(properties)
    time.sleep(properties['anticipated-frequency-seconds'] + 1)
    metrics_rawdata = mc.get_metrics()
    cv = zhmcclient.CollectedMetrics(mc, metrics_rawdata)
    # print(metrics_rawdata)
    cpc_metrics = []
    for metrics in cv.metrics:
        if metrics.uri == cpc.uri:
            cpc_metrics.append(metrics)
    cmd_ctx.spinner.stop()
    # print(metrics_rawdata)
    print_resources(cpc_metrics, cmd_ctx.output_format)
    mc.delete()


def cmd_metrics_crypto(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    properties = {'anticipated-frequency-seconds': MIN_ANTICIPATED_FREQUENCY,
                  'metric-groups': ['crypto-usage']}
    mc = client.metrics_contexts.create(properties)
    time.sleep(properties['anticipated-frequency-seconds'] + 1)
    metrics_rawdata = mc.get_metrics()
    cv = zhmcclient.CollectedMetrics(mc, metrics_rawdata)
    crypto_metrics = []
    for metrics in cv.metrics:
        if metrics.uri == cpc.uri:
            crypto_metrics.append(metrics)
    cmd_ctx.spinner.stop()
#    print(metrics_rawdata)
    print_resources(crypto_metrics, cmd_ctx.output_format)
    mc.delete()


def cmd_metrics_channel(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    if cpc.dpm_enabled:
        cmd_ctx.spinner.stop()
        click.echo("No channels available. CPC is in DPM mode.")
        click.echo("Please use 'zhmc metrics adapter %s' instead." % cpc_name)
        return

    properties = {'anticipated-frequency-seconds': MIN_ANTICIPATED_FREQUENCY,
                  'metric-groups': ['channel-usage']}
    mc = client.metrics_contexts.create(properties)
    time.sleep(properties['anticipated-frequency-seconds'] + 1)
    metrics_rawdata = mc.get_metrics()
    cv = zhmcclient.CollectedMetrics(mc, metrics_rawdata)
    channel_metrics = []
    for metrics in cv.metrics:
        if metrics.uri == cpc.uri:
            channel_metrics.append(metrics)
    cmd_ctx.spinner.stop()
    # print(metrics_rawdata)
    print_resources(channel_metrics, cmd_ctx.output_format)
    mc.delete()


def cmd_metrics_adapter(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    if not cpc.dpm_enabled:
        cmd_ctx.spinner.stop()
        click.echo("No adapters available. CPC is not in DPM mode.")
        click.echo("Please use 'zhmc metrics channel %s' instead." % cpc_name)
        return

    properties = {'anticipated-frequency-seconds': MIN_ANTICIPATED_FREQUENCY,
                  'metric-groups': ['adapter-usage']}
    mc = client.metrics_contexts.create(properties)
    time.sleep(properties['anticipated-frequency-seconds'] + 1)
    metrics_rawdata = mc.get_metrics()
    cv = zhmcclient.CollectedMetrics(mc, metrics_rawdata)
    adapter_metrics = []
    for metrics in cv.metrics:
        if metrics.uri == cpc.uri:
            adapter_metrics.append(metrics)
    cmd_ctx.spinner.stop()
    print(metrics_rawdata)
    print_resources(adapter_metrics, cmd_ctx.output_format)
    mc.delete()


def cmd_metrics_flash(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    properties = {'anticipated-frequency-seconds': MIN_ANTICIPATED_FREQUENCY,
                  'metric-groups': ['flash-memory-usage']}
    mc = client.metrics_contexts.create(properties)
    time.sleep(properties['anticipated-frequency-seconds'] + 1)
    metrics_rawdata = mc.get_metrics()
    cv = zhmcclient.CollectedMetrics(mc, metrics_rawdata)
    # print(metrics_rawdata)
    flash_metrics = []
    show_list = ['channel-id', 'adapter-usage']
    for idx, metrics in enumerate(cv.metrics):
        if idx == 0:
            show_list += metrics.properties.keys()
        if metrics.uri == cpc.uri:
            flash_metrics.append(metrics)
        #    print(metrics.properties)
    cmd_ctx.spinner.stop()
#    print(metrics_rawdata)
    print_resources(flash_metrics, cmd_ctx.output_format, show_list)
    mc.delete()


def cmd_metrics_roce(cmd_ctx, cpc_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)

    properties = {'anticipated-frequency-seconds': MIN_ANTICIPATED_FREQUENCY,
                  'metric-groups': ['roce-usage']}
    mc = client.metrics_contexts.create(properties)
    time.sleep(properties['anticipated-frequency-seconds'] + 1)
    metrics_rawdata = mc.get_metrics()
    cv = zhmcclient.CollectedMetrics(mc, metrics_rawdata)
    roce_metrics = []
    for metrics in cv.metrics:
        if metrics.uri == cpc.uri:
            roce_metrics.append(metrics)
    cmd_ctx.spinner.stop()
    # print(metrics_rawdata)
    print_resources(roce_metrics, cmd_ctx.output_format)
    mc.delete()
