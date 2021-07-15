# Copyright 2016-2021 IBM Corp. All Rights Reserved.
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

# pylint: disable=too-few-public-methods

"""
A module with various handler classes for the HTTP methods against HMC URIs,
based on the faked HMC.

Most handler classes do not need to be documented, but some of them have
methods that can be mocked in order to provoke non-standard behavior in
the handling of the HTTP methods.
"""

from __future__ import absolute_import

import re
import time
import copy
from requests.utils import unquote

from ._hmc import InputError

__all__ = ['UriHandler', 'LparActivateHandler', 'LparDeactivateHandler',
           'LparLoadHandler', 'HTTPError', 'URIS']


class HTTPError(Exception):
    """
    Exception that will be turned into an HTTP error response message.
    """

    def __init__(self, method, uri, http_status, reason, message):
        super(HTTPError, self).__init__()
        self.method = method
        self.uri = uri
        self.http_status = http_status
        self.reason = reason
        self.message = message

    def response(self):
        """
        Return the JSON object for the HTTP error response message.
        """
        return {
            'request-method': self.method,
            'request-uri': self.uri,
            'http-status': self.http_status,
            'reason': self.reason,
            'message': self.message,
        }


class ConnectionError(Exception):
    # pylint: disable=redefined-builtin
    """
    Indicates a connection error to the faked HMC.
    This mimics the requests.exception.ConnectionError.
    """

    def __init__(self, message):
        super(ConnectionError, self).__init__()
        self.message = message


class InvalidResourceError(HTTPError):
    """
    HTTP error indicating an invalid resource.
    """

    def __init__(self, method, uri, handler_class=None, reason=1,
                 resource_uri=None):
        if handler_class is not None:
            handler_txt = " (handler class %s)" % handler_class.__name__
        else:
            handler_txt = ""
        if not resource_uri:
            resource_uri = uri
        super(InvalidResourceError, self).__init__(
            method, uri,
            http_status=404,
            reason=reason,
            message="Unknown resource with URI: %s%s" %
            (resource_uri, handler_txt))


class InvalidMethodError(HTTPError):
    """
    HTTP error indicating an invalid HTTP method.
    """

    def __init__(self, method, uri, handler_class=None):
        if handler_class is not None:
            handler_txt = "handler class %s" % handler_class.__name__
        else:
            handler_txt = "no handler class"
        super(InvalidMethodError, self).__init__(
            method, uri,
            http_status=404,
            reason=1,
            message="Invalid HTTP method %s on URI: %s %s" %
            (method, uri, handler_txt))


class BadRequestError(HTTPError):
    """
    HTTP error indicating an invalid client request (status 400).
    """

    def __init__(self, method, uri, reason, message):
        super(BadRequestError, self).__init__(
            method, uri,
            http_status=400,
            reason=reason,
            message=message)


class ConflictError(HTTPError):
    """
    HTTP error indicating a conflict in the client request (status 409).
    """

    def __init__(self, method, uri, reason, message):
        super(ConflictError, self).__init__(
            method, uri,
            http_status=409,
            reason=reason,
            message=message)


class CpcNotInDpmError(ConflictError):
    """
    Indicates that the operation requires DPM mode but the CPC is not in DPM
    mode.

    Out of the set of operations that only work in DPM mode, this error is used
    only for the following subset:

    - Create Partition
    - Create Hipersocket
    - Start CPC
    - Stop CPC
    - Set Auto-Start List
    """

    def __init__(self, method, uri, cpc):
        super(CpcNotInDpmError, self).__init__(
            method, uri, reason=5,
            message="CPC is not in DPM mode: %s" % cpc.uri)


class CpcInDpmError(ConflictError):
    """
    Indicates that the operation requires to be not in DPM mode, but the CPC is
    in DPM mode.

    Out of the set of operations that do not work in DPM mode, this error is
    used only for the following subset:

    - Activate CPC (not yet implemented in zhmcclient)
    - Deactivate CPC (not yet implemented in zhmcclient)
    - Import Profiles (not yet implemented in this URI handler)
    - Export Profiles (not yet implemented in this URI handler)
    """

    def __init__(self, method, uri, cpc):
        super(CpcInDpmError, self).__init__(
            method, uri, reason=4,
            message="CPC is in DPM mode: %s" % cpc.uri)


class ServerError(HTTPError):
    """
    HTTP error indicating a server error (status 500).
    """

    def __init__(self, method, uri, reason, message):
        super(ServerError, self).__init__(
            method, uri,
            http_status=500,
            reason=reason,
            message=message)


def parse_query_parms(method, uri, query_str):
    """
    Parse the specified query parms string and return a dictionary of query
    parameters. The key of each dict item is the query parameter name, and the
    value of each dict item is the query parameter value. If a query parameter
    shows up more than once, the resulting dict item value is a list of all
    those values.

    query_str is the query string from the URL, everything after the '?'. If
    it is empty or None, None is returned.

    If a query parameter is not of the format "name=value", an HTTPError 400,1
    is raised.
    """
    if not query_str:
        return None
    query_parms = {}
    for query_item in query_str.split('&'):
        # Example for these items: 'name=a%20b'
        if query_item == '':
            continue
        items = query_item.split('=')
        if len(items) != 2:
            raise BadRequestError(
                method, uri, reason=1,
                message="Invalid format for URI query parameter: {!r} "
                "(valid format is: 'name=value').".
                format(query_item))
        name = unquote(items[0])
        value = unquote(items[1])
        if name in query_parms:
            existing_value = query_parms[name]
            if not isinstance(existing_value, list):
                query_parms[name] = list()
                query_parms[name].append(existing_value)
            query_parms[name].append(value)
        else:
            query_parms[name] = value
    return query_parms


def check_required_fields(method, uri, body, field_names):
    """
    Check required fields in the request body.

    Raises:
      BadRequestError with reason 3: Missing request body
      BadRequestError with reason 5: Missing required field in request body
    """

    # Check presence of request body
    if body is None:
        raise BadRequestError(method, uri, reason=3,
                              message="Missing request body")

    # Check required input fields
    for field_name in field_names:
        if field_name not in body:
            raise BadRequestError(method, uri, reason=5,
                                  message="Missing required field in request "
                                  "body: {}".format(field_name))


def check_valid_cpc_status(method, uri, cpc):
    """
    Check that the CPC is in a valid status, as indicated by its 'status'
    property.

    If the Cpc object does not have a 'status' property set, this function does
    nothing (in order to make the mock support easy to use).

    Raises:
      ConflictError with reason 1: The CPC itself has been targeted by the
        operation.
      ConflictError with reason 6: The CPC is hosting the resource targeted by
        the operation.
    """
    status = cpc.properties.get('status', None)
    if status is None:
        # Do nothing if no status is set on the faked CPC
        return

    valid_statuses = ['active', 'service-required', 'degraded', 'exceptions']
    if status not in valid_statuses:

        if uri.startswith(cpc.uri):
            # The uri targets the CPC (either is the CPC uri or some
            # multiplicity under the CPC uri)
            raise ConflictError(method, uri, reason=1,
                                message="The operation cannot be performed "
                                "because the targeted CPC {} has a status "
                                "that is not valid for the operation: {}".
                                format(cpc.name, status))

        # The uri targets a resource hosted by the CPC
        raise ConflictError(method, uri, reason=6,
                            message="The operation cannot be performed "
                            "because CPC {} hosting the targeted resource "
                            "has a status that is not valid for the "
                            "operation: {}".
                            format(cpc.name, status))


def check_partition_status(method, uri, partition, valid_statuses=None,
                           invalid_statuses=None):
    """
    Check that the partition is in one of the valid statuses (if specified)
    and not in one of the invalid statuses (if specified), as indicated by its
    'status' property.

    If the Partition object does not have a 'status' property set, this
    function does nothing (in order to make the mock support easy to use).

    Raises:
      ConflictError with reason 1 (reason 6 is not used for partitions).
    """
    status = partition.properties.get('status', None)
    if status is None:
        # Do nothing if no status is set on the faked partition
        return

    if valid_statuses and status not in valid_statuses or \
            invalid_statuses and status in invalid_statuses:
        if uri.startswith(partition.uri):

            # The uri targets the partition (either is the partition uri or
            # some multiplicity under the partition uri)
            raise ConflictError(method, uri, reason=1,
                                message="The operation cannot be performed "
                                "because the targeted partition {} has a "
                                "status that is not valid for the operation: "
                                "{}".
                                format(partition.name, status))

        # The uri targets a resource hosted by the partition
        raise ConflictError(method, uri,
                            reason=1,  # Note: 6 not used for partitions
                            message="The operation cannot be performed "
                            "because partition {} hosting the targeted "
                            "resource has a status that is not valid for "
                            "the operation: {}".
                            format(partition.name, status))


class UriHandler(object):
    """
    Handle HTTP methods against a set of known URIs and invoke respective
    handlers.
    """

    def __init__(self, uris):
        self._uri_handlers = []  # tuple of (regexp-pattern, handler-name)
        for uri, handler_class in uris:
            uri_pattern = re.compile('^' + uri + '$')
            tup = (uri_pattern, handler_class)
            self._uri_handlers.append(tup)

    def handler(self, uri, method):
        """
        Return the handler function for an URI and HTTP method.
        """
        for uri_pattern, handler_class in self._uri_handlers:
            m = uri_pattern.match(uri)
            if m:
                uri_parms = m.groups()
                return handler_class, uri_parms
        new_exc = InvalidResourceError(method, uri)
        new_exc.__cause__ = None
        raise new_exc  # zhmcclient_mock.InvalidResourceError

    def get(self, hmc, uri, logon_required):
        """
        Process a HTTP GET method on a URI.
        """
        if not hmc.enabled:
            raise ConnectionError("HMC is not enabled.")
        handler_class, uri_parms = self.handler(uri, 'GET')
        if not getattr(handler_class, 'get', None):
            raise InvalidMethodError('GET', uri, handler_class)
        return handler_class.get('GET', hmc, uri, uri_parms, logon_required)

    def post(self, hmc, uri, body, logon_required, wait_for_completion):
        """
        Process a HTTP POST method on a URI.
        """
        if not hmc.enabled:
            raise ConnectionError("HMC is not enabled.")
        handler_class, uri_parms = self.handler(uri, 'POST')
        if not getattr(handler_class, 'post', None):
            raise InvalidMethodError('POST', uri, handler_class)
        return handler_class.post('POST', hmc, uri, uri_parms, body,
                                  logon_required, wait_for_completion)

    def delete(self, hmc, uri, logon_required):
        """
        Process a HTTP DELETE method on a URI.
        """
        if not hmc.enabled:
            raise ConnectionError("HMC is not enabled.")
        handler_class, uri_parms = self.handler(uri, 'DELETE')
        if not getattr(handler_class, 'delete', None):
            raise InvalidMethodError('DELETE', uri, handler_class)
        handler_class.delete('DELETE', hmc, uri, uri_parms, logon_required)


class GenericGetPropertiesHandler(object):
    """
    Handler class for generic get of resource properties.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Get <resource> Properties."""
        try:
            resource = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        return resource.properties


class GenericUpdatePropertiesHandler(object):
    """
    Handler class for generic update of resource properties.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Update <resource> Properties."""
        assert wait_for_completion is True  # async not supported yet
        try:
            resource = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        resource.update(body)


