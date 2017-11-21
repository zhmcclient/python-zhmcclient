# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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

    def __init__(self, method, uri, http_status, reason, message):
        self.method = method
        self.uri = uri
        self.http_status = http_status
        self.reason = reason
        self.message = message

    def response(self):
        return {
            'request-method': self.method,
            'request-uri': self.uri,
            'http-status': self.http_status,
            'reason': self.reason,
            'message': self.message,
        }


class ConnectionError(Exception):

    def __init__(self, message):
        self.message = message


class InvalidResourceError(HTTPError):

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

    def __init__(self, method, uri, reason, message):
        super(BadRequestError, self).__init__(
            method, uri,
            http_status=400,
            reason=reason,
            message=message)


class ConflictError(HTTPError):

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
        else:
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
        else:
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
        for uri_pattern, handler_class in self._uri_handlers:
            m = uri_pattern.match(uri)
            if m:
                uri_parms = m.groups()
                return handler_class, uri_parms
        raise InvalidResourceError(method, uri)

    def get(self, hmc, uri, logon_required):
        if not hmc.enabled:
            raise ConnectionError("HMC is not enabled.")
        handler_class, uri_parms = self.handler(uri, 'GET')
        if not getattr(handler_class, 'get', None):
            raise InvalidMethodError('GET', uri, handler_class)
        return handler_class.get('GET', hmc, uri, uri_parms, logon_required)

    def post(self, hmc, uri, body, logon_required, wait_for_completion):
        if not hmc.enabled:
            raise ConnectionError("HMC is not enabled.")
        handler_class, uri_parms = self.handler(uri, 'POST')
        if not getattr(handler_class, 'post', None):
            raise InvalidMethodError('POST', uri, handler_class)
        return handler_class.post('POST', hmc, uri, uri_parms, body,
                                  logon_required, wait_for_completion)

    def delete(self, hmc, uri, logon_required):
        if not hmc.enabled:
            raise ConnectionError("HMC is not enabled.")
        handler_class, uri_parms = self.handler(uri, 'DELETE')
        if not getattr(handler_class, 'delete', None):
            raise InvalidMethodError('DELETE', uri, handler_class)
        handler_class.delete('DELETE', hmc, uri, uri_parms, logon_required)


class GenericGetPropertiesHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: Get <resource> Properties."""
        try:
            resource = hmc.lookup_by_uri(uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        return resource.properties


class GenericUpdatePropertiesHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Update <resource> Properties."""
        assert wait_for_completion is True  # async not supported yet
        try:
            resource = hmc.lookup_by_uri(uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        resource.update(body)


class GenericDeleteHandler(object):

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        """Operation: Delete <resource>."""
        try:
            resource = hmc.lookup_by_uri(uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        resource.manager.remove(resource.oid)


class VersionHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        api_major, api_minor = hmc.api_version.split('.')
        return {
            'hmc-name': hmc.hmc_name,
            'hmc-version': hmc.hmc_version,
            'api-major-version': int(api_major),
            'api-minor-version': int(api_minor),
        }


class ConsoleHandler(GenericGetPropertiesHandler):
    pass


class ConsoleRestartHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Restart Console."""
        assert wait_for_completion is True  # synchronous operation
        console_uri = '/api/console'
        try:
            hmc.lookup_by_uri(console_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        hmc.disable()
        time.sleep(5)
        hmc.enable()
        # Note: The HTTP status 202 that the real HMC operation returns, is
        # not visible for the caller of FakedSession (or Session).


class ConsoleShutdownHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Shutdown Console."""
        assert wait_for_completion is True  # synchronous operation
        console_uri = '/api/console'
        try:
            hmc.lookup_by_uri(console_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        hmc.disable()
        # Note: The HTTP status 202 that the real HMC operation returns, is
        # not visible for the caller of FakedSession (or Session).


class ConsoleMakePrimaryHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Make Console Primary."""
        assert wait_for_completion is True  # synchronous operation
        console_uri = '/api/console'
        try:
            hmc.lookup_by_uri(console_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        # Nothing to do, as long as the faked HMC does not need to know whether
        # it is primary or alternate.


class ConsoleReorderUserPatternsHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Reorder User Patterns."""
        assert wait_for_completion is True  # synchronous operation
        console_uri = '/api/console'
        try:
            console = hmc.lookup_by_uri(console_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        check_required_fields(method, uri, body, ['user-pattern-uris'])
        new_order_uris = body['user-pattern-uris']
        objs = console.user_patterns.list()
        obj_by_uri = {}
        for obj in objs:
            obj_by_uri[obj.uri] = obj
        # Perform the reordering in the faked HMC:
        for uri in new_order_uris:
            obj = obj_by_uri[uri]
            console.user_patterns.remove(obj.oid)  # remove from old position
            console.user_patterns.add(obj.properties)  # append to end


class ConsoleGetAuditLogHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Get Console Audit Log."""
        assert wait_for_completion is True  # synchronous operation
        console_uri = '/api/console'
        try:
            hmc.lookup_by_uri(console_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        resp = []
        # TODO: Add the ability to return audit log entries in mock support.
        return resp


class ConsoleGetSecurityLogHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Get Console Security Log."""
        assert wait_for_completion is True  # synchronous operation
        console_uri = '/api/console'
        try:
            hmc.lookup_by_uri(console_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        resp = []
        # TODO: Add the ability to return security log entries in mock support.
        return resp


class ConsoleListUnmanagedCpcsHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List Unmanaged CPCs."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            raise InvalidResourceError(method, uri)

        result_ucpcs = []
        filter_args = parse_query_parms(method, uri, query_str)
        for ucpc in console.unmanaged_cpcs.list(filter_args):
            result_ucpc = {}
            for prop in ucpc.properties:
                if prop in ('object-uri', 'name'):
                    result_ucpc[prop] = ucpc.properties[prop]
            result_ucpcs.append(result_ucpc)
        return {'cpcs': result_ucpcs}


class UsersHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List Users."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
        """Operation: Create User."""
        assert wait_for_completion is True  # synchronous operation
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            raise InvalidResourceError(method, uri)
        check_required_fields(method, uri, body,
                              ['name', 'type', 'authentication-type'])
        # TODO: There are some more input properties that are required under
        # certain conditions.
        new_user = console.users.add(body)
        return {'object-uri': new_user.uri}


class UserHandler(GenericGetPropertiesHandler,
                  GenericUpdatePropertiesHandler):

    # TODO: Add post() for Update User that rejects name update

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        """Operation: Delete User."""
        try:
            user = hmc.lookup_by_uri(uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Add User Role to User."""
        assert wait_for_completion is True  # synchronous operation
        user_oid = uri_parms[0]
        user_uri = '/api/users/' + user_oid
        try:
            user = hmc.lookup_by_uri(user_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
            raise InvalidResourceError(method, user_role_uri, reason=2)
        if user.properties.get('user-roles', None) is None:
            user.properties['user-roles'] = []
        user.properties['user-roles'].append(user_role_uri)


class UserRemoveUserRoleHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Remove User Role from User."""
        assert wait_for_completion is True  # synchronous operation
        user_oid = uri_parms[0]
        user_uri = '/api/users/' + user_oid
        try:
            user = hmc.lookup_by_uri(user_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
            raise InvalidResourceError(method, user_role_uri, reason=2)
        if user.properties.get('user-roles', None) is None \
                or user_role_uri not in user.properties['user-roles']:
            raise ConflictError(
                method, uri, reason=316,
                message="User {!r} does not have User Role {!r}".
                format(user.name, user_role.name))
        user.properties['user-roles'].remove(user_role_uri)


class UserRolesHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List User Roles."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
        """Operation: Create User Role."""
        assert wait_for_completion is True  # synchronous operation
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
    pass
    # TODO: Add post() for Update UserRole that rejects name update
    # TODO: Add delete() for Delete UserRole that rejects system-defined type


class UserRoleAddPermissionHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Add Permission to User Role."""
        assert wait_for_completion is True  # synchronous operation
        user_role_oid = uri_parms[0]
        user_role_uri = '/api/user-roles/' + user_role_oid
        try:
            user_role = hmc.lookup_by_uri(user_role_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Remove Permission from User Role."""
        assert wait_for_completion is True  # synchronous operation
        user_role_oid = uri_parms[0]
        user_role_uri = '/api/user-roles/' + user_role_oid
        try:
            user_role = hmc.lookup_by_uri(user_role_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List Tasks."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
    pass


class UserPatternsHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List User Patterns."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
        """Operation: Create User Pattern."""
        assert wait_for_completion is True  # synchronous operation
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            raise InvalidResourceError(method, uri)
        check_required_fields(method, uri, body,
                              ['name', 'pattern', 'type', 'retention-time',
                               'user-template-uri'])
        new_user_pattern = console.user_patterns.add(body)
        return {'element-uri': new_user_pattern.uri}


class UserPatternHandler(GenericGetPropertiesHandler,
                         GenericUpdatePropertiesHandler,
                         GenericDeleteHandler):
    pass


class PasswordRulesHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List Password Rules."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
        """Operation: Create Password Rule."""
        assert wait_for_completion is True  # synchronous operation
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            raise InvalidResourceError(method, uri)
        check_required_fields(method, uri, body, ['name'])
        new_password_rule = console.password_rules.add(body)
        return {'element-uri': new_password_rule.uri}


class PasswordRuleHandler(GenericGetPropertiesHandler,
                          GenericUpdatePropertiesHandler,
                          GenericDeleteHandler):
    pass
    # TODO: Add post() for Update PasswordRule that rejects name update


class LdapServerDefinitionsHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List LDAP Server Definitions."""
        query_str = uri_parms[0]
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
        """Operation: Create LDAP Server Definition."""
        assert wait_for_completion is True  # synchronous operation
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            raise InvalidResourceError(method, uri)
        check_required_fields(method, uri, body, ['name'])
        new_ldap_srv_def = console.ldap_server_definitions.add(body)
        return {'element-uri': new_ldap_srv_def.uri}


class LdapServerDefinitionHandler(GenericGetPropertiesHandler,
                                  GenericUpdatePropertiesHandler,
                                  GenericDeleteHandler):
    pass
    # TODO: Add post() for Update LdapServerDefinition that rejects name update


class CpcsHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
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
    pass


class CpcSetPowerSaveHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Set CPC Power Save (any CPC mode)."""
        assert wait_for_completion is True  # async not supported yet
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Set CPC Power Capping (any CPC mode)."""
        assert wait_for_completion is True  # async not supported yet
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: Get CPC Energy Management Data (any CPC mode)."""
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)

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

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Start CPC (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        cpc.properties['status'] = 'active'


class CpcStopHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Stop CPC (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        cpc.properties['status'] = 'not-operating'


class CpcImportProfilesHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Import Profiles (requires classic mode)."""
        assert wait_for_completion is True  # no async
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)
        check_required_fields(method, uri, body, ['profile-area'])
        # TODO: Import the CPC profiles from a simulated profile area


class CpcExportProfilesHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Export Profiles (requires classic mode)."""
        assert wait_for_completion is True  # no async
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)
        check_required_fields(method, uri, body, ['profile-area'])
        # TODO: Export the CPC profiles to a simulated profile area


class CpcExportPortNamesListHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Export WWPN List (requires DPM mode)."""
        assert wait_for_completion is True  # this operation is always synchr.
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
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


class MetricsContextsHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
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

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        """Operation: Delete Metrics Context."""
        try:
            metrics_context = hmc.lookup_by_uri(uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        hmc.metrics_contexts.remove(metrics_context.oid)

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: Get Metrics."""
        try:
            metrics_context = hmc.lookup_by_uri(uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        result = metrics_context.get_metric_values_response()
        return result


class AdaptersHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List Adapters of a CPC (empty result if not in DPM
        mode)."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
        """Operation: Create Hipersocket (requires DPM mode)."""
        assert wait_for_completion is True
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
            raise BadRequestError(method, uri, reason=5, message=str(exc))
        return {'object-uri': new_adapter.uri}


class AdapterHandler(GenericGetPropertiesHandler,
                     GenericUpdatePropertiesHandler):

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        """Operation: Delete Hipersocket (requires DPM mode)."""
        try:
            adapter = hmc.lookup_by_uri(uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        cpc = adapter.manager.parent
        assert cpc.dpm_enabled
        adapter.manager.remove(adapter.oid)


class AdapterChangeCryptoTypeHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Change Crypto Type (requires DPM mode)."""
        assert wait_for_completion is True  # HMC operation is synchronous
        adapter_uri = uri.split('/operations/')[0]
        try:
            adapter = hmc.lookup_by_uri(adapter_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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


class NetworkPortHandler(GenericGetPropertiesHandler,
                         GenericUpdatePropertiesHandler):
    pass


class StoragePortHandler(GenericGetPropertiesHandler,
                         GenericUpdatePropertiesHandler):
    pass


class PartitionsHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List Partitions of a CPC (empty result if not in DPM
        mode)."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)

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
        """Operation: Create Partition (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

    # TODO: Add check_valid_cpc_status() in Update Partition Properties
    # TODO: Add check_partition_status(transitional) in Update Partition Props

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        """Operation: Delete Partition."""
        try:
            partition = hmc.lookup_by_uri(uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['stopped'])

        # Reflect the result of deleting the partition
        partition.manager.remove(partition.oid)


class PartitionStartHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Start Partition (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['stopped'])

        # Reflect the result of starting the partition
        partition.properties['status'] = 'active'
        return {}


class PartitionStopHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Stop Partition (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Dump Partition (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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


class PartitionPswRestartHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Perform PSW Restart (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['active', 'paused',
                                               'terminated'])

        # We don't reflect the PSW restart in the mock state.
        return {}


class PartitionMountIsoImageHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Mount ISO Image (requires DPM mode)."""
        assert wait_for_completion is True  # synchronous operation
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
            raise BadRequestError(
                method, uri, reason=1,
                message="Missing required URI query parameter 'image-name'")
        try:
            ins_file_name = query_parms['ins-file-name']
        except KeyError:
            raise BadRequestError(
                method, uri, reason=1,
                message="Missing required URI query parameter 'ins-file-name'")

        # Reflect the effect of mounting in the partition properties
        partition.properties['boot-iso-image-name'] = image_name
        partition.properties['boot-iso-ins-file'] = ins_file_name
        return {}


class PartitionUnmountIsoImageHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Perform PSW Restart (requires DPM mode)."""
        assert wait_for_completion is True  # synchronous operation
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Increase Crypto Configuration (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

        for uri in add_adapter_uris:
            if uri not in adapter_uris:
                adapter_uris.append(uri)
        for dc in add_domain_configs:
            if dc not in domain_configs:
                domain_configs.append(dc)


class PartitionDecreaseCryptoConfigHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Decrease Crypto Configuration (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

        for uri in remove_adapter_uris:
            if uri in adapter_uris:
                adapter_uris.remove(uri)
        for remove_di in remove_domain_indexes:
            for i, dc in enumerate(domain_configs):
                if dc['domain-index'] == remove_di:
                    del domain_configs[i]


class PartitionChangeCryptoConfigHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Change Crypto Configuration (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])
        check_required_fields(method, uri, body,
                              ['domain-index', 'access-mode'])

        adapter_uris, domain_configs = ensure_crypto_config(partition)

        change_domain_index = body['domain-index']
        change_access_mode = body['access-mode']

        # We don't support finding errors in this simple-minded mock support,
        # so we assume that the input is fine (e.g. no invalid domain indexes)
        # and we just change it.

        for i, dc in enumerate(domain_configs):
            if dc['domain-index'] == change_domain_index:
                dc['access-mode'] = change_access_mode


class HbasHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Create HBA (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_uri = re.sub('/hbas$', '', uri)
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
            raise InvalidResourceError(method, uri, reason=2,
                                       resource_uri=adapter_uri)
        try:
            hmc.lookup_by_uri(port_uri)
        except KeyError:
            raise InvalidResourceError(method, uri, reason=6,
                                       resource_uri=port_uri)

        new_hba = partition.hbas.add(body)

        return {'element-uri': new_hba.uri}


class HbaHandler(GenericGetPropertiesHandler,
                 GenericUpdatePropertiesHandler):

    # TODO: Add check_valid_cpc_status() in Update HBA Properties
    # TODO: Add check_partition_status(transitional) in Update HBA Properties

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        """Operation: Delete HBA (requires DPM mode)."""
        try:
            hba = hmc.lookup_by_uri(uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        partition = hba.manager.parent
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])

        partition.hbas.remove(hba.oid)


class HbaReassignPortHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Reassign Storage Adapter Port (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_oid = uri_parms[0]
        partition_uri = '/api/partitions/' + partition_oid
        hba_oid = uri_parms[1]
        hba_uri = '/api/partitions/' + partition_oid + '/hbas/' + hba_oid
        try:
            hba = hmc.lookup_by_uri(hba_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Create NIC (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_uri = re.sub('/nics$', '', uri)
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
                raise InvalidResourceError(method, uri, reason=2,
                                           resource_uri=adapter_uri)
            try:
                hmc.lookup_by_uri(port_uri)
            except KeyError:
                raise InvalidResourceError(method, uri, reason=6,
                                           resource_uri=port_uri)
        elif 'virtual-switch-uri' in body:
            vswitch_uri = body['virtual-switch-uri']
            try:
                hmc.lookup_by_uri(vswitch_uri)
            except KeyError:
                raise InvalidResourceError(method, uri, reason=2,
                                           resource_uri=vswitch_uri)
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

    # TODO: Add check_valid_cpc_status() in Update NIC Properties
    # TODO: Add check_partition_status(transitional) in Update NIC Properties

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        """Operation: Delete NIC (requires DPM mode)."""
        try:
            nic = hmc.lookup_by_uri(uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        partition = nic.manager.parent
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])

        partition.nics.remove(nic.oid)


class VirtualFunctionsHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Create Virtual Function (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        partition_uri = re.sub('/virtual-functions$', '', uri)
        try:
            partition = hmc.lookup_by_uri(partition_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

    # TODO: Add check_valid_cpc_status() in Update VF Properties
    # TODO: Add check_partition_status(transitional) in Update VF Properties

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        """Operation: Delete Virtual Function (requires DPM mode)."""
        try:
            vf = hmc.lookup_by_uri(uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        partition = vf.manager.parent
        cpc = partition.manager.parent
        assert cpc.dpm_enabled
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])

        partition.virtual_functions.remove(vf.oid)


class VirtualSwitchesHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List Virtual Switches of a CPC (empty result if not in
        DPM mode)."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
    pass


class VirtualSwitchGetVnicsHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Get Connected VNICs of a Virtual Switch
        (requires DPM mode)."""
        assert wait_for_completion is True  # async not supported yet
        vswitch_oid = uri_parms[0]
        vswitch_uri = '/api/virtual-switches/' + vswitch_oid
        try:
            vswitch = hmc.lookup_by_uri(vswitch_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        cpc = vswitch.manager.parent
        assert cpc.dpm_enabled

        connected_vnic_uris = vswitch.properties['connected-vnic-uris']
        return {'connected-vnic-uris': connected_vnic_uris}


class StorageGroupsHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
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
        """Operation: Create Storage Group."""
        assert wait_for_completion is True  # async not supported yet
        check_required_fields(method, uri, body, ['name', 'cpc-uri', 'type'])
        cpc_uri = body['cpc-uri']
        try:
            cpc = hmc.lookup_by_uri(cpc_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
    pass


class StorageGroupModifyHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Modify Storage Group Properties."""
        assert wait_for_completion is True  # async not supported yet
        # The URI is a POST operation, so we need to construct the SG URI
        storage_group_oid = uri_parms[0]
        storage_group_uri = '/api/storage-groups/' + storage_group_oid
        try:
            storage_group = hmc.lookup_by_uri(storage_group_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)

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

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Delete Storage Group."""
        assert wait_for_completion is True  # async not supported yet
        # The URI is a POST operation, so we need to construct the SG URI
        storage_group_oid = uri_parms[0]
        storage_group_uri = '/api/storage-groups/' + storage_group_oid
        try:
            storage_group = hmc.lookup_by_uri(storage_group_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)

        # TODO: Check that the SG is detached from any partitions

        # Reflect the result of deleting the storage_group
        storage_group.manager.remove(storage_group.oid)


class StorageGroupRequestFulfillmentHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Request Storage Group Fulfillment."""
        assert wait_for_completion is True  # async not supported yet
        # The URI is a POST operation, so we need to construct the SG URI
        storage_group_oid = uri_parms[0]
        storage_group_uri = '/api/storage-groups/' + storage_group_oid
        try:
            hmc.lookup_by_uri(storage_group_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)

        # Reflect the result of requesting fulfilment for the storage group
        pass


class StorageGroupAddCandidatePortsHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Add Candidate Adapter Ports to an FCP Storage Group."""
        assert wait_for_completion is True  # async not supported yet
        # The URI is a POST operation, so we need to construct the SG URI
        storage_group_oid = uri_parms[0]
        storage_group_uri = '/api/storage-groups/' + storage_group_oid
        try:
            storage_group = hmc.lookup_by_uri(storage_group_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)

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
            else:
                candidate_adapter_port_uris.append(ap_uri)


class StorageGroupRemoveCandidatePortsHandler(object):

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        """Operation: Remove Candidate Adapter Ports from an FCP Storage
        Group."""
        assert wait_for_completion is True  # async not supported yet
        # The URI is a POST operation, so we need to construct the SG URI
        storage_group_oid = uri_parms[0]
        storage_group_uri = '/api/storage-groups/' + storage_group_oid
        try:
            storage_group = hmc.lookup_by_uri(storage_group_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)

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
            else:
                candidate_adapter_port_uris.remove(ap_uri)


class LparsHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List Logical Partitions of CPC (empty result in DPM
        mode."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
        """Operation: Activate Logical Partition (requires classic mode)."""
        assert wait_for_completion is True  # async not supported yet
        lpar_oid = uri_parms[0]
        lpar_uri = '/api/logical-partitions/' + lpar_oid
        try:
            lpar = hmc.lookup_by_uri(lpar_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
        """Operation: Deactivate Logical Partition (requires classic mode)."""
        assert wait_for_completion is True  # async not supported yet
        lpar_oid = uri_parms[0]
        lpar_uri = '/api/logical-partitions/' + lpar_oid
        try:
            lpar = hmc.lookup_by_uri(lpar_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
        elif status == 'operating' and not force:
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
        """Operation: Load Logical Partition (requires classic mode)."""
        assert wait_for_completion is True  # async not supported yet
        lpar_oid = uri_parms[0]
        lpar_uri = '/api/logical-partitions/' + lpar_oid
        try:
            lpar = hmc.lookup_by_uri(lpar_uri)
        except KeyError:
            raise InvalidResourceError(method, uri)
        cpc = lpar.manager.parent
        assert not cpc.dpm_enabled

        status = lpar.properties.get('status', None)
        force = body.get('force', False) if body else False
        if status == 'not-activated':
            raise ConflictError(method, uri, reason=0,
                                message="LPAR {!r} could not be loaded "
                                "because the LPAR is in status {}.".
                                format(lpar.name, status))
        elif status == 'operating' and not force:
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
        lpar.properties['status'] = LparLoadHandler.get_status()
        lpar.properties['last-used-load-address'] = load_address
        lpar.properties['last-used-load-parameter'] = load_parameter


class ResetActProfilesHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List Reset Activation Profiles (requires classic
        mode)."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
    pass


class ImageActProfilesHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List Image Activation Profiles (requires classic
        mode)."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
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
    pass


class LoadActProfilesHandler(object):

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        """Operation: List Load Activation Profiles (requires classic mode)."""
        cpc_oid = uri_parms[0]
        query_str = uri_parms[1]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            raise InvalidResourceError(method, uri)
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

    (r'/api/adapters/([^/]+)/network-ports/([^/]+)', NetworkPortHandler),

    (r'/api/adapters/([^/]+)/storage-ports/([^/]+)', StoragePortHandler),

    (r'/api/cpcs/([^/]+)/partitions(?:\?(.*))?', PartitionsHandler),
    (r'/api/partitions/([^/]+)', PartitionHandler),
    (r'/api/partitions/([^/]+)/operations/start', PartitionStartHandler),
    (r'/api/partitions/([^/]+)/operations/stop', PartitionStopHandler),
    (r'/api/partitions/([^/]+)/operations/scsi-dump',
     PartitionScsiDumpHandler),
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

    # Only in classic (or ensemble) mode:

    (r'/api/cpcs/([^/]+)/operations/import-profiles',
     CpcImportProfilesHandler),
    (r'/api/cpcs/([^/]+)/operations/export-profiles',
     CpcExportProfilesHandler),

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
