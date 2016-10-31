
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

import os, sys
import click
from tabulate import tabulate
import zhmcclient

global_session_filename = 'session.yml'

class CmdContext(object):

    def __init__(self, host, userid, password, output_format):
        if password is None:
            if "ZHMC_SESSION_ID" in os.environ:
                session_id = os.environ['ZHMC_SESSION_ID']
                self._session = zhmcclient.Session(host, userid,
                                 session_id=session_id)
            else:
                 self._session = zhmcclient.Session(host, userid)
        else:
            self._session = zhmcclient.Session(host, userid, password)

        self._host = host
        self_userid = userid
        self._output_format = output_format

    @property
    def session(self):
        """
        :term:`string`: :class:`requests.Session` object for this session.
        """
        return self._session

    @property
    def output_format(self):
        """
        """
        return self._output_format

    def is_active_session(self):
        if self._session is None:
            return False
        return True

    def execute_cmd(self, cmd):
        if self.is_active_session():
            cmd()
            if self.session.time_stats_keeper.enabled:
                click.echo(self.session.time_stats_keeper)
            return True
        else:
            click.echo('Session is not available.')
            return False


def options_to_properties(options):
    properties = {}
    for k, v in options.iteritems():
        properties[k.replace('_', '-')] = v
    return properties


def print_properties_in_table(properties, skip_list):
    """
    Print properties in tabular output format.
    """
    table = list()
    sorted_fields = sorted(properties)
    for field in sorted_fields:
        if field in skip_list:
            continue
        value = properties[field]
        table.append((field, value))
    headers = ['Field Name', 'Value']
    click.echo(tabulate(table, headers, tablefmt="psql"))


def print_list_in_table(resources):
    """
    Print list of resources in tabular output format.
    """
    table = list()
    header = list()
    for i, resource in enumerate(resources):
        if i == 0:
            headers = [ k for k in resource.properties]
        row = [ v for v in resource.properties.values() ]
        table.append(reversed(row))
    if not table:
        click.echo("No entries.")
    else:
        click.echo(tabulate(table, reversed(headers), tablefmt="psql"))
