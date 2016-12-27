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

import json
from collections import OrderedDict
import click
import click_spinner
from tabulate import tabulate

import zhmcclient

# Display of options in usage line
GENERAL_OPTIONS_METAVAR = '[GENERAL-OPTIONS]'
COMMAND_OPTIONS_METAVAR = '[COMMAND-OPTIONS]'


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
        self._spinner = click_spinner.Spinner()

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
        :class:`~click_spinner.Spinner` object.

        Since click_spinner 0.1.5, the Spinner object takes care of suppressing
        the spinner when not on a tty, and is able to suspend/resume the
        spinner via its stop() and start() methods.
        """
        return self._spinner

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
        self.spinner.start()
        try:
            cmd()
        finally:
            self.spinner.stop()
            if self._session.time_stats_keeper.enabled:
                click.echo(self._session.time_stats_keeper)


def original_options(options):
    """
    Return the input options with their original names.

    This is used to undo the name change the click package applies
    automatically before passing the options to the function that was decorated
    with 'click.option()'. The original names are needed in case there is
    special processing of the options on top of 'options_to_properties()'.

    The original names are constructed by replacing any underscores '_' with
    hyphens '-'. This approach may not be perfect in general, but it works for
    the zhmc CLI because the original option names do not have any underscores.

    Parameters:

      options (dict): The click options dictionary as passed to the decorated
        function by click (key: option name as changed by click, value: option
        value).

    Returns:

      dict: Options with their original names.
    """
    org_options = {}
    for name, value in options.iteritems():
        org_name = name.replace('_', '-')
        org_options[org_name] = value
    return org_options


def options_to_properties(options, name_map=None):
    """
    Convert click options into HMC resource properties.

    The click option names in input parameters to this function are the
    original option names (e.g. as produced by `original_options()`.

    Options with a value of `None` are not added to the returned resource
    properties.

    If a name mapping dictionary is specified, the option names are mapped
    using that dictionary. If an option name is mapped to `None`, it is not
    going to be added to the set of returned resource properties.

    Parameters:

      options (dict): The options dictionary (key: original option name,
        value: option value).

      name_map (dict): `None` or name mapping dictionary (key: original
        option name, value: property name, or `None` to not add this option to
        the returned properties).

    Returns:

      dict: Resource properties (key: property name, value: option value)
    """
    properties = {}
    for name, value in options.iteritems():
        if value is None:
            continue
        if name_map:
            name = name_map.get(name, name)
        if name is not None:
            properties[name] = value
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


def print_resources(resources, output_format, show_list=None):
    """
    Print the properties of a list of resources in the desired output format.
    """
    if output_format == 'table':
        print_resources_as_table(resources, show_list)
    elif output_format == 'json':
        print_resources_as_json(resources, show_list)
    else:
        raise InvalidOutputFormatError(output_format)


def print_properties_as_table(properties, skip_list=None):
    """
    Print properties in tabular output format.

    The order of rows is ascending by property name.

    Parameters:

      properties (dict): The properties.

      skip_list (iterable of string): The property names to be skipped.
        If `None`, all properties are shown.
    """
    additional_skip_list = (
        '@@implementation-errors',
    )
    table = list()
    sorted_fields = sorted(properties)
    for field in sorted_fields:
        if skip_list and field in skip_list or field in additional_skip_list:
            continue
        value = properties[field]
        table.append((field, value))
    headers = ['Field Name', 'Value']
    click.echo(tabulate(table, headers, tablefmt="psql"))


def print_resources_as_table(resources, show_list=None):
    """
    Print resources in tabular output format.

    Parameters:

      resources (iterable of BaseResource):
        The resources.

      show_list (iterable of string):
        The property names to be shown. If a property is not in the resource
        object, it will be retrieved from the HMC. This iterable also defines
        the order of columns in the table, from left to right in iteration
        order.

        If `None`, all properties in the resource objects are shown, and their
        column order is ascending by property name.
    """
    table = list()
    for i, resource in enumerate(resources):
        properties = OrderedDict()
        if show_list:
            for name in show_list:
                # By using prop(), the resource with the full set of
                # properties will be retrieved, if a desired property is not
                # yet in the resource object
                properties[name] = resource.prop(name)
        else:
            for name in sorted(resource.properties.keys()):
                properties[name] = resource.prop(name)
        if i == 0:
            headers = properties.keys()
        row = properties.values()
        table.append(row)
    if not table:
        click.echo("No resources.")
    else:
        sorted_table = sorted(table, key=lambda row: row[0])
        click.echo(tabulate(sorted_table, headers, tablefmt="psql"))


def print_properties_as_json(properties):
    """
    Print properties in JSON output format.

    Parameters:

      properties (dict): The properties.
    """
    json_str = json.dumps(properties)
    click.echo(json_str)


def print_resources_as_json(resources, show_list=None):
    """
    Print resources in JSON output format.

    Parameters:

      resources (iterable of BaseResource):
        The resources.

      show_list (iterable of string):
        The property names to be shown. If a property is not in a resource
        object, it will be retrieved from the HMC.

        If `None`, all properties in the input resource objects are shown.
    """
    json_obj = list()
    for i, resource in enumerate(resources):
        if show_list:
            properties = OrderedDict()
            for name in show_list:
                # By using prop(), the resource with the full set of
                # properties will be retrieved, if a desired property is not
                # yet in the resource object
                properties[name] = resource.prop(name, None)
        else:
            properties = resource.properties
        json_obj.append(properties)
    json_str = json.dumps(json_obj)
    click.echo(json_str)