class GenericDeleteHandler(object):
    """
    Handler class for generic delete of a resource.
    """

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Delete <resource>."""
        try:
            resource = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        resource.manager.remove(resource.oid)


class VersionHandler(object):
    """
    Handler class for operation: Get version.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Get version."""
        api_major, api_minor = hmc.api_version.split('.')
        return {
            'hmc-name': hmc.hmc_name,
            'hmc-version': hmc.hmc_version,
            'api-major-version': int(api_major),
            'api-minor-version': int(api_minor),
        }


class ConsoleHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on Console resource.
    """
    pass


class ConsoleRestartHandler(object):
    """
    Handler class for Console operation: Restart Console.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Restart Console."""
        assert wait_for_completion is True  # synchronous operation
        console_uri = '/api/console'
        try:
            hmc.lookup_by_uri(console_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        hmc.disable()
        time.sleep(5)
        hmc.enable()
        # Note: The HTTP status 202 that the real HMC operation returns, is
        # not visible for the caller of FakedSession (or Session).


class ConsoleShutdownHandler(object):
    """
    Handler class for Console operation: Shutdown Console.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Shutdown Console."""
        assert wait_for_completion is True  # synchronous operation
        console_uri = '/api/console'
        try:
            hmc.lookup_by_uri(console_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        hmc.disable()
        # Note: The HTTP status 202 that the real HMC operation returns, is
        # not visible for the caller of FakedSession (or Session).


class ConsoleMakePrimaryHandler(object):
    """
    Handler class for Console operation: Make Console Primary.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Make Console Primary."""
        assert wait_for_completion is True  # synchronous operation
        console_uri = '/api/console'
        try:
            hmc.lookup_by_uri(console_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        # Nothing to do, as long as the faked HMC does not need to know whether
        # it is primary or alternate.


class ConsoleReorderUserPatternsHandler(object):
    """
    Handler class for Console operation: Reorder User Patterns.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Reorder User Patterns."""
        assert wait_for_completion is True  # synchronous operation
        console_uri = '/api/console'
        try:
            console = hmc.lookup_by_uri(console_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['user-pattern-uris'])
        new_order_uris = body['user-pattern-uris']
        objs = console.user_patterns.list()
        obj_by_uri = {}
        for obj in objs:
            obj_by_uri[obj.uri] = obj
        # Perform the reordering in the faked HMC:
        for _uri in new_order_uris:
            obj = obj_by_uri[_uri]
            console.user_patterns.remove(obj.oid)  # remove from old position
            console.user_patterns.add(obj.properties)  # append to end


class ConsoleGetAuditLogHandler(object):
    """
    Handler class for Console operation: Get Console Audit Log.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Get Console Audit Log."""
        console_uri = '/api/console'
        try:
            hmc.lookup_by_uri(console_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        resp = []
        # TODO: Add the ability to return audit log entries in mock support.
        return resp


class ConsoleGetSecurityLogHandler(object):
    """
    Handler class for Console operation: Get Console Security Log.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Get Console Security Log."""
        console_uri = '/api/console'
        try:
            hmc.lookup_by_uri(console_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        resp = []
        # TODO: Add the ability to return security log entries in mock support.
        return resp


class ConsoleListUnmanagedCpcsHandler(object):
    """
    Handler class for Console operation: List Unmanaged CPCs.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Unmanaged CPCs."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        result_ucpcs = []
        filter_args = parse_query_parms(method, uri, query_str)
        for ucpc in console.unmanaged_cpcs.list(filter_args):
            result_ucpc = {}
            for prop in ucpc.properties:
                if prop in ('object-uri', 'name'):
                    result_ucpc[prop] = ucpc.properties[prop]
            result_ucpcs.append(result_ucpc)
        return {'cpcs': result_ucpcs}


class ConsoleListPermittedPartitionsHandler(object):
    """
    Handler class for Console operation: List Permitted Partitions (DPM).
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Permitted Partitions."""
        query_str = uri_parms[0]
        filter_args = parse_query_parms(method, uri, query_str)

        result_partitions = []
        for cpc in hmc.cpcs.list():

            # Reflect the result of listing the partition
            if cpc.dpm_enabled:

                # Apply the CPC name filter, if specified
                if filter_args and 'cpc-name' in filter_args:
                    if not re.match(filter_args['cpc-name'], cpc.name):
                        continue
                    del filter_args['cpc-name']

                for partition in cpc.partitions.list(filter_args):
                    result_partition = {}
                    result_partition['object-uri'] = \
                        partition.properties.get('object-uri', None)
                    result_partition['name'] = \
                        partition.properties.get('name', None)
                    result_partition['type'] = \
                        partition.properties.get('type', None)
                    result_partition['status'] = \
                        partition.properties.get('status', None)
                    result_partition['has-unacceptable-status'] = \
                        partition.properties.get(
                            'has-unacceptable-status', None)
                    result_partition['cpc-name'] = cpc.name
                    result_partition['cpc-object-uri'] = cpc.uri
                    result_partition['se-version'] = \
                        cpc.properties.get('se-version', None)
                    result_partitions.append(result_partition)

        return {'partitions': result_partitions}


class ConsoleListPermittedLparsHandler(object):
    """
    Handler class for Console operation: List Permitted LPARs (classic).
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Permitted LPARs."""
        query_str = uri_parms[0]
        filter_args = parse_query_parms(method, uri, query_str)

        result_lpars = []
        for cpc in hmc.cpcs.list():

            # Reflect the result of listing the partition
            if not cpc.dpm_enabled:

                # Apply the CPC name filter, if specified
                if filter_args and 'cpc-name' in filter_args:
                    if not re.match(filter_args['cpc-name'], cpc.name):
                        continue
                    del filter_args['cpc-name']

                for lpar in cpc.lpars.list(filter_args):
                    result_lpar = {}
                    result_lpar['object-uri'] = \
                        lpar.properties.get('object-uri', None)
                    result_lpar['name'] = \
                        lpar.properties.get('name', None)
                    result_lpar['activation-mode'] = \
                        lpar.properties.get('activation-mode', None)
                    result_lpar['status'] = \
                        lpar.properties.get('status', None)
                    result_lpar['has-unacceptable-status'] = \
                        lpar.properties.get(
                            'has-unacceptable-status', None)
                    result_lpar['cpc-name'] = cpc.name
                    result_lpar['cpc-object-uri'] = cpc.uri
                    result_lpar['se-version'] = \
                        cpc.properties.get('se-version', None)
                    result_lpars.append(result_lpar)

        return {'logical-partitions': result_lpars}


class UsersHandler(object):
    """
    Handler class for HTTP methods on set of User resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Users."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_users = []
        filter_args = parse_query_parms(method, uri, query_str)
        for user in console.users.list(filter_args):
            result_user = {}
            for prop in user.properties:
                if prop in ('object-uri', 'name', 'type'):
                    result_user[prop] = user.properties[prop]
            result_users.append(result_user)
        return {'users': result_users}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create User."""
        assert wait_for_completion is True  # synchronous operation
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body,
                              ['name', 'type', 'authentication-type'])
        # TODO: There are some more input properties that are required under
        # certain conditions.
        new_user = console.users.add(body)
        return {'object-uri': new_user.uri}


class UserHandler(GenericGetPropertiesHandler,
                  GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single User resource.
    """

    # TODO: Add post() for Update User that rejects name update

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Delete User."""
        try:
            user = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        # Check user type
        type_ = user.properties['type']
        if type_ == 'pattern-based':
            raise BadRequestError(
                method, uri, reason=312,
                message="Cannot delete pattern-based user {!r}".
                format(user.name))
        # Delete the mocked resource
        user.manager.remove(user.oid)


class UserAddUserRoleHandler(object):
    """
    Handler class for operation: Add User Role to User.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Add User Role to User."""
        assert wait_for_completion is True  # synchronous operation
        user_oid = uri_parms[0]
        user_uri = '/api/users/' + user_oid
        try:
            user = hmc.lookup_by_uri(user_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['user-role-uri'])
        user_type = user.properties['type']
        if user_type in ('pattern-based', 'system-defined'):
            raise BadRequestError(
                method, uri, reason=314,
                message="Cannot add user role to user of type {}: {}".
                format(user_type, user_uri))
        user_role_uri = body['user-role-uri']
        try:
            hmc.lookup_by_uri(user_role_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, user_role_uri, reason=2)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        if user.properties.get('user-roles', None) is None:
            user.properties['user-roles'] = []
        user.properties['user-roles'].append(user_role_uri)


class UserRemoveUserRoleHandler(object):
    """
    Handler class for operation: Remove User Role from User.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Remove User Role from User."""
        assert wait_for_completion is True  # synchronous operation
        user_oid = uri_parms[0]
        user_uri = '/api/users/' + user_oid
        try:
            user = hmc.lookup_by_uri(user_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['user-role-uri'])
        user_type = user.properties['type']
        if user_type in ('pattern-based', 'system-defined'):
            raise BadRequestError(
                method, uri, reason=314,
                message="Cannot remove user role from user of type {}: {}".
                format(user_type, user_uri))
        user_role_uri = body['user-role-uri']
        try:
            user_role = hmc.lookup_by_uri(user_role_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, user_role_uri, reason=2)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        if user.properties.get('user-roles', None) is None \
                or user_role_uri not in user.properties['user-roles']:
            raise ConflictError(
                method, uri, reason=316,
                message="User {!r} does not have User Role {!r}".
                format(user.name, user_role.name))
        user.properties['user-roles'].remove(user_role_uri)


class UserRolesHandler(object):
    """
    Handler class for HTTP methods on set of UserRole resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List User Roles."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_user_roles = []
        filter_args = parse_query_parms(method, uri, query_str)
        for user_role in console.user_roles.list(filter_args):
            result_user_role = {}
            for prop in user_role.properties:
                if prop in ('object-uri', 'name', 'type'):
                    result_user_role[prop] = user_role.properties[prop]
            result_user_roles.append(result_user_role)
        return {'user-roles': result_user_roles}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create User Role."""
        assert wait_for_completion is True  # synchronous operation
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['name'])
        properties = copy.deepcopy(body)
        if 'type' in properties:
            raise BadRequestError(
                method, uri, reason=6,
                message="Type specified when creating a user role: {!r}".
                format(properties['type']))
        properties['type'] = 'user-defined'
        new_user_role = console.user_roles.add(properties)
        return {'object-uri': new_user_role.uri}


class UserRoleHandler(GenericGetPropertiesHandler,
                      GenericUpdatePropertiesHandler,
                      GenericDeleteHandler):
    """
    Handler class for HTTP methods on single UserRole resource.
    """
    pass
    # TODO: Add post() for Update UserRole that rejects name update
    # TODO: Add delete() for Delete UserRole that rejects system-defined type


class UserRoleAddPermissionHandler(object):
    """
    Handler class for operation: Add Permission to User Role.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Add Permission to User Role."""
        assert wait_for_completion is True  # synchronous operation
        user_role_oid = uri_parms[0]
        user_role_uri = '/api/user-roles/' + user_role_oid
        try:
            user_role = hmc.lookup_by_uri(user_role_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body,
                              ['permitted-object', 'permitted-object-type'])
        # Reject if User Role is system-defined:
        if user_role.properties['type'] == 'system-defined':
            raise BadRequestError(
                method, uri, reason=314, message="Cannot add permission to "
                "system-defined user role: {}".format(user_role_uri))
        # Apply defaults, so our internally stored copy has all fields:
        permission = copy.deepcopy(body)
        if 'include-members' not in permission:
            permission['include-members'] = False
        if 'view-only-mode' not in permission:
            permission['view-only-mode'] = True
        # Add the permission to its store (the faked User Role object):
        if user_role.properties.get('permissions', None) is None:
            user_role.properties['permissions'] = []
        user_role.properties['permissions'].append(permission)


class UserRoleRemovePermissionHandler(object):
    """
    Handler class for operation: Remove Permission from User Role.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Remove Permission from User Role."""
        assert wait_for_completion is True  # synchronous operation
        user_role_oid = uri_parms[0]
        user_role_uri = '/api/user-roles/' + user_role_oid
        try:
            user_role = hmc.lookup_by_uri(user_role_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body,
                              ['permitted-object', 'permitted-object-type'])
        # Reject if User Role is system-defined:
        if user_role.properties['type'] == 'system-defined':
            raise BadRequestError(
                method, uri, reason=314, message="Cannot remove permission "
                "from system-defined user role: {}".format(user_role_uri))
        # Apply defaults, so we can locate it based upon all fields:
        permission = copy.deepcopy(body)
        if 'include-members' not in permission:
            permission['include-members'] = False
        if 'view-only-mode' not in permission:
            permission['view-only-mode'] = True
        # Remove the permission from its store (the faked User Role object):
        if user_role.properties.get('permissions', None) is not None:
            user_role.properties['permissions'].remove(permission)


class TasksHandler(object):
    """
    Handler class for HTTP methods on set of Task resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Tasks."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_tasks = []
        filter_args = parse_query_parms(method, uri, query_str)
        for task in console.tasks.list(filter_args):
            result_task = {}
            for prop in task.properties:
                if prop in ('element-uri', 'name'):
                    result_task[prop] = task.properties[prop]
            result_tasks.append(result_task)
        return {'tasks': result_tasks}


class TaskHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single Task resource.
    """
    pass


class UserPatternsHandler(object):
    """
    Handler class for HTTP methods on set of UserPattern resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List User Patterns."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_user_patterns = []
        filter_args = parse_query_parms(method, uri, query_str)
        for user_pattern in console.user_patterns.list(filter_args):
            result_user_pattern = {}
            for prop in user_pattern.properties:
                if prop in ('element-uri', 'name', 'type'):
                    result_user_pattern[prop] = user_pattern.properties[prop]
            result_user_patterns.append(result_user_pattern)
        return {'user-patterns': result_user_patterns}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create User Pattern."""
        assert wait_for_completion is True  # synchronous operation
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body,
                              ['name', 'pattern', 'type', 'retention-time',
                               'user-template-uri'])
        new_user_pattern = console.user_patterns.add(body)
        return {'element-uri': new_user_pattern.uri}


class UserPatternHandler(GenericGetPropertiesHandler,
                         GenericUpdatePropertiesHandler,
                         GenericDeleteHandler):
    """
    Handler class for HTTP methods on single UserPattern resource.
    """
    pass


class PasswordRulesHandler(object):
    """
    Handler class for HTTP methods on set of PasswordRule resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Password Rules."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_password_rules = []
        filter_args = parse_query_parms(method, uri, query_str)
        for password_rule in console.password_rules.list(filter_args):
            result_password_rule = {}
            for prop in password_rule.properties:
                if prop in ('element-uri', 'name', 'type'):
                    result_password_rule[prop] = password_rule.properties[prop]
            result_password_rules.append(result_password_rule)
        return {'password-rules': result_password_rules}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create Password Rule."""
        assert wait_for_completion is True  # synchronous operation
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['name'])
        new_password_rule = console.password_rules.add(body)
        return {'element-uri': new_password_rule.uri}


class PasswordRuleHandler(GenericGetPropertiesHandler,
                          GenericUpdatePropertiesHandler,
                          GenericDeleteHandler):
    """
    Handler class for HTTP methods on single PasswordRule resource.
    """
    pass
    # TODO: Add post() for Update PasswordRule that rejects name update


class LdapServerDefinitionsHandler(object):
    """
    Handler class for HTTP methods on set of LdapServerDefinition resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List LDAP Server Definitions."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_ldap_srv_defs = []
        filter_args = parse_query_parms(method, uri, query_str)
        for ldap_srv_def in console.ldap_server_definitions.list(filter_args):
            result_ldap_srv_def = {}
            for prop in ldap_srv_def.properties:
                if prop in ('element-uri', 'name', 'type'):
                    result_ldap_srv_def[prop] = ldap_srv_def.properties[prop]
            result_ldap_srv_defs.append(result_ldap_srv_def)
        return {'ldap-server-definitions': result_ldap_srv_defs}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create LDAP Server Definition."""
        assert wait_for_completion is True  # synchronous operation
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['name'])
        new_ldap_srv_def = console.ldap_server_definitions.add(body)
        return {'element-uri': new_ldap_srv_def.uri}


class LdapServerDefinitionHandler(GenericGetPropertiesHandler,
                                  GenericUpdatePropertiesHandler,
                                  GenericDeleteHandler):
    """
    Handler class for HTTP methods on single LdapServerDefinition resource.
    """
    pass
    # TODO: Add post() for Update LdapServerDefinition that rejects name update


class CpcsHandler(object):
    """
    Handler class for HTTP methods on set of Cpc resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List CPCs."""
        query_str = uri_parms[0]
        result_cpcs = []
        filter_args = parse_query_parms(method, uri, query_str)
        for cpc in hmc.cpcs.list(filter_args):
            result_cpc = {}
            for prop in cpc.properties:
                if prop in ('object-uri', 'name', 'status'):
                    result_cpc[prop] = cpc.properties[prop]
            result_cpcs.append(result_cpc)
        return {'cpcs': result_cpcs}


class CpcHandler(GenericGetPropertiesHandler,
                 GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single Cpc resource.
    """
    pass


class CpcSetPowerSaveHandler(object):
    """
    Handler class for operation: Set CPC Power Save.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Set CPC Power Save (any CPC mode)."""
        assert wait_for_completion is True  # async not supported yet
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['power-saving'])

        power_saving = body['power-saving']
        if power_saving not in ['high-performance', 'low-power', 'custom']:
            raise BadRequestError(method, uri, reason=7,
                                  message="Invalid power-saving value: %r" %
                                  power_saving)

        cpc.properties['cpc-power-saving'] = power_saving
        cpc.properties['cpc-power-saving-state'] = power_saving
        cpc.properties['zcpc-power-saving'] = power_saving
        cpc.properties['zcpc-power-saving-state'] = power_saving


class CpcSetPowerCappingHandler(object):
    """
    Handler class for operation: Set CPC Power Capping.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Set CPC Power Capping (any CPC mode)."""
        assert wait_for_completion is True  # async not supported yet
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['power-capping-state'])

        power_capping_state = body['power-capping-state']
        power_cap_current = body.get('power-cap-current', None)

        if power_capping_state not in ['disabled', 'enabled', 'custom']:
            raise BadRequestError(method, uri, reason=7,
                                  message="Invalid power-capping-state value: "
                                  "%r" % power_capping_state)

        if power_capping_state == 'enabled' and power_cap_current is None:
            raise BadRequestError(method, uri, reason=7,
                                  message="Power-cap-current must be provided "
                                  "when enabling power capping")

        cpc.properties['cpc-power-capping-state'] = power_capping_state
        cpc.properties['cpc-power-cap-current'] = power_cap_current
        cpc.properties['zcpc-power-capping-state'] = power_capping_state
        cpc.properties['zcpc-power-cap-current'] = power_cap_current


class CpcGetEnergyManagementDataHandler(object):
    """
    Handler class for operation: Get CPC Energy Management Data.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Get CPC Energy Management Data (any CPC mode)."""
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        energy_props = {
            'cpc-power-cap-allowed':
                cpc.properties.get('cpc-power-cap-allowed'),
            'cpc-power-cap-current':
                cpc.properties.get('cpc-power-cap-current'),
            'cpc-power-cap-maximum':
                cpc.properties.get('cpc-power-cap-maximum'),
            'cpc-power-cap-minimum':
                cpc.properties.get('cpc-power-cap-minimum'),
            'cpc-power-capping-state':
                cpc.properties.get('cpc-power-capping-state'),
            'cpc-power-consumption':
                cpc.properties.get('cpc-power-consumption'),
            'cpc-power-rating':
                cpc.properties.get('cpc-power-rating'),
            'cpc-power-save-allowed':
                cpc.properties.get('cpc-power-save-allowed'),
            'cpc-power-saving':
                cpc.properties.get('cpc-power-saving'),
            'cpc-power-saving-state':
                cpc.properties.get('cpc-power-saving-state'),
            'zcpc-ambient-temperature':
                cpc.properties.get('zcpc-ambient-temperature'),
            'zcpc-dew-point':
                cpc.properties.get('zcpc-dew-point'),
            'zcpc-exhaust-temperature':
                cpc.properties.get('zcpc-exhaust-temperature'),
            'zcpc-heat-load':
                cpc.properties.get('zcpc-heat-load'),
            'zcpc-heat-load-forced-air':
                cpc.properties.get('zcpc-heat-load-forced-air'),
            'zcpc-heat-load-water':
                cpc.properties.get('zcpc-heat-load-water'),
            'zcpc-humidity':
                cpc.properties.get('zcpc-humidity'),
            'zcpc-maximum-potential-heat-load':
                cpc.properties.get('zcpc-maximum-potential-heat-load'),
            'zcpc-maximum-potential-power':
                cpc.properties.get('zcpc-maximum-potential-power'),
            'zcpc-power-cap-allowed':
                cpc.properties.get('zcpc-power-cap-allowed'),
            'zcpc-power-cap-current':
                cpc.properties.get('zcpc-power-cap-current'),
            'zcpc-power-cap-maximum':
                cpc.properties.get('zcpc-power-cap-maximum'),
            'zcpc-power-cap-minimum':
                cpc.properties.get('zcpc-power-cap-minimum'),
            'zcpc-power-capping-state':
                cpc.properties.get('zcpc-power-capping-state'),
            'zcpc-power-consumption':
                cpc.properties.get('zcpc-power-consumption'),
            'zcpc-power-rating':
                cpc.properties.get('zcpc-power-rating'),
            'zcpc-power-save-allowed':
                cpc.properties.get('zcpc-power-save-allowed'),
            'zcpc-power-saving':
                cpc.properties.get('zcpc-power-saving'),
            'zcpc-power-saving-state':
                cpc.properties.get('zcpc-power-saving-state'),
        }
        cpc_data = {
            'error-occurred': False,
            'object-uri': cpc.uri,
            'object-id': cpc.oid,
            'class': 'cpcs',
            'properties': energy_props,
        }
        result = {'objects': [cpc_data]}

        return result


class CpcStartHandler(object):
    """
    Handler class for operation: Start CPC.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Start CPC (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        cpc.properties['status'] = 'active'


class CpcStopHandler(object):
    """
    Handler class for operation: Stop CPC.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Stop CPC (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        cpc.properties['status'] = 'not-operating'


class CpcImportProfilesHandler(object):
    """
    Handler class for operation: Import Profiles.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Import Profiles (requires classic mode)."""
        assert wait_for_completion is True  # no async
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)
        check_required_fields(method, uri, body, ['profile-area'])
        # TODO: Import the CPC profiles from a simulated profile area


class CpcExportProfilesHandler(object):
    """
    Handler class for operation: Export Profiles.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Export Profiles (requires classic mode)."""
        assert wait_for_completion is True  # no async
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)
        check_required_fields(method, uri, body, ['profile-area'])
        # TODO: Export the CPC profiles to a simulated profile area


class CpcExportPortNamesListHandler(object):
    """
    Handler class for operation: Export WWPN List.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Export WWPN List (requires DPM mode)."""
        assert wait_for_completion is True  # this operation is always synchr.
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_required_fields(method, uri, body, ['partitions'])
        partition_uris = body['partitions']
        if len(partition_uris) == 0:
            raise BadRequestError(
                method, uri, reason=149,
                message="'partitions' field in request body is empty.")

        wwpn_list = []
        for partition_uri in partition_uris:
            partition = hmc.lookup_by_uri(partition_uri)
            partition_cpc = partition.manager.parent
            if partition_cpc.oid != cpc_oid:
                raise BadRequestError(
                    method, uri, reason=149,
                    message="Partition %r specified in 'partitions' field "
                    "is not in the targeted CPC with ID %r (but in the CPC "
                    "with ID %r)." %
                    (partition.uri, cpc_oid, partition_cpc.oid))
            partition_name = partition.properties.get('name', '')
            for hba in partition.hbas.list():
                port_uri = hba.properties['adapter-port-uri']
                port = hmc.lookup_by_uri(port_uri)
                adapter = port.manager.parent
                adapter_id = adapter.properties.get('adapter-id', '')
                devno = hba.properties.get('device-number', '')
                wwpn = hba.properties.get('wwpn', '')
                wwpn_str = '%s,%s,%s,%s' % (partition_name, adapter_id,
                                            devno, wwpn)
                wwpn_list.append(wwpn_str)
        return {
            'wwpn-list': wwpn_list
        }


CPC_PROPNAME_FROM_PROCTYPE = {
    'sap': 'processor-count-service-assist',
    'aap': 'processor-count-aap',
    'ifl': 'processor-count-ifl',
    'icf': 'processor-count-icf',
    'iip': 'processor-count-iip',
    'cbp': 'processor-count-cbp',
}


class CpcAddTempCapacityHandler(object):
    """
    Handler class for operation: Add Temporary Capacity.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Add Temporary Capacity."""
        assert wait_for_completion is True  # no async
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['record-id', 'test'])
        # record_id = body['record-id']  # TODO: Implement
        # test = body['test']  # TODO: Implement
        # force = body.get('force', False)  # TODO: Implement
        software_model = body.get('software-model', None)
        processor_info = body.get('processor-info', None)
        if software_model is not None:
            current_software_model = \
                cpc.properties['software-model-permanent-plus-temporary']
            if current_software_model is not None:
                raise BadRequestError(
                    method, uri, reason=277,
                    message="Cannot activate temporary software model {} "
                    "because temporary software model {} is already active".
                    format(software_model, current_software_model))
            # We accept any software model, and imply the desired total number
            # of general purpose processors from the last two digits.
            pnum = int(software_model[1:])
            pname = 'processor-count-general-purpose'
            ptype = 'cp'
            if pnum < cpc.properties[pname]:
                raise BadRequestError(
                    method, uri, reason=276,
                    message="Cannot activate temporary software model {} "
                    "because its target number of {} {} processors is below "
                    "the current number of {} {} processors".
                    format(software_model, pnum, ptype, cpc.properties[pname],
                           ptype))
            cpc.properties[pname] = pnum
            cpc.properties['software-model-permanent-plus-temporary'] = \
                software_model
        if processor_info is not None:
            for pitem in processor_info:
                ptype = pitem['processor-type']
                psteps = pitem.get('num-processor-steps', None)
                if ptype not in CPC_PROPNAME_FROM_PROCTYPE:
                    raise BadRequestError(
                        method, uri, reason=276,
                        message="Invalid processor type {} was specified in a "
                        "processor-info entry".format(ptype))
                pname = CPC_PROPNAME_FROM_PROCTYPE[ptype]
                if psteps is not None:
                    # TODO: Check against installed number of processors
                    cpc.properties[pname] += psteps


class CpcRemoveTempCapacityHandler(object):
    """
    Handler class for operation: Remove Temporary Capacity.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Remove Temporary Capacity."""
        assert wait_for_completion is True  # no async
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['record-id'])
        # record_id = body['record-id']  # TODO: Implement
        software_model = body.get('software-model', None)
        processor_info = body.get('processor-info', None)
        if software_model is not None:
            current_software_model = \
                cpc.properties['software-model-permanent-plus-temporary']
            if current_software_model is None:
                raise BadRequestError(
                    method, uri, reason=277,
                    message="Cannot deactivate temporary software model {} "
                    "because no temporary software model is currently active".
                    format(software_model))
            # We accept any software model, and imply the desired total number
            # of general purpose processors from the last two digits.
            pnum = int(software_model[1:])
            pname = 'processor-count-general-purpose'
            ptype = 'cp'
            if pnum > cpc.properties[pname]:
                raise BadRequestError(
                    method, uri, reason=276,
                    message="Cannot activate temporary software model {} "
                    "because its target number of {} {} processors is above "
                    "the current number of {} {} processors".
                    format(software_model, pnum, ptype, cpc.properties[pname],
                           ptype))
            cpc.properties[pname] = pnum
            cpc.properties['software-model-permanent-plus-temporary'] = None
        if processor_info is not None:
            for pitem in processor_info:
                ptype = pitem['processor-type']
                psteps = pitem.get('num-processor-steps', None)
                if ptype not in CPC_PROPNAME_FROM_PROCTYPE:
                    raise BadRequestError(
                        method, uri, reason=276,
                        message="Invalid processor type {} was specified in a "
                        "processor-info entry".format(ptype))
                pname = CPC_PROPNAME_FROM_PROCTYPE[ptype]
                if psteps is not None:
                    if cpc.properties[pname] - psteps < 1:
                        raise BadRequestError(
                            method, uri, reason=276,
                            message="Cannot reduce the number of {} {} "
                            "processors by {} because at least one processor "
                            "must remain.".
                            format(cpc.properties[pname], ptype, psteps))
                    cpc.properties[pname] -= psteps


