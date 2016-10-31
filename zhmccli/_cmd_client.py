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

import click
import zhmcclient
from _cmd_helper import *


def cmd_info(cmd_ctx, host):
    """
    zhmcclient info.
    """
    try:
        session = zhmcclient.Session(host)
        client = zhmcclient.Client(session)
        vi = client.version_info()
        click.echo("HMC API version: {}.{}".format(vi[0], vi[1]))
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))


def cmd_api_version(cmd_ctx, host):
    """
    Query API version.
    """
    session = zhmcclient.Session(host)
    client = zhmcclient.Client(session)
    table = list()
    try:
        api_version = client.query_api_version()
        if cmd_ctx.output_format == 'table':
            print_properties_in_table(api_version, skip_list=list())
        else:
            click.echo(api_version)
    except zhmcclient.Error as exc:
        click.echo("%s: %s" % (exc.__class__.__name__, exc))

