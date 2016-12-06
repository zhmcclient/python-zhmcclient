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
import json
import click
import click_spinner
from tabulate import tabulate

import zhmcclient


def abort_if_false(ctx, param, value):
    # pylint: disable=unused-argument
    if not value:
        raise click.ClickException("Aborted.")


class InvalidOutputFormatError(click.ClickException):
    """
    Exception indicating an invalid output format for zhmc.
    """

    def __init__(self, output_format):
        msg = "Invalid output format: {of}".format(of=output_format)
        super(InvalidOutputFormatError, self).__init__(msg)


class CmdContext(object):

    def __init__(self, host, userid, output_format, timestats, session_id,
                 get_password):
        self._host = host
        self._userid = userid
        self._output_format = output_format
        self._timestats = timestats
        self._session_id = session_id
        self._get_password = get_password
        self._session = None
        self._spinner = None

    @property
    def host(self):
        """
        :term:`string`: Hostname or IP address of the HMC.
        """
        return self._host

    @property
    def userid(self):
        """
        :term:`string`: Userid on the HMC.
        """
        return self._userid

    @property
    def output_format(self):
        """
        :term:`string`: Output format to be used.
        """
        return self._output_format

    @property
    def timestats(self):
        """
        bool: Indicates whether time statistics should be printed.
        """
        return self._timestats

    @property
    def session_id(self):
        """
        :term:`string`: Session-id to be used instead of logging on, or `None`.
        """
        return self._session_id

    @property
    def get_password(self):
        """
        :term:`callable`: Password retrieval function, or `None`.
        """
        return self._get_password

    @property
    def session(self):
        """
        :class:`requests.Session` object once logged on, or `None`.
        """
        return self._session

    @property
    def spinner(self):
        """
        :class:`~click_spinner.Spinner` object if a spinner is running, or
        `None`.
        """
        return self._spinner

    def spinner_start(self):
        """
        Start the spinner (unless redirected).

        Unlike :meth:`click_spinner.Spinner.start`, this function can be called
        to restart the spinner after having stopped it (via
        :meth:`spinner_stop`).
        """
        if sys.stdout.isatty():
            self._spinner = click_spinner.Spinner()
            self._spinner.start()

    def spinner_stop(self):
        """
        Stop the spinner.
        """
        if self._spinner is not None:
            self._spinner.stop()
            self._spinner = None

    def execute_cmd(self, cmd):
        if self._session is None:
            if self._host is None:
                raise click.ClickException("No HMC host provided")
            if self._session_id is not None:
                self._session = zhmcclient.Session(
                    self._host, self._userid, session_id=self._session_id,
                    get_password=self._get_password)
            else:
                self._session = zhmcclient.Session(
                    self._host, self._userid, get_password=self._get_password)
        if self.timestats:
            self._session.time_stats_keeper.enable()
        self.spinner_start()
        try:
            cmd()
        finally:
            self.spinner_stop()
            if self._session.time_stats_keeper.enabled:
                click.echo(self._session.time_stats_keeper)


def options_to_properties(options):
    properties = {}
    for k, v in options.iteritems():
        properties[k.replace('_', '-')] = v
    return properties


def print_properties(properties, output_format, skip_list=None):
    """
    Print properties in the desired output format.
    """
    if output_format == 'table':
        print_properties_as_table(properties, skip_list)
    elif output_format == 'json':
        print_properties_as_json(properties)
    else:
        raise InvalidOutputFormatError(output_format)


def print_resources(resources, output_format):
    """
    Print the properties of a list of resources in the desired output format.
    """
    if output_format == 'table':
        print_resources_as_table(resources)
    elif output_format == 'json':
        print_resources_as_json(resources)
    else:
        raise InvalidOutputFormatError(output_format)


def print_properties_as_table(properties, skip_list=None):
    """
    Print properties in tabular output format.
    """
    table = list()
    sorted_fields = sorted(properties)
    for field in sorted_fields:
        if skip_list and field in skip_list:
            continue
        value = properties[field]
        table.append((field, value))
    headers = ['Field Name', 'Value']
    click.echo(tabulate(table, headers, tablefmt="psql"))


def print_resources_as_table(resources):
    """
    Print list of resources in tabular output format.
    """
    table = list()
    for i, resource in enumerate(resources):
        if i == 0:
            headers = resource.properties.keys()
        row = resource.properties.values()
        table.append(reversed(row))
    if not table:
        click.echo("No entries.")
    else:
        click.echo(tabulate(table, reversed(headers), tablefmt="psql"))


def print_properties_as_json(properties):
    """
    Print properties in JSON output format.
    """
    json_str = json.dumps(properties)
    click.echo(json_str)


def print_resources_as_json(resources):
    """
    Print properties of a list of resources in JSON output format.
    """
    json_str = json.dumps([r.properties for r in resources])
    click.echo(json_str)