class MetricsContextsHandler(object):
    """
    Handler class for HTTP methods on set of MetricsContext resources.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create Metrics Context."""
        assert wait_for_completion is True  # always synchronous
        check_required_fields(method, uri, body,
                              ['anticipated-frequency-seconds'])
        new_metrics_context = hmc.metrics_contexts.add(body)
        result = {
            'metrics-context-uri': new_metrics_context.uri,
            'metric-group-infos': new_metrics_context.get_metric_group_infos()
        }
        return result


class MetricsContextHandler(object):
    """
    Handler class for HTTP methods on single MetricsContext resource.
    """

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Delete Metrics Context."""
        try:
            metrics_context = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        hmc.metrics_contexts.remove(metrics_context.oid)

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Get Metrics."""
        try:
            metrics_context = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result = metrics_context.get_metric_values_response()
        return result


class AdaptersHandler(object):
    """
    Handler class for HTTP methods on set of Adapter resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Adapters of a CPC (empty result if not in DPM
        mode)."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_adapters = []
        if cpc.dpm_enabled:
            filter_args = parse_query_parms(method, uri, query_str)
            for adapter in cpc.adapters.list(filter_args):
                result_adapter = {}
                for prop in adapter.properties:
                    if prop in ('object-uri', 'name', 'status'):
                        result_adapter[prop] = adapter.properties[prop]
                result_adapters.append(result_adapter)
        return {'adapters': result_adapters}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create Hipersocket (requires DPM mode)."""
        assert wait_for_completion is True
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_required_fields(method, uri, body, ['name'])

        # We need to emulate the behavior of this POST to always create a
        # hipersocket, but the add() method is used for adding all kinds of
        # faked adapters to the faked HMC. So we need to specify the adapter
        # type, but because the behavior of the Adapter resource object is
        # that it only has its input properties set, we add the 'type'
        # property on a copy of the input properties.
        body2 = body.copy()
        body2['type'] = 'hipersockets'
        try:
            new_adapter = cpc.adapters.add(body2)
        except InputError as exc:
            new_exc = BadRequestError(method, uri, reason=5, message=str(exc))
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.BadRequestError
        return {'object-uri': new_adapter.uri}


class AdapterHandler(GenericGetPropertiesHandler,
                     GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single Adapter resource.
    """

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Delete Hipersocket (requires DPM mode)."""
        try:
            adapter = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = adapter.manager.parent
        assert cpc.dpm_enabled
        adapter.manager.remove(adapter.oid)


class AdapterChangeCryptoTypeHandler(object):
    """
    Handler class for operation: Change Crypto Type.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Change Crypto Type (requires DPM mode)."""
        assert wait_for_completion is True  # HMC operation is synchronous
        adapter_uri = uri.split('/operations/')[0]
        try:
            adapter = hmc.lookup_by_uri(adapter_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = adapter.manager.parent
        assert cpc.dpm_enabled
        check_required_fields(method, uri, body, ['crypto-type'])

        # Check the validity of the new crypto_type
        crypto_type = body['crypto-type']
        if crypto_type not in ['accelerator', 'cca-coprocessor',
                               'ep11-coprocessor']:
            raise BadRequestError(
                method, uri, reason=8,
                message="Invalid value for 'crypto-type' field: %s" %
                crypto_type)

        # Reflect the result of changing the crypto type
        adapter.properties['crypto-type'] = crypto_type


class AdapterChangeAdapterTypeHandler(object):
    """
    Handler class for operation: Change Adapter Type.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Change Adapter Type (requires DPM mode)."""
        assert wait_for_completion is True  # HMC operation is synchronous
        adapter_uri = uri.split('/operations/')[0]
        try:
            adapter = hmc.lookup_by_uri(adapter_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = adapter.manager.parent
        assert cpc.dpm_enabled
        check_required_fields(method, uri, body, ['type'])

        new_adapter_type = body['type']

        # Check the validity of the adapter family
        adapter_family = adapter.properties.get('adapter-family', None)
        if adapter_family != 'ficon':
            raise BadRequestError(
                method, uri, reason=18,
                message="The adapter type cannot be changed for adapter "
                "family: %s" % adapter_family)

        # Check the adapter status
        adapter_status = adapter.properties.get('status', None)
        if adapter_status == 'exceptions':
            raise BadRequestError(
                method, uri, reason=18,
                message="The adapter type cannot be changed for adapter "
                "status: %s" % adapter_status)

        # Check the validity of the new adapter type
        if new_adapter_type not in ['fc', 'fcp', 'not-configured']:
            raise BadRequestError(
                method, uri, reason=8,
                message="Invalid new value for 'type' field: %s" %
                new_adapter_type)

        # Check that the new adapter type is not already set
        adapter_type = adapter.properties.get('type', None)
        if new_adapter_type == adapter_type:
            raise BadRequestError(
                method, uri, reason=8,
                message="New value for 'type' field is already set: %s" %
                new_adapter_type)

        # TODO: Reject if adapter is attached to a partition.

        # Reflect the result of changing the adapter type
        adapter.properties['type'] = new_adapter_type


class NetworkPortHandler(GenericGetPropertiesHandler,
                         GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single NetworkPort resource.
    """
    pass


class StoragePortHandler(GenericGetPropertiesHandler,
                         GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single StoragePort resource.
    """
    pass


class PartitionsHandler(object):
    """
    Handler class for HTTP methods on set of Partition resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Partitions of a CPC (empty result if not in DPM
        mode)."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        # Reflect the result of listing the partition
        result_partitions = []
        if cpc.dpm_enabled:
            filter_args = parse_query_parms(method, uri, query_str)
            for partition in cpc.partitions.list(filter_args):
                result_partition = {}
                for prop in partition.properties:
                    if prop in ('object-uri', 'name', 'status'):
                        result_partition[prop] = partition.properties[prop]
                result_partitions.append(result_partition)
        return {'partitions': result_partitions}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create Partition (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)
        check_required_fields(method, uri, body,
                              ['name', 'initial-memory', 'maximum-memory'])
        # TODO: There are some more input properties that are required under
        # certain conditions.

        # Reflect the result of creating the partition
        new_partition = cpc.partitions.add(body)
        return {'object-uri': new_partition.uri}


class PartitionHandler(GenericGetPropertiesHandler,
                       GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single Partition resource.
    """

    # TODO: Add check_valid_cpc_status() in Update Partition Properties
    # TODO: Add check_partition_status(transitional) in Update Partition Props

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Delete Partition."""
        try:
            partition = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['stopped'])

        # Reflect the result of deleting the partition
        partition.manager.remove(partition.oid)


class PartitionStartHandler(object):
    """
    Handler class for operation: Start Partition.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Start Partition (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['stopped'])

        # Reflect the result of starting the partition
        partition.properties['status'] = 'active'
        return {}


class PartitionStopHandler(object):
    """
    Handler class for operation: Stop Partition.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Stop Partition (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['active', 'paused',
                                               'terminated'])
        # TODO: Clarify with HMC team whether statuses 'degraded' and
        #       'reservation-error' should also be stoppable. Otherwise, the
        #       partition cannot leave these states.

        # Reflect the result of stopping the partition
        partition.properties['status'] = 'stopped'
        return {}


class PartitionScsiDumpHandler(object):
    """
    Handler class for operation: Dump Partition.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Dump Partition (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['active', 'paused',
                                               'terminated'])
        check_required_fields(method, uri, body,
                              ['dump-load-hba-uri',
                               'dump-world-wide-port-name',
                               'dump-logical-unit-number'])

        # We don't reflect the dump in the mock state.
        return {}


class PartitionStartDumpProgramHandler(object):
    """
    Handler class for operation: Start Dump Program.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Start Dump Program (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['active', 'degraded', 'paused',
                                               'terminated'])
        check_required_fields(method, uri, body,
                              ['dump-program-info',
                               'dump-program-type'])

        # We don't reflect the dump in the mock state.
        return {}


class PartitionPswRestartHandler(object):
    """
    Handler class for operation: Perform PSW Restart.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Perform PSW Restart (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['active', 'paused',
                                               'terminated'])

        # We don't reflect the PSW restart in the mock state.
        return {}


class PartitionMountIsoImageHandler(object):
    """
    Handler class for operation: Mount ISO Image.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Mount ISO Image (requires DPM mode)."""
        assert wait_for_completion is True  # synchronous operation
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])

        # Parse and check required query parameters
        query_parms = parse_query_parms(method, uri, uri_parms[1])
        try:
            image_name = query_parms['image-name']
        except KeyError:
            new_exc = BadRequestError(
                method, uri, reason=1,
                message="Missing required URI query parameter 'image-name'")
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.BadRequestError
        try:
            ins_file_name = query_parms['ins-file-name']
        except KeyError:
            new_exc = BadRequestError(
                method, uri, reason=1,
                message="Missing required URI query parameter 'ins-file-name'")
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.BadRequestError

        # Reflect the effect of mounting in the partition properties
        partition.properties['boot-iso-image-name'] = image_name
        partition.properties['boot-iso-ins-file'] = ins_file_name
        return {}


class PartitionUnmountIsoImageHandler(object):
    """
    Handler class for operation: Unmount ISO Image.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Unmount ISO Image (requires DPM mode)."""
        assert wait_for_completion is True  # synchronous operation
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])

        # Reflect the effect of unmounting in the partition properties
        partition.properties['boot-iso-image-name'] = None
        partition.properties['boot-iso-ins-file'] = None
        return {}


def ensure_crypto_config(partition):
    """
    Ensure that the 'crypto-configuration' property on the faked partition
    is initialized.
    """

    if 'crypto-configuration' not in partition.properties or \
            partition.properties['crypto-configuration'] is None:
        partition.properties['crypto-configuration'] = {}
    crypto_config = partition.properties['crypto-configuration']

    if 'crypto-adapter-uris' not in crypto_config or \
            crypto_config['crypto-adapter-uris'] is None:
        crypto_config['crypto-adapter-uris'] = []
    adapter_uris = crypto_config['crypto-adapter-uris']

    if 'crypto-domain-configurations' not in crypto_config or \
            crypto_config['crypto-domain-configurations'] is None:
        crypto_config['crypto-domain-configurations'] = []
    domain_configs = crypto_config['crypto-domain-configurations']

    return adapter_uris, domain_configs


class PartitionIncreaseCryptoConfigHandler(object):
    """
    Handler class for operation: Increase Crypto Configuration.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Increase Crypto Configuration (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])
        check_required_fields(method, uri, body, [])  # check just body

        adapter_uris, domain_configs = ensure_crypto_config(partition)

        add_adapter_uris = body.get('crypto-adapter-uris', [])
        add_domain_configs = body.get('crypto-domain-configurations', [])

        # We don't support finding errors in this simple-minded mock support,
        # so we assume that the input is fine (e.g. no invalid adapters) and
        # we just add it.

        for _uri in add_adapter_uris:
            if _uri not in adapter_uris:
                adapter_uris.append(_uri)
        for dc in add_domain_configs:
            if dc not in domain_configs:
                domain_configs.append(dc)


class PartitionDecreaseCryptoConfigHandler(object):
    """
    Handler class for operation: Decrease Crypto Configuration.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Decrease Crypto Configuration (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])
        check_required_fields(method, uri, body, [])  # check just body

        adapter_uris, domain_configs = ensure_crypto_config(partition)

        remove_adapter_uris = body.get('crypto-adapter-uris', [])
        remove_domain_indexes = body.get('crypto-domain-indexes', [])

        # We don't support finding errors in this simple-minded mock support,
        # so we assume that the input is fine (e.g. no invalid adapters) and
        # we just remove it.

        for _uri in remove_adapter_uris:
            if _uri in adapter_uris:
                adapter_uris.remove(_uri)
        for remove_di in remove_domain_indexes:
            for i, dc in enumerate(domain_configs):
                if dc['domain-index'] == remove_di:
                    del domain_configs[i]


class PartitionChangeCryptoConfigHandler(object):
    """
    Handler class for operation: Change Crypto Configuration.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Change Crypto Configuration (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])
        check_required_fields(method, uri, body,
                              ['domain-index', 'access-mode'])

        _, domain_configs = ensure_crypto_config(partition)

        change_domain_index = body['domain-index']
        change_access_mode = body['access-mode']

        # We don't support finding errors in this simple-minded mock support,
        # so we assume that the input is fine (e.g. no invalid domain indexes)
        # and we just change it.

        for dc in domain_configs:
            if dc['domain-index'] == change_domain_index:
                dc['access-mode'] = change_access_mode


class HbasHandler(object):
    """
    Handler class for HTTP methods on set of Hba resources.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create HBA (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_uri = re.sub('/hbas$', '', uri)
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])
        check_required_fields(method, uri, body, ['name', 'adapter-port-uri'])

        # Check the port-related input property
        port_uri = body['adapter-port-uri']
        m = re.match(r'(^/api/adapters/[^/]+)/storage-ports/[^/]+$', port_uri)
        if not m:
            # We treat an invalid port URI like "port not found".
            raise InvalidResourceError(method, uri, reason=6,
                                       resource_uri=port_uri)
        adapter_uri = m.group(1)
        try:
            hmc.lookup_by_uri(adapter_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri, reason=2,
                                           resource_uri=adapter_uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        try:
            hmc.lookup_by_uri(port_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri, reason=6,
                                           resource_uri=port_uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        new_hba = partition.hbas.add(body)

        return {'element-uri': new_hba.uri}


class HbaHandler(GenericGetPropertiesHandler,
                 GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single Hba resource.
    """

    # TODO: Add check_valid_cpc_status() in Update HBA Properties
    # TODO: Add check_partition_status(transitional) in Update HBA Properties

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Delete HBA (requires DPM mode)."""
        try:
            hba = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        partition = hba.manager.parent
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])

        partition.hbas.remove(hba.oid)


class HbaReassignPortHandler(object):
    """
    Handler class for operation: Reassign Storage Adapter Port.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Reassign Storage Adapter Port (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        hba_oid = uri_parms[1]
        hba_uri = '/api/partitions/' + partition_oid + '/hbas/' + hba_oid
        try:
            hba = hmc.lookup_by_uri(hba_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        partition = hmc.lookup_by_uri(partition_uri)  # assert it exists
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])
        check_required_fields(method, uri, body, ['adapter-port-uri'])

        # Reflect the effect of the operation on the HBA
        new_port_uri = body['adapter-port-uri']
        hba.properties['adapter-port-uri'] = new_port_uri


class NicsHandler(object):
    """
    Handler class for HTTP methods on set of Nic resources.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create NIC (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_uri = re.sub('/nics$', '', uri)
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])
        check_required_fields(method, uri, body, ['name'])

        # Check the port-related input properties
        if 'network-adapter-port-uri' in body:
            port_uri = body['network-adapter-port-uri']
            m = re.match(r'(^/api/adapters/[^/]+)/network-ports/[^/]+$',
                         port_uri)
            if not m:
                # We treat an invalid port URI like "port not found".
                raise InvalidResourceError(method, uri, reason=6,
                                           resource_uri=port_uri)
            adapter_uri = m.group(1)
            try:
                hmc.lookup_by_uri(adapter_uri)
            except KeyError:
                new_exc = InvalidResourceError(method, uri, reason=2,
                                               resource_uri=adapter_uri)
                new_exc.__cause__ = None
                raise new_exc  # zhmcclient_mock.InvalidResourceError
            try:
                hmc.lookup_by_uri(port_uri)
            except KeyError:
                new_exc = InvalidResourceError(method, uri, reason=6,
                                               resource_uri=port_uri)
                new_exc.__cause__ = None
                raise new_exc  # zhmcclient_mock.InvalidResourceError
        elif 'virtual-switch-uri' in body:
            vswitch_uri = body['virtual-switch-uri']
            try:
                hmc.lookup_by_uri(vswitch_uri)
            except KeyError:
                new_exc = InvalidResourceError(method, uri, reason=2,
                                               resource_uri=vswitch_uri)
                new_exc.__cause__ = None
                raise new_exc  # zhmcclient_mock.InvalidResourceError
        else:
            nic_name = body.get('name', None)
            raise BadRequestError(
                method, uri, reason=5,
                message="The input properties for creating a NIC {!r} in "
                "partition {!r} must specify either the "
                "'network-adapter-port-uri' or the "
                "'virtual-switch-uri' property.".
                format(nic_name, partition.name))

        # We have ensured that the vswitch exists, so no InputError handling
        new_nic = partition.nics.add(body)

        return {'element-uri': new_nic.uri}


class NicHandler(GenericGetPropertiesHandler,
                 GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single Nic resource.
    """

    # TODO: Add check_valid_cpc_status() in Update NIC Properties
    # TODO: Add check_partition_status(transitional) in Update NIC Properties

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Delete NIC (requires DPM mode)."""
        try:
            nic = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        partition = nic.manager.parent
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])

        partition.nics.remove(nic.oid)


class VirtualFunctionsHandler(object):
    """
    Handler class for HTTP methods on set of VirtualFunction resources.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create Virtual Function (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_uri = re.sub('/virtual-functions$', '', uri)
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])
        check_required_fields(method, uri, body, ['name'])

        new_vf = partition.virtual_functions.add(body)
        return {'element-uri': new_vf.uri}


class VirtualFunctionHandler(GenericGetPropertiesHandler,
                             GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single VirtualFunction resource.
    """

    # TODO: Add check_valid_cpc_status() in Update VF Properties
    # TODO: Add check_partition_status(transitional) in Update VF Properties

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Delete Virtual Function (requires DPM mode)."""
        try:
            vf = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        partition = vf.manager.parent
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])

        partition.virtual_functions.remove(vf.oid)


class VirtualSwitchesHandler(object):
    """
    Handler class for HTTP methods on set of VirtualSwitch resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Virtual Switches of a CPC (empty result if not in
        DPM mode)."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_vswitches = []
        if cpc.dpm_enabled:
            filter_args = parse_query_parms(method, uri, query_str)
            for vswitch in cpc.virtual_switches.list(filter_args):
                result_vswitch = {}
                for prop in vswitch.properties:
                    if prop in ('object-uri', 'name', 'type'):
                        result_vswitch[prop] = vswitch.properties[prop]
                result_vswitches.append(result_vswitch)
        return {'virtual-switches': result_vswitches}


class VirtualSwitchHandler(GenericGetPropertiesHandler,
                           GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single VirtualSwitch resource.
    """
    pass


class VirtualSwitchGetVnicsHandler(object):
    """
    Handler class for operation: Get Connected VNICs of a Virtual Switch.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Get Connected VNICs of a Virtual Switch
        (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        vswitch_oid = uri_parms[0]
        vswitch_uri = '/api/virtual-switches/' + vswitch_oid
        try:
            vswitch = hmc.lookup_by_uri(vswitch_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = vswitch.manager.parent
        assert cpc.dpm_enabled

        connected_vnic_uris = vswitch.properties['connected-vnic-uris']
        return {'connected-vnic-uris': connected_vnic_uris}


class StorageGroupsHandler(object):
    """
    Handler class for HTTP methods on set of StorageGroup resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Storage Groups (always global but with filters)."""
        query_str = uri_parms[0]
        filter_args = parse_query_parms(method, uri, query_str)
        result_storage_groups = []
        for sg in hmc.consoles.console.storage_groups.list(filter_args):
            result_sg = {}
            for prop in sg.properties:
                if prop in ('object-uri', 'cpc-uri', 'name', 'status',
                            'fulfillment-state', 'type'):
                    result_sg[prop] = sg.properties[prop]
            result_storage_groups.append(result_sg)
        return {'storage-groups': result_storage_groups}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create Storage Group."""
        assert wait_for_completion is True  # async not supported yet
        check_required_fields(method, uri, body, ['name', 'cpc-uri', 'type'])
        cpc_uri = body['cpc-uri']
        try:
            cpc = hmc.lookup_by_uri(cpc_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)

        # Reflect the result of creating the storage group

        body2 = body.copy()
        sv_requests = body2.pop('storage-volumes', None)
        new_storage_group = hmc.consoles.console.storage_groups.add(body2)

        sv_uris = []
        if sv_requests:
            for sv_req in sv_requests:
                check_required_fields(method, uri, sv_req, ['operation'])
                operation = sv_req['operation']
                if operation == 'create':
                    sv_props = sv_req.copy()
                    del sv_props['operation']
                    if 'element-uri' in sv_props:
                        raise BadRequestError(
                            method, uri, 7,
                            "The 'element-uri' field in storage-volumes is "
                            "invalid for the create operation")
                    sv_uri = new_storage_group.storage_volumes.add(sv_props)
                    sv_uris.append(sv_uri)
                else:
                    raise BadRequestError(
                        method, uri, 5,
                        "Invalid value for storage-volumes 'operation' "
                        "field: %s" % operation)

        return {
            'object-uri': new_storage_group.uri,
            'element-uris': sv_uris,
        }


class StorageGroupHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single StorageGroup resource.
    """
    pass


class StorageGroupModifyHandler(object):
    """
    Handler class for operation: Modify Storage Group Properties.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Modify Storage Group Properties."""
        assert wait_for_completion is True  # async not supported yet
        # The URI is a POST operation, so we need to construct the SG URI
        storage_group_oid = uri_parms[0]
        storage_group_uri = '/api/storage-groups/' + storage_group_oid
        try:
            storage_group = hmc.lookup_by_uri(storage_group_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        # Reflect the result of modifying the storage group

        body2 = body.copy()
        sv_requests = body2.pop('storage-volumes', None)
        storage_group.update(body2)

        sv_uris = []
        if sv_requests:
            for sv_req in sv_requests:
                check_required_fields(method, uri, sv_req, ['operation'])
                operation = sv_req['operation']
                if operation == 'create':
                    sv_props = sv_req.copy()
                    del sv_props['operation']
                    if 'element-uri' in sv_props:
                        raise BadRequestError(
                            method, uri, 7,
                            "The 'element-uri' field in storage-volumes is "
                            "invalid for the create operation")
                    sv_uri = storage_group.storage_volumes.add(sv_props)
                    sv_uris.append(sv_uri)
                elif operation == 'modify':
                    check_required_fields(method, uri, sv_req, ['element-uri'])
                    sv_uri = sv_req['element-uri']
                    storage_volume = hmc.lookup_by_uri(sv_uri)
                    storage_volume.update_properties(sv_props)
                elif operation == 'delete':
                    check_required_fields(method, uri, sv_req, ['element-uri'])
                    sv_uri = sv_req['element-uri']
                    storage_volume = hmc.lookup_by_uri(sv_uri)
                    storage_volume.delete()
                else:
                    raise BadRequestError(
                        method, uri, 5,
                        "Invalid value for storage-volumes 'operation' "
                        "field: %s" % operation)

        return {
            'element-uris': sv_uris,  # SVs created, maintaining the order
        }


class StorageGroupDeleteHandler(object):
    """
    Handler class for operation: Delete Storage Group.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Delete Storage Group."""
        assert wait_for_completion is True  # async not supported yet
        # The URI is a POST operation, so we need to construct the SG URI
        storage_group_oid = uri_parms[0]
        storage_group_uri = '/api/storage-groups/' + storage_group_oid
        try:
            storage_group = hmc.lookup_by_uri(storage_group_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        # TODO: Check that the SG is detached from any partitions

        # Reflect the result of deleting the storage_group
        storage_group.manager.remove(storage_group.oid)


class StorageGroupRequestFulfillmentHandler(object):
    """
    Handler class for operation: Request Storage Group Fulfillment.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Request Storage Group Fulfillment."""
        assert wait_for_completion is True  # async not supported yet
        # The URI is a POST operation, so we need to construct the SG URI
        storage_group_oid = uri_parms[0]
        storage_group_uri = '/api/storage-groups/' + storage_group_oid
        try:
            hmc.lookup_by_uri(storage_group_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        # Reflect the result of requesting fulfilment for the storage group
        pass


class StorageGroupAddCandidatePortsHandler(object):
    """
    Handler class for operation: Add Candidate Adapter Ports to an FCP Storage
    Group.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Add Candidate Adapter Ports to an FCP Storage Group."""
        assert wait_for_completion is True  # async not supported yet
        # The URI is a POST operation, so we need to construct the SG URI
        storage_group_oid = uri_parms[0]
        storage_group_uri = '/api/storage-groups/' + storage_group_oid
        try:
            storage_group = hmc.lookup_by_uri(storage_group_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        check_required_fields(method, uri, body, ['adapter-port-uris'])

        # TODO: Check that storage group has type FCP

        # Reflect the result of adding the candidate ports
        candidate_adapter_port_uris = \
            storage_group.properties['candidate-adapter-port-uris']
        for ap_uri in body['adapter-port-uris']:
            if ap_uri in candidate_adapter_port_uris:
                raise ConflictError(method, uri, 483,
                                    "Adapter port is already in candidate "
                                    "list of storage group %s: %s" %
                                    (storage_group.name, ap_uri))
            candidate_adapter_port_uris.append(ap_uri)


class StorageGroupRemoveCandidatePortsHandler(object):
    """
    Handler class for operation: Remove Candidate Adapter Ports from an FCP
    Storage Group.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Remove Candidate Adapter Ports from an FCP Storage
        Group."""
        assert wait_for_completion is True  # async not supported yet
        # The URI is a POST operation, so we need to construct the SG URI
        storage_group_oid = uri_parms[0]
        storage_group_uri = '/api/storage-groups/' + storage_group_oid
        try:
            storage_group = hmc.lookup_by_uri(storage_group_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        check_required_fields(method, uri, body, ['adapter-port-uris'])

        # TODO: Check that storage group has type FCP

        # Reflect the result of adding the candidate ports
        candidate_adapter_port_uris = \
            storage_group.properties['candidate-adapter-port-uris']
        for ap_uri in body['adapter-port-uris']:
            if ap_uri not in candidate_adapter_port_uris:
                raise ConflictError(method, uri, 479,
                                    "Adapter port is not in candidate "
                                    "list of storage group %s: %s" %
                                    (storage_group.name, ap_uri))
            candidate_adapter_port_uris.remove(ap_uri)


class CapacityGroupsHandler(object):
    """
    Handler class for HTTP methods on set of CapacityGroup resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Capacity Groups (always global but with filters)."""
        cpc_oid = uri_parms[0]
        cpc_uri = '/api/cpcs/' + cpc_oid
        try:
            cpc = hmc.lookup_by_uri(cpc_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        query_str = uri_parms[1]
        filter_args = parse_query_parms(method, uri, query_str)
        result_capacity_groups = []
        for cg in cpc.capacity_groups.list(filter_args):
            result_cg = {}
            for prop in cg.properties:
                if prop in ('element-uri', 'name'):
                    result_cg[prop] = cg.properties[prop]
            result_capacity_groups.append(result_cg)
        return {'capacity-groups': result_capacity_groups}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create Capacity Group."""
        assert wait_for_completion is True  # async not supported yet
        check_required_fields(method, uri, body, ['name'])
        cpc_oid = uri_parms[0]
        cpc_uri = '/api/cpcs/' + cpc_oid
        try:
            cpc = hmc.lookup_by_uri(cpc_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)

        # Reflect the result of creating the capacity group
        new_capacity_group = cpc.capacity_groups.add(body)

        return {
            'element-uri': new_capacity_group.uri
        }


class CapacityGroupHandler(GenericGetPropertiesHandler,
                           GenericUpdatePropertiesHandler,
                           GenericDeleteHandler):
    """
    Handler class for HTTP methods on single CapacityGroup resource.
    """

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Delete Capacity Group."""
        try:
            capacity_group = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        # Check that Capacity Group is empty
        partition_uris = capacity_group.properties['partition-uris']
        if partition_uris:
            raise ConflictError(
                method, uri, reason=110,
                message="Capacity group {!r} is not empty and contains "
                "partitions with URIs {!r}".
                format(capacity_group.name, partition_uris))

        # Delete the mocked resource
        capacity_group.manager.remove(capacity_group.oid)


class CapacityGroupAddPartitionHandler(object):
    """
    Handler class for operation: Add Partition to Capacity Group.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Add Partition to Capacity Group."""
        assert wait_for_completion is True  # async not supported yet

        # The URI is a POST operation, so we need to construct the CG URI
        cpc_oid = uri_parms[0]
        cpc_uri = '/api/cpcs/' + cpc_oid
        try:
            cpc = hmc.lookup_by_uri(cpc_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cg_oid = uri_parms[1]
        cg_uri = cpc_uri + '/capacity-groups/' + cg_oid

        try:
            capacity_group = hmc.lookup_by_uri(cg_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri, reason=150)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        check_required_fields(method, uri, body, ['partition-uri'])

        # Check the partition exists
        partition_uri = body['partition-uri']
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri, reason=2)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        # Check the partition is in shared processor mode
        processor_mode = partition.properties.get('processor-mode', 'shared')
        if processor_mode != 'shared':
            raise ConflictError(method, uri, 170,
                                "Partition %s is in %s processor mode" %
                                (partition.name, processor_mode))

        # Check the partition is not in this capacity group
        partition_uris = capacity_group.properties['partition-uris']
        if partition.uri in partition_uris:
            raise ConflictError(method, uri, 130,
                                "Partition %s is already a member of "
                                "this capacity group %s" %
                                (partition.name, capacity_group.name))

        # Check the partition is not in any other capacity group
        for cg in cpc.capacity_groups.list():
            if partition.uri in cg.properties['partition-uris']:
                raise ConflictError(method, uri, 120,
                                    "Partition %s is already a member of "
                                    "another capacity group %s" %
                                    (partition.name, cg.name))

        # Reflect the result of adding the partition to the capacity group
        capacity_group.properties['partition-uris'].append(partition.uri)


class CapacityGroupRemovePartitionHandler(object):
    """
    Handler class for operation: Remove Partition from Capacity Group.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Remove Partition from Capacity Group."""
        assert wait_for_completion is True  # async not supported yet

        # The URI is a POST operation, so we need to construct the CG URI
        cpc_oid = uri_parms[0]
        cpc_uri = '/api/cpcs/' + cpc_oid
        try:
            hmc.lookup_by_uri(cpc_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cg_oid = uri_parms[1]
        cg_uri = cpc_uri + '/capacity-groups/' + cg_oid

        try:
            capacity_group = hmc.lookup_by_uri(cg_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri, reason=150)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        check_required_fields(method, uri, body, ['partition-uri'])

        # Check the partition exists
        partition_uri = body['partition-uri']
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        # Check the partition is in this capacity group
        partition_uris = capacity_group.properties['partition-uris']
        if partition.uri not in partition_uris:
            raise ConflictError(method, uri, 140,
                                "Partition %s is not a member of "
                                "capacity group %s" %
                                (partition.name, capacity_group.name))

        # Reflect the result of removing the partition from the capacity group
        capacity_group.properties['partition-uris'].remove(partition.uri)


class LparsHandler(object):
    """
    Handler class for HTTP methods on set of Lpar resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Logical Partitions of CPC (empty result in DPM
        mode."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_lpars = []
        if not cpc.dpm_enabled:
            filter_args = parse_query_parms(method, uri, query_str)
            for lpar in cpc.lpars.list(filter_args):
                result_lpar = {}
                for prop in lpar.properties:
                    if prop in ('object-uri', 'name', 'status'):
                        result_lpar[prop] = lpar.properties[prop]
                result_lpars.append(result_lpar)
        return {'logical-partitions': result_lpars}


class LparHandler(GenericGetPropertiesHandler,
                  GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single Lpar resource.
    """
    pass


class LparActivateHandler(object):
    """
    A handler class for the "Activate Logical Partition" operation.
    """

    @staticmethod
    def get_status():
        """
        Status retrieval method that returns the status the faked Lpar will
        have after completion of the the "Activate Logical Partition"
        operation.

        This method returns the successful status 'not-operating', and can be
        mocked by testcases to return a different status (e.g. 'exceptions').
        """
        return 'not-operating'

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Activate Logical Partition (requires classic mode)."""
        assert wait_for_completion is True  # async not supported yet
        lpar_oid = uri_parms[0]
        lpar_uri = '/api/logical-partitions/' + lpar_oid
        try:
            lpar = hmc.lookup_by_uri(lpar_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = lpar.manager.parent
        assert not cpc.dpm_enabled

        status = lpar.properties.get('status', None)
        force = body.get('force', False) if body else False
        if status == 'operating' and not force:
            raise ServerError(method, uri, reason=263,
                              message="LPAR {!r} could not be activated "
                              "because the LPAR is in status {} "
                              "(and force was not specified).".
                              format(lpar.name, status))

        act_profile_name = body.get('activation-profile-name', None)
        if not act_profile_name:
            act_profile_name = lpar.properties.get(
                'next-activation-profile-name', None)
        if act_profile_name is None:
            act_profile_name = ''

        # Perform the check between LPAR name and profile name
        if act_profile_name != lpar.name:
            raise ServerError(method, uri, reason=263,
                              message="LPAR {!r} could not be activated "
                              "because the name of the image activation "
                              "profile {!r} is different from the LPAR name.".
                              format(lpar.name, act_profile_name))

        # Reflect the activation in the resource
        lpar.properties['status'] = LparActivateHandler.get_status()
        lpar.properties['last-used-activation-profile'] = act_profile_name


class LparDeactivateHandler(object):
    """
    A handler class for the "Deactivate Logical Partition" operation.
    """

    @staticmethod
    def get_status():
        """
        Status retrieval method that returns the status the faked Lpar will
        have after completion of the the "Deactivate Logical Partition"
        operation.

        This method returns the successful status 'not-activated', and can be
        mocked by testcases to return a different status (e.g. 'exceptions').
        """
        return 'not-activated'

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Deactivate Logical Partition (requires classic mode)."""
        assert wait_for_completion is True  # async not supported yet
        lpar_oid = uri_parms[0]
        lpar_uri = '/api/logical-partitions/' + lpar_oid
        try:
            lpar = hmc.lookup_by_uri(lpar_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = lpar.manager.parent
        assert not cpc.dpm_enabled

        status = lpar.properties.get('status', None)
        force = body.get('force', False) if body else False
        if status == 'not-activated' and not force:
            # Note that the current behavior (on EC12) is that force=True
            # still causes this error to be returned (different behavior
            # compared to the Activate and Load operations).
            raise ServerError(method, uri, reason=263,
                              message="LPAR {!r} could not be deactivated "
                              "because the LPAR is already deactivated "
                              "(and force was not specified).".
                              format(lpar.name))
        if status == 'operating' and not force:
            raise ServerError(method, uri, reason=263,
                              message="LPAR {!r} could not be deactivated "
                              "because the LPAR is in status {} "
                              "(and force was not specified).".
                              format(lpar.name, status))

        # Reflect the deactivation in the resource
        lpar.properties['status'] = LparDeactivateHandler.get_status()


class LparLoadHandler(object):
    """
    A handler class for the "Load Logical Partition" operation.
    """

    @staticmethod
    def get_status():
        """
        Status retrieval method that returns the status the faked Lpar will
        have after completion of the "Load Logical Partition" operation.

        This method returns the successful status 'operating', and can be
        mocked by testcases to return a different status (e.g. 'exceptions').
        """
        return 'operating'

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Load Logical Partition (requires classic mode)."""
        assert wait_for_completion is True  # async not supported yet
        lpar_oid = uri_parms[0]
        lpar_uri = '/api/logical-partitions/' + lpar_oid
        try:
            lpar = hmc.lookup_by_uri(lpar_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = lpar.manager.parent
        assert not cpc.dpm_enabled

        status = lpar.properties.get('status', None)
        force = body.get('force', False) if body else False
        clear_indicator = body.get('clear-indicator', True) if body else True
        store_status_indicator = body.get('store-status-indicator',
                                          False) if body else False
        if status == 'not-activated':
            raise ConflictError(method, uri, reason=0,
                                message="LPAR {!r} could not be loaded "
                                "because the LPAR is in status {}.".
                                format(lpar.name, status))
        if status == 'operating' and not force:
            raise ServerError(method, uri, reason=263,
                              message="LPAR {!r} could not be loaded "
                              "because the LPAR is already loaded "
                              "(and force was not specified).".
                              format(lpar.name))

        load_address = body.get('load-address', None) if body else None
        if not load_address:
            # Starting with z14, this parameter is optional and a last-used
            # property is available.
            load_address = lpar.properties.get('last-used-load-address', None)
        if load_address is None:
            # TODO: Verify actual error for this case on a z14.
            raise BadRequestError(method, uri, reason=5,
                                  message="LPAR {!r} could not be loaded "
                                  "because a load address is not specified "
                                  "in the request or in the Lpar last-used "
                                  "property".
                                  format(lpar.name))

        load_parameter = body.get('load-parameter', None) if body else None
        if not load_parameter:
            # Starting with z14, a last-used property is available.
            load_parameter = lpar.properties.get(
                'last-used-load-parameter', None)
        if load_parameter is None:
            load_parameter = ''

        # Reflect the load in the resource
        if clear_indicator:
            lpar.properties['memory'] = ''

        if store_status_indicator:
            lpar.properties['stored-status'] = status
        else:
            lpar.properties['stored-status'] = None
        lpar.properties['status'] = LparLoadHandler.get_status()
        lpar.properties['last-used-load-address'] = load_address
        lpar.properties['last-used-load-parameter'] = load_parameter


class ResetActProfilesHandler(object):
    """
    Handler class for HTTP methods on set of ResetActProfile resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Reset Activation Profiles (requires classic
        mode)."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        assert not cpc.dpm_enabled  # TODO: Verify error or empty result?
        result_profiles = []
        filter_args = parse_query_parms(method, uri, query_str)
        for profile in cpc.reset_activation_profiles.list(filter_args):
            result_profile = {}
            for prop in profile.properties:
                if prop in ('element-uri', 'name'):
                    result_profile[prop] = profile.properties[prop]
            result_profiles.append(result_profile)
        return {'reset-activation-profiles': result_profiles}


class ResetActProfileHandler(GenericGetPropertiesHandler,
                             GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single ResetActProfile resource.
    """
    pass


class ImageActProfilesHandler(object):
    """
    Handler class for HTTP methods on set of ImageActProfile resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Image Activation Profiles (requires classic
        mode)."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        assert not cpc.dpm_enabled  # TODO: Verify error or empty result?
        result_profiles = []
        filter_args = parse_query_parms(method, uri, query_str)
        for profile in cpc.image_activation_profiles.list(filter_args):
            result_profile = {}
            for prop in profile.properties:
                if prop in ('element-uri', 'name'):
                    result_profile[prop] = profile.properties[prop]
            result_profiles.append(result_profile)
        return {'image-activation-profiles': result_profiles}


class ImageActProfileHandler(GenericGetPropertiesHandler,
                             GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single ImageActProfile resource.
    """
    pass


class LoadActProfilesHandler(object):
    """
    Handler class for HTTP methods on set of LoadActProfile resources.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Load Activation Profiles (requires classic mode)."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        assert not cpc.dpm_enabled  # TODO: Verify error or empty result?
        result_profiles = []
        filter_args = parse_query_parms(method, uri, query_str)
        for profile in cpc.load_activation_profiles.list(filter_args):
            result_profile = {}
            for prop in profile.properties:
                if prop in ('element-uri', 'name'):
                    result_profile[prop] = profile.properties[prop]
            result_profiles.append(result_profile)
        return {'load-activation-profiles': result_profiles}


class LoadActProfileHandler(GenericGetPropertiesHandler,
                            GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single LoadActProfile resource.
    """
    pass


# URIs to be handled
# Note: This list covers only the HMC operations implemented in the zhmcclient.
# The HMC supports several more operations.
URIS = (
    # (uri_regexp, handler_class)

    # In all modes:

    (r'/api/version', VersionHandler),

    (r'/api/console', ConsoleHandler),
    (r'/api/console/operations/restart', ConsoleRestartHandler),
    (r'/api/console/operations/shutdown', ConsoleShutdownHandler),
    (r'/api/console/operations/make-primary', ConsoleMakePrimaryHandler),
    (r'/api/console/operations/reorder-user-patterns',
     ConsoleReorderUserPatternsHandler),
    (r'/api/console/operations/get-audit-log(?:\?(.*))?',
     ConsoleGetAuditLogHandler),
    (r'/api/console/operations/get-security-log(?:\?(.*))?',
     ConsoleGetSecurityLogHandler),
    (r'/api/console/operations/list-unmanaged-cpcs(?:\?(.*))?',
     ConsoleListUnmanagedCpcsHandler),
    (r'/api/console/operations/list-permitted-partitions(?:\?(.*))?',
     ConsoleListPermittedPartitionsHandler),
    (r'/api/console/operations/list-permitted-logical-partitions(?:\?(.*))?',
     ConsoleListPermittedLparsHandler),

    (r'/api/console/users(?:\?(.*))?', UsersHandler),
    (r'/api/users/([^/]+)', UserHandler),
    (r'/api/users/([^/]+)/operations/add-user-role',
     UserAddUserRoleHandler),
    (r'/api/users/([^/]+)/operations/remove-user-role',
     UserRemoveUserRoleHandler),

    (r'/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
    (r'/api/user-roles/([^/]+)', UserRoleHandler),
    (r'/api/user-roles/([^/]+)/operations/add-permission',
     UserRoleAddPermissionHandler),
    (r'/api/user-roles/([^/]+)/operations/remove-permission',
     UserRoleRemovePermissionHandler),

    (r'/api/console/tasks(?:\?(.*))?', TasksHandler),
    (r'/api/console/tasks/([^/]+)', TaskHandler),

    (r'/api/console/user-patterns(?:\?(.*))?', UserPatternsHandler),
    (r'/api/console/user-patterns/([^/]+)', UserPatternHandler),

    (r'/api/console/password-rules(?:\?(.*))?', PasswordRulesHandler),
    (r'/api/console/password-rules/([^/]+)', PasswordRuleHandler),

    (r'/api/console/ldap-server-definitions(?:\?(.*))?',
     LdapServerDefinitionsHandler),
    (r'/api/console/ldap-server-definitions/([^/]+)',
     LdapServerDefinitionHandler),

    (r'/api/cpcs(?:\?(.*))?', CpcsHandler),
    (r'/api/cpcs/([^/]+)', CpcHandler),
    (r'/api/cpcs/([^/]+)/operations/set-cpc-power-save',
     CpcSetPowerSaveHandler),
    (r'/api/cpcs/([^/]+)/operations/set-cpc-power-capping',
     CpcSetPowerCappingHandler),
    (r'/api/cpcs/([^/]+)/energy-management-data',
     CpcGetEnergyManagementDataHandler),

    (r'/api/services/metrics/context', MetricsContextsHandler),
    (r'/api/services/metrics/context/([^/]+)', MetricsContextHandler),

    # Only in DPM mode:

    (r'/api/cpcs/([^/]+)/operations/start', CpcStartHandler),
    (r'/api/cpcs/([^/]+)/operations/stop', CpcStopHandler),
    (r'/api/cpcs/([^/]+)/operations/export-port-names-list',
     CpcExportPortNamesListHandler),

    (r'/api/cpcs/([^/]+)/adapters(?:\?(.*))?', AdaptersHandler),
    (r'/api/adapters/([^/]+)', AdapterHandler),
    (r'/api/adapters/([^/]+)/operations/change-crypto-type',
     AdapterChangeCryptoTypeHandler),
    (r'/api/adapters/([^/]+)/operations/change-adapter-type',
     AdapterChangeAdapterTypeHandler),

    (r'/api/adapters/([^/]+)/network-ports/([^/]+)', NetworkPortHandler),

    (r'/api/adapters/([^/]+)/storage-ports/([^/]+)', StoragePortHandler),

    (r'/api/cpcs/([^/]+)/partitions(?:\?(.*))?', PartitionsHandler),
    (r'/api/partitions/([^/]+)', PartitionHandler),
    (r'/api/partitions/([^/]+)/operations/start', PartitionStartHandler),
    (r'/api/partitions/([^/]+)/operations/stop', PartitionStopHandler),
    (r'/api/partitions/([^/]+)/operations/scsi-dump',
     PartitionScsiDumpHandler),
    (r'/api/partitions/([^/]+)/operations/start-dump-program',
     PartitionStartDumpProgramHandler),
    (r'/api/partitions/([^/]+)/operations/psw-restart',
     PartitionPswRestartHandler),
    (r'/api/partitions/([^/]+)/operations/mount-iso-image(?:\?(.*))?',
     PartitionMountIsoImageHandler),
    (r'/api/partitions/([^/]+)/operations/unmount-iso-image',
     PartitionUnmountIsoImageHandler),
    (r'/api/partitions/([^/]+)/operations/increase-crypto-configuration',
     PartitionIncreaseCryptoConfigHandler),
    (r'/api/partitions/([^/]+)/operations/decrease-crypto-configuration',
     PartitionDecreaseCryptoConfigHandler),
    (r'/api/partitions/([^/]+)/operations/change-crypto-domain-configuration',
     PartitionChangeCryptoConfigHandler),

    (r'/api/partitions/([^/]+)/hbas(?:\?(.*))?', HbasHandler),
    (r'/api/partitions/([^/]+)/hbas/([^/]+)', HbaHandler),
    (r'/api/partitions/([^/]+)/hbas/([^/]+)/operations/'\
     'reassign-storage-adapter-port', HbaReassignPortHandler),

    (r'/api/partitions/([^/]+)/nics(?:\?(.*))?', NicsHandler),
    (r'/api/partitions/([^/]+)/nics/([^/]+)', NicHandler),

    (r'/api/partitions/([^/]+)/virtual-functions(?:\?(.*))?',
     VirtualFunctionsHandler),
    (r'/api/partitions/([^/]+)/virtual-functions/([^/]+)',
     VirtualFunctionHandler),

    (r'/api/cpcs/([^/]+)/virtual-switches(?:\?(.*))?', VirtualSwitchesHandler),
    (r'/api/virtual-switches/([^/]+)', VirtualSwitchHandler),
    (r'/api/virtual-switches/([^/]+)/operations/get-connected-vnics',
     VirtualSwitchGetVnicsHandler),

    (r'/api/storage-groups(?:\?(.*))?', StorageGroupsHandler),
    (r'/api/storage-groups/([^/]+)', StorageGroupHandler),
    (r'/api/storage-groups/([^/]+)/operations/delete',
     StorageGroupDeleteHandler),
    (r'/api/storage-groups/([^/]+)/operations/modify',
     StorageGroupModifyHandler),
    (r'/api/storage-groups/([^/]+)/operations/request-fulfillment',
     StorageGroupRequestFulfillmentHandler),
    (r'/api/storage-groups/([^/]+)/operations/add-candidate-adapter-ports',
     StorageGroupAddCandidatePortsHandler),
    (r'/api/storage-groups/([^/]+)/operations/remove-candidate-adapter-ports',
     StorageGroupRemoveCandidatePortsHandler),

    (r'/api/cpcs/([^/]+)/capacity-groups(?:\?(.*))?', CapacityGroupsHandler),
    (r'/api/cpcs/([^/]+)/capacity-groups/([^/]+)', CapacityGroupHandler),
    (r'/api/cpcs/([^/]+)/capacity-groups/([^/]+)/operations/add-partition',
     CapacityGroupAddPartitionHandler),
    (r'/api/cpcs/([^/]+)/capacity-groups/([^/]+)/operations/remove-partition',
     CapacityGroupRemovePartitionHandler),

    # Only in classic (or ensemble) mode:

    (r'/api/cpcs/([^/]+)/operations/import-profiles',
     CpcImportProfilesHandler),
    (r'/api/cpcs/([^/]+)/operations/export-profiles',
     CpcExportProfilesHandler),

    (r'/api/cpcs/([^/]+)/operations/add-temp-capacity',
     CpcAddTempCapacityHandler),
    (r'/api/cpcs/([^/]+)/operations/remove-temp-capacity',
     CpcRemoveTempCapacityHandler),

    (r'/api/cpcs/([^/]+)/logical-partitions(?:\?(.*))?', LparsHandler),
    (r'/api/logical-partitions/([^/]+)', LparHandler),
    (r'/api/logical-partitions/([^/]+)/operations/activate',
     LparActivateHandler),
    (r'/api/logical-partitions/([^/]+)/operations/deactivate',
     LparDeactivateHandler),
    (r'/api/logical-partitions/([^/]+)/operations/load', LparLoadHandler),

    (r'/api/cpcs/([^/]+)/reset-activation-profiles(?:\?(.*))?',
     ResetActProfilesHandler),
    (r'/api/cpcs/([^/]+)/reset-activation-profiles/([^/]+)',
     ResetActProfileHandler),

    (r'/api/cpcs/([^/]+)/image-activation-profiles(?:\?(.*))?',
     ImageActProfilesHandler),
    (r'/api/cpcs/([^/]+)/image-activation-profiles/([^/]+)',
     ImageActProfileHandler),

    (r'/api/cpcs/([^/]+)/load-activation-profiles(?:\?(.*))?',
     LoadActProfilesHandler),
    (r'/api/cpcs/([^/]+)/load-activation-profiles/([^/]+)',
     LoadActProfileHandler),
)
