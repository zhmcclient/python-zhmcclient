# Copyright 2016,2021 IBM Corp. All Rights Reserved.
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


import re
import time
import copy
import uuid
from random import randrange
from requests.utils import unquote

from zhmcclient._exceptions import HTTPError as HTTPError_zhmc
from ._hmc import InputError

__all__ = ['UriHandler', 'LparActivateHandler', 'LparDeactivateHandler',
           'LparLoadHandler', 'HTTPError', 'URIS']

# CPC status values
CPC_ACTIVE_STATUSES = (
    "active",
    "operating",
    "degraded",
    "acceptable",
    "exceptions",
    "service-required",
    "service",
)
CPC_INACTIVE_STATUSES = (
    "not-operating",
    "no-power",
)
CPC_BAD_STATUSES = (
    "not-communicating",
    "status-check",
)


class HTTPError(Exception):
    """
    Exception that will be turned into an HTTP error response message.
    """

    def __init__(self, method, uri, http_status, reason, message):
        super().__init__()
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
        super().__init__()
        self.message = message


class InvalidResourceError(HTTPError):
    """
    HTTP error indicating an invalid resource.
    """

    def __init__(self, method, uri, handler_class=None, reason=1,
                 resource_uri=None):
        if handler_class is not None:
            handler_txt = f" (handler class {handler_class.__name__})"
        else:
            handler_txt = ""
        if not resource_uri:
            resource_uri = uri
        super().__init__(
            method, uri,
            http_status=404,
            reason=reason,
            message=f"Unknown resource with URI: {resource_uri}{handler_txt}")


class InvalidMethodError(HTTPError):
    """
    HTTP error indicating an invalid HTTP method.
    """

    def __init__(self, method, uri, handler_class=None):
        if handler_class is not None:
            handler_txt = f"handler class {handler_class.__name__}"
        else:
            handler_txt = "no handler class"
        super().__init__(
            method, uri,
            http_status=404,
            reason=1,
            message=f"Invalid HTTP method {method} on URI: {uri} {handler_txt}")


class BadRequestError(HTTPError):
    """
    HTTP error indicating an invalid client request (status 400).
    """

    def __init__(self, method, uri, reason, message):
        super().__init__(
            method, uri,
            http_status=400,
            reason=reason,
            message=message)


class ConflictError(HTTPError):
    """
    HTTP error indicating a conflict in the client request (status 409).
    """

    def __init__(self, method, uri, reason, message):
        super().__init__(
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
        super().__init__(
            method, uri, reason=5,
            message=f"CPC is not in DPM mode: {cpc.uri}")


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
        super().__init__(
            method, uri, reason=4,
            message=f"CPC is in DPM mode: {cpc.uri}")


class ServerError(HTTPError):
    """
    HTTP error indicating a server error (status 500).
    """

    def __init__(self, method, uri, reason, message):
        super().__init__(
            method, uri,
            http_status=500,
            reason=reason,
            message=message)


class MockedResourceError(Exception):
    """
    Indicates that there is an issue with the setup of a mocked resource.
    """

    def __init__(self, message):
        super().__init__()
        self.message = message


def parse_query_parms(method, uri):
    """
    Parse the specified URI with optional query parms and return the URI
    without query parms and a dictionary of query parms.

    The key of each dict item is the query parameter name, and the
    value of each dict item is the query parameter value. If a query parameter
    shows up more than once, the resulting dict item value is a list of all
    those values.

    If a query parameter is not of the format "name=value", an HTTPError 400,1
    is raised.

    Returns:

        tuple(uri, query_parms) with:

        - uri(str): Input URI without query parms
        - query_parms(dict): Query parms as dict (name, value). Empty if no
          query parms were specified.
    """
    uri_split = uri.split('?')
    uri = uri_split[0]
    try:
        query_str = uri_split[1]
    except IndexError:
        query_str = ''
    query_parms = {}
    for query_item in query_str.split('&'):
        # Example for these items: 'name=a%20b'
        if query_item == '':
            continue
        items = query_item.split('=')
        if len(items) != 2:
            raise BadRequestError(
                method, uri, reason=1,
                message="Invalid format for URI query parameter: "
                f"{query_item!r} (valid format is: 'name=value').")
        name = unquote(items[0])
        value = unquote(items[1])
        if name in query_parms:
            existing_value = query_parms[name]
            if not isinstance(existing_value, list):
                query_parms[name] = []
                query_parms[name].append(existing_value)
            query_parms[name].append(value)
        else:
            query_parms[name] = value
    return uri, query_parms


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
                                  f"body: {field_name}")


def check_required_subfields(method, uri, element, element_str, field_names):
    """
    Check required fields in an element within the request body.

    Raises:

      BadRequestError with reason 5: Missing required field in request body
    """

    for field_name in field_names:
        if field_name not in element:
            raise BadRequestError(
                method, uri, reason=5,
                message="Missing required field in request body within "
                f"{element_str}: {field_name}")


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
            raise ConflictError(
                method, uri, reason=1,
                message="The operation cannot be performed because the "
                f"targeted CPC {cpc.name} has a status that is not valid "
                f"for the operation: {status}")

        # The uri targets a resource hosted by the CPC
        raise ConflictError(
            method, uri, reason=6,
            message=f"The operation cannot be performed because CPC {cpc.name} "
            "hosting the targeted resource has a status that is not valid "
            f"for the operation: {status}")


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
            raise ConflictError(
                method, uri, reason=1,
                message="The operation cannot be performed because the "
                f"targeted partition {partition.name} has a status that is "
                f"not valid for the operation: {status}")

        # The uri targets a resource hosted by the partition
        raise ConflictError(
            method, uri, reason=1,  # Note: 6 not used for partitions
            message="The operation cannot be performed because partition "
            f"{partition.name} hosting the targeted resource has a status "
            f"that is not valid for the operation: {status}")


def check_writable(method, uri, body, writeable):
    """
    Check that the body specifies only writeable properties.

    Raises:

      BadRequestError with reason 6.
    """
    for prop in body:
        if prop not in writeable:
            raise BadRequestError(
                method, uri, reason=6,
                message=f"Property is not writable: {prop!r}")


def check_set_noninput(method, uri, properties, prop_name, prop_value):
    """
    Check that a non-input property is not contained in the properties,
    and set it to the specified value.

    Raises:

      BadRequestError with reason 6.
    """
    if prop_name in properties:
        raise BadRequestError(
            method, uri, reason=6,
            message=f"Property cannot be provided as input: {prop_name!r}")
    properties[prop_name] = prop_value


def check_invalid_query_parms(method, uri, query_parms, valid_query_parms):
    """
    Check that the query parameters are valid.

    Raises:

      BadRequestError with reason 1.
    """
    invalid_parms = []
    for qp in query_parms:
        if qp not in valid_query_parms:
            invalid_parms.append(qp)
    if invalid_parms:
        new_exc = BadRequestError(
            method, uri, reason=1,
            message="Unrecognized or unsupported query parameters: "
            f"{invalid_parms!r}")
        new_exc.__cause__ = None
        raise new_exc  # zhmcclient_mock.BadRequestError


def properties_copy(properties):
    """
    Return a deep copy of the properties that is independent of the input.

    Parameters:
        properties (DictView or dict): Input properties
    """
    return copy.deepcopy(dict(properties))


def prop_copy(prop):
    """
    Return a deep copy of a single property value that is independent of the
    input.

    Parameters:
        prop (object): Input property value
    """
    return copy.deepcopy(prop)


class UriHandler:
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


class GenericGetPropertiesHandler:
    """
    Handler class for generic get of resource properties.
    """

    # List of supported query parameters for the 'Get Properties' operation
    # of the resource type using this class.
    # Must be overridden in the derived resource handler class, if it supports
    # query parameters.
    valid_query_parms_get = []

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Get <resource> Properties."""
        # All URI patterns for Get Properties operations must have a last
        # match group for the query parms.
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)

        try:
            resource = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        subset_pnames = query_parms.get('properties', None)
        if subset_pnames:
            subset_pnames = subset_pnames.split(',')
            ret_props = {}
            for pname in subset_pnames:
                try:
                    ret_props[pname] = resource.properties[pname]
                except KeyError:
                    new_exc = BadRequestError(
                        method, uri, reason=14,
                        message=f"Invalid property {pname!r} in 'properties' "
                        f"query parameter for resource with URI {uri!r}")
                    new_exc.__cause__ = None
                    raise new_exc  # BadRequestError
            return ret_props
        return properties_copy(resource.properties)


class GenericUpdatePropertiesHandler:
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


class GenericDeleteHandler:
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


class VersionHandler:
    """
    Handler class for operation: Get version.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Get version."""
        api_major, api_minor = hmc.api_version.split('.')[0:2]
        return {
            'hmc-name': hmc.hmc_name,
            'hmc-version': hmc.hmc_version,
            'api-major-version': int(api_major),
            'api-minor-version': int(api_minor),
        }


class SessionsHandler:
    """
    Handler class for session operations.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Logon."""
        assert wait_for_completion is True  # synchronous operation
        check_required_fields(method, uri, body, ['userid', 'password'])
        session_id = uuid.uuid4().hex
        session_cred = session_id + '-cred'
        hmc.add_session_id(session_id)
        result = {
            'api-session': session_id,
            'notification-topic': 'fake-topic-1',
            'job-notification-topic': 'fake-topic-2',
            'api-major-version': 4,
            'api-minor-version': 40,
            'password-expires': -1,
            # 'shared-secret-key' not included
            'session-credential': session_cred,
        }
        return result


class ThisSessionHandler:
    """
    Handler class for session operations.
    """

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Logoff."""
        # TODO: Add support for removing the current session ID. This requires
        #       passing the request headers, which requires changing the
        #       FakedSession class to get control at the HTTP level.
        pass


class ConsoleHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on Console resource.
    """

    valid_query_parms_get = ['properties']


class ConsoleRestartHandler:
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


class ConsoleShutdownHandler:
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


class ConsoleMakePrimaryHandler:
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


class ConsoleReorderUserPatternsHandler:
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


class ConsoleGetAuditLogHandler:
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


class ConsoleGetSecurityLogHandler:
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


class ConsoleListUnmanagedCpcsHandler:
    """
    Handler class for Console operation: List Unmanaged CPCs.
    """

    valid_query_parms_get = ['name']

    returned_props = ['name', 'object-uri']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Unmanaged CPCs."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        result_ucpcs = []
        filter_args = query_parms
        for ucpc in console.unmanaged_cpcs.list(filter_args):
            result_ucpc = {}
            for prop in cls.returned_props:
                result_ucpc[prop] = prop_copy(ucpc.properties[prop])
            result_ucpcs.append(result_ucpc)
        return {'cpcs': result_ucpcs}


class ConsoleListPermittedPartitionsHandler:
    """
    Handler class for Console operation: List Permitted Partitions (DPM).
    """

    valid_query_parms_get = ['name', 'type', 'status',
                             'has-unacceptable-status', 'cpc-name',
                             'additional-properties']

    returned_props = [
        'name', 'object-uri', 'type', 'status', 'has-unacceptable-status',
        # plus additional-properties
        # plus properties not from Partition
    ]

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Permitted Partitions."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        if 'additional-properties' in query_parms:
            add_props = query_parms.pop('additional-properties').split(',')
        else:
            add_props = []
        filter_args = query_parms

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
                    for prop in cls.returned_props + add_props:
                        result_partition[prop] = \
                            partition.properties.get(prop)
                    result_partition['cpc-name'] = cpc.name
                    result_partition['cpc-object-uri'] = cpc.uri
                    result_partition['se-version'] = \
                        cpc.properties.get('se-version', None)
                    result_partitions.append(result_partition)

        return {'partitions': result_partitions}


class ConsoleListPermittedLparsHandler:
    """
    Handler class for Console operation: List Permitted LPARs (classic).
    """

    valid_query_parms_get = ['name', 'activation-mode', 'status',
                             'has-unacceptable-status', 'cpc-name',
                             'additional-properties']

    returned_props = [
        'name', 'object-uri', 'activation-mode', 'status',
        'has-unacceptable-status',
        # plus additional-properties
        # plus properties not from LPAR
    ]

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Permitted LPARs."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        if 'additional-properties' in query_parms:
            add_props = query_parms.pop('additional-properties').split(',')
        else:
            add_props = []
        filter_args = query_parms

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
                    for prop in cls.returned_props + add_props:
                        result_lpar[prop] = prop_copy(lpar.properties.get(prop))
                    result_lpar['cpc-name'] = cpc.name
                    result_lpar['cpc-object-uri'] = cpc.uri
                    result_lpar['se-version'] = \
                        cpc.properties.get('se-version', None)
                    result_lpars.append(result_lpar)

        return {'logical-partitions': result_lpars}


class ConsoleListPermittedAdaptersHandler:
    """
    Handler class for Console operation: List Permitted Adapters (classic+DPM).
    """

    valid_query_parms_get = ['name', 'adapter-id', 'adapter-family', 'type',
                             'status', 'firmware-update-pending', 'cpc-name',
                             'dpm-enabled', 'additional-properties']

    returned_props = [
        'object-uri', 'name', 'adapter-id', 'adapter-family', 'type',
        'status', 'firmware-update-pending',
        # plus additional-properties
        # plus properties not from Adapter
    ]

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """
        Operation: List Permitted Adapters (classic+DPM).

        Note that the support in the HMC for classic mode CPCs is only for z16
        and newer CPCs. For z15 and earlier CPCs in classic mode, the operation
        will not have any adapters in the result.
        """
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        if 'additional-properties' in query_parms:
            add_props = query_parms.pop('additional-properties').split(',')
        else:
            add_props = []
        filter_args = query_parms

        result_adapters = []
        for cpc in hmc.cpcs.list():
            se_version_info = list(map(
                int, cpc.properties.get('se-version').split('.')))

            if cpc.dpm_enabled or se_version_info >= [2, 16]:

                # Apply the CPC name filter, if specified
                if filter_args and 'cpc-name' in filter_args:
                    if not re.match(filter_args['cpc-name'], cpc.name):
                        continue
                    del filter_args['cpc-name']

                for adapter in cpc.adapters.list(filter_args):
                    result_adapter = {}
                    for prop in cls.returned_props + add_props:
                        result_adapter[prop] = \
                            adapter.properties.get(prop)
                    result_adapter['cpc-name'] = cpc.name
                    result_adapter['cpc-object-uri'] = cpc.uri
                    result_adapter['se-version'] = \
                        cpc.properties.get('se-version', None)
                    result_adapter['dpm-enabled'] = \
                        cpc.properties.get('dpm-enabled', None)
                    result_adapters.append(result_adapter)

        return {'adapters': result_adapters}


class UsersHandler:
    """
    Handler class for HTTP methods on set of User resources.
    """

    valid_query_parms_get = ['name', 'type']

    returned_props = ['object-uri', 'name', 'type']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Users."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_users = []
        for user in console.users.list(filter_args):
            result_user = {}
            for prop in cls.returned_props:
                result_user[prop] = prop_copy(user.properties.get(prop))
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
        properties = copy.deepcopy(body)
        user_name = properties['name']

        properties.setdefault('allow-management-interfaces', True)
        properties.setdefault('allow-remote-access', True)
        properties.setdefault('default-group-uri', None)
        properties.setdefault('description', '')
        properties.setdefault('disable-delay', 1)
        properties.setdefault('disabled', False)
        properties.setdefault('disruptive-pw-required', True)
        properties.setdefault('disruptive-text-required', False)
        properties.setdefault('email-address', None)
        properties.setdefault('force-password-change', False)
        properties.setdefault('force-shared-secret-key-change', None)
        properties.setdefault('idle-timeout', 0)
        properties.setdefault('inactivity-timeout', 0)
        properties.setdefault('is-locked', False)
        properties.setdefault('max-failed-logins', 3)
        properties.setdefault('max-web-services-api-sessions', 1000)
        properties.setdefault('min-pw-change-time', 0)
        properties.setdefault('multi-factor-authentication-required', False)
        properties.setdefault('password-expires', -1)
        properties.setdefault('replication-overwrite-possible', False)
        properties.setdefault('session-timeout', 0)
        properties.setdefault('user-roles', [])
        properties.setdefault('userid-on-ldap-server', None)
        properties.setdefault('verify-timeout', 15)
        properties.setdefault('web-services-api-session-idle-timeout', 360)

        auth_type = properties['authentication-type']
        if auth_type == 'local':
            check_required_fields(method, uri, body,
                                  ['password', 'password-rule-uri'])
        elif auth_type == 'ldap':
            check_required_fields(method, uri, body,
                                  ['ldap-server-definition-uri'])
        else:
            raise BadRequestError(
                method, uri, reason=4,
                message=f"Invalid authentication-type: {auth_type!r}")

        user_type = properties['type']
        if user_type == 'standard':
            pass
        elif user_type == 'template':
            pass
        elif user_type == 'pattern-based':
            pass
        elif user_type == 'system-defined':
            raise BadRequestError(
                method, uri, reason=4,
                message="System-defined users cannot be created: "
                f"{user_name!r}")
        else:
            raise BadRequestError(
                method, uri, reason=4,
                message=f"Invalid user type: {user_type!r}")

        new_user = console.users.add(properties)
        return {'object-uri': new_user.uri}


class UserHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single User resource.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Update StoragePort Properties."""
        try:
            user = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        # Check whether requested properties are modifiable
        check_writable(
            method, uri, body,
            [
                'description',
                'disabled',
                'authentication-type',
                'password-rule-uri',
                'password',
                'force-password-change',
                'ldap-server-definition-uri',
                'userid-on-ldap-server',
                'session-timeout',
                'verify-timeout',
                'timeout',
                'idle-timeout',
                'min-pw-change-time',
                'max-failed-logins',
                'disable-delay',
                'inactivity-timeout',
                'disruptive-pw-required',
                'disruptive-text-required',
                'allow-remote-access',
                'allow-management-interfaces',
                'max-web-services-api-sessions',
                'web-services-api-session-idle-timeout',
                'default-group-uri',
                'multi-factor-authentication-required',
                'force-shared-secret-key-change',
                'email-address',
                'mfa-types',
                'primary-mfa-server-definition-uri',
                'backup-mfa-server-definition-uri',
                'mfa-policy',
                'mfa-userid',
                'mfa-userid-override',
            ])
        user.update(body)

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
                message=f"Cannot delete pattern-based user {user.name!r}")
        # Delete the mocked resource
        user.manager.remove(user.oid)


class UserAddUserRoleHandler:
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
                message=f"Cannot add user role to user of type {user_type}: "
                f"{user_uri}")
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


class UserRemoveUserRoleHandler:
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
                message="Cannot remove user role from user of type "
                f"{user_type}: {user_uri}")
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
                message=f"User {user.name!r} does not have User Role "
                f"{user_role.name!r}")
        user.properties['user-roles'].remove(user_role_uri)


class UserRolesHandler:
    """
    Handler class for HTTP methods on set of UserRole resources.
    """

    valid_query_parms_get = ['name', 'type']

    returned_props = ['object-uri', 'name', 'type']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List User Roles."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_user_roles = []
        for user_role in console.user_roles.list(filter_args):
            result_user_role = {}
            for prop in cls.returned_props:
                result_user_role[prop] = \
                    prop_copy(user_role.properties.get(prop))
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
        if 'type' in body:
            raise BadRequestError(
                method, uri, reason=6,
                message="The 'type' property cannot be specified when "
                f"creating a user role (type: {body['type']!r}, uri: {uri!r})")
        properties = copy.deepcopy(body)
        # createable/updateable
        properties.setdefault('description', '')
        if 'associated-system-defined-user-role-uri' not in properties:
            # Use the default
            uroles = console.user_roles.list(
                filter_args=dict(name='hmc-operator-tasks'))
            if not uroles:
                new_exc = ServerError(
                    method, uri, reason=99,
                    message="Mock setup error: System-defined user role "
                    "'hmc-operator-tasks' does not exist")
                new_exc.__cause__ = None
                raise new_exc  # zhmcclient_mock.ServerError
            urole_uri = uroles[0].uri
            properties['associated-system-defined-user-role-uri'] = urole_uri
        properties.setdefault('is-inheritance-enabled', False)
        # read-only
        properties.setdefault('type', 'user-defined')
        properties.setdefault('replication-overwrite-possible', True)
        properties.setdefault('permissions', [])
        new_user_role = console.user_roles.add(properties)
        return {'object-uri': new_user_role.uri}


class UserRoleHandler(GenericGetPropertiesHandler,
                      GenericDeleteHandler):
    """
    Handler class for HTTP methods on single UserRole resource.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Update StoragePort Properties."""
        try:
            user_role = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        # Check whether requested properties are modifiable
        check_writable(
            method, uri, body,
            [
                'description',
                'associated-system-defined-user-role-uri',
                'is-inheritance-enabled',
            ])
        user_role.update(body)

    # TODO: Add delete() for Delete UserRole that rejects system-defined type


class UserRoleAddPermissionHandler:
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
                f"system-defined user role: {user_role_uri}")
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


class UserRoleRemovePermissionHandler:
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
                f"from system-defined user role: {user_role_uri}")
        # Apply defaults, so we can locate it based upon all fields:
        permission = copy.deepcopy(body)
        if 'include-members' not in permission:
            permission['include-members'] = False
        if 'view-only-mode' not in permission:
            permission['view-only-mode'] = True
        # Remove the permission from its store (the faked User Role object):
        if user_role.properties.get('permissions', None) is not None:
            user_role.properties['permissions'].remove(permission)


class TasksHandler:
    """
    Handler class for HTTP methods on set of Task resources.
    """

    valid_query_parms_get = ['name']

    returned_props = ['element-uri', 'name']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Tasks."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_tasks = []
        for task in console.tasks.list(filter_args):
            result_task = {}
            for prop in cls.returned_props:
                result_task[prop] = prop_copy(task.properties.get(prop))
            result_tasks.append(result_task)
        return {'tasks': result_tasks}


class TaskHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single Task resource.
    """
    pass


class UserPatternsHandler:
    """
    Handler class for HTTP methods on set of UserPattern resources.
    """

    valid_query_parms_get = ['name', 'type']

    returned_props = ['element-uri', 'name', 'type']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List User Patterns."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_user_patterns = []
        for user_pattern in console.user_patterns.list(filter_args):
            result_user_pattern = {}
            for prop in cls.returned_props:
                result_user_pattern[prop] = \
                    user_pattern.properties.get(prop)
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
                              ['name', 'pattern', 'type', 'retention-time'])

        # Note: user-template-uri was required until HMC 2.13. Since 2.14,
        # one of three user template identification methods is required

        # Check that exacly one user template identification method is
        # specified.
        m1_used = body.get('specific-template-uri') is not None
        m2_used = body.get('template-name-override') is not None
        m3_used = body.get('ldap-group-to-template-mappings') is not None
        methods_used = m1_used + m2_used + m3_used
        if methods_used == 0:
            raise BadRequestError(
                method, uri, reason=15,
                message="Unable to determine template identification method "
                "from request body")
        if methods_used > 1:
            raise BadRequestError(
                method, uri, reason=15,
                message="More than one template identification method "
                "specified in request body")

        properties = copy.deepcopy(body)
        properties.setdefault('description', '')
        properties.setdefault('search-order-index', 0)
        properties.setdefault('replication-overwrite-possible', False)
        properties.setdefault('user-template-uri', None)
        properties.setdefault('ldap-server-definition-uri', None)
        properties.setdefault('template-name-override', None)
        properties.setdefault('domain-name-restrictions', None)
        properties.setdefault('specific-template-uri', None)
        properties.setdefault(
            'template-name-override-ldap-server-definition-uri', None)
        properties.setdefault(
            'template-name-override-default-template-uri', None)
        properties.setdefault('ldap-group-to-template-mappings', None)
        properties.setdefault('ldap-group-ldap-server-definition-uri', None)
        properties.setdefault('ldap-group-default-template-uri', None)
        properties.setdefault(
            'domain-name-restrictions-ldap-server-definition-uri', None)

        new_user_pattern = console.user_patterns.add(properties)
        return {'element-uri': new_user_pattern.uri}


class UserPatternHandler(GenericGetPropertiesHandler,
                         GenericUpdatePropertiesHandler,
                         GenericDeleteHandler):
    """
    Handler class for HTTP methods on single UserPattern resource.
    """
    pass


class PasswordRulesHandler:
    """
    Handler class for HTTP methods on set of PasswordRule resources.
    """

    valid_query_parms_get = ['name', 'type']

    returned_props = ['element-uri', 'name', 'type']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Password Rules."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_password_rules = []
        for password_rule in console.password_rules.list(filter_args):
            result_password_rule = {}
            for prop in cls.returned_props:
                result_password_rule[prop] = \
                    password_rule.properties.get(prop)
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

        properties = copy.deepcopy(body)
        # createable/updateable
        properties.setdefault('description', '')
        properties.setdefault('expiration', 0)
        properties.setdefault('min-length', 8)
        properties.setdefault('max-length', 256)
        properties.setdefault('consecutive-characters', 0)
        properties.setdefault('similarity-count', 0)
        properties.setdefault('history-count', 0)
        properties.setdefault('case-sensitive', False)
        properties.setdefault('character-rules', [])
        # read-only
        properties.setdefault('type', 'user-defined')
        properties.setdefault('replication-overwrite-possible', True)

        new_password_rule = console.password_rules.add(properties)
        return {'element-uri': new_password_rule.uri}


class PasswordRuleHandler(GenericGetPropertiesHandler,
                          GenericDeleteHandler):
    """
    Handler class for HTTP methods on single PasswordRule resource.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Update PasswordRule Properties."""
        try:
            pw_rule = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        # Check whether requested properties are modifiable
        check_writable(
            method, uri, body,
            [
                'description',
                'expiration',
                'min-length',
                'max-length',
                'consecutive-characters',
                'similarity-count',
                'history-count',
                'case-sensitive',
                'character-rules',
            ])
        pw_rule.update(body)


class LdapServerDefinitionsHandler:
    """
    Handler class for HTTP methods on set of LdapServerDefinition resources.
    """

    valid_query_parms_get = ['name']

    returned_props = ['element-uri', 'name']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List LDAP Server Definitions."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_ldap_srv_defs = []
        for ldap_srv_def in console.ldap_server_definitions.list(filter_args):
            result_ldap_srv_def = {}
            for prop in cls.returned_props:
                result_ldap_srv_def[prop] = \
                    ldap_srv_def.properties.get(prop)
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
        check_required_fields(method, uri, body,
                              ['name', 'primary-hostname-ipaddr',
                               'search-distinguished-name'])
        new_ldap_srv_def = console.ldap_server_definitions.add(body)
        return {'element-uri': new_ldap_srv_def.uri}


class LdapServerDefinitionHandler(GenericGetPropertiesHandler,
                                  GenericDeleteHandler):
    """
    Handler class for HTTP methods on single LdapServerDefinition resource.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Update LdapServerDefinition Properties."""
        try:
            lsd = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        # Check whether requested properties are modifiable
        check_writable(
            method, uri, body,
            [
                'description',
                'primary-hostname-ipaddr',
                'connection-port',
                'backup-hostname-ipaddr',
                'use-ssl',
                'tolerate-untrusted-certificates',
                'bind-distinguished-name',
                'bind-password',
                'location-method',
                'search-distinguished-name',
                'search-scope',
                'search-filter',
                'replication-overwrite-possible',
            ])
        lsd.update(body)


class MfaServerDefinitionsHandler:
    """
    Handler class for HTTP methods on set of MfaServerDefinition resources.
    """

    valid_query_parms_get = ['name']

    returned_props = ['element-uri', 'name']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List MFA Server Definitions."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_mfa_srv_defs = []
        for mfa_srv_def in console.mfa_server_definitions.list(filter_args):
            result_mfa_srv_def = {}
            for prop in cls.returned_props:
                result_mfa_srv_def[prop] = \
                    mfa_srv_def.properties.get(prop)
            result_mfa_srv_defs.append(result_mfa_srv_def)
        return {'mfa-server-definitions': result_mfa_srv_defs}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create MFA Server Definition."""
        assert wait_for_completion is True  # synchronous operation
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body,
                              ['name', 'hostname-ipaddr'])
        new_mfa_srv_def = console.mfa_server_definitions.add(body)
        return {'element-uri': new_mfa_srv_def.uri}


class MfaServerDefinitionHandler(GenericGetPropertiesHandler,
                                 GenericDeleteHandler):
    """
    Handler class for HTTP methods on single MfaServerDefinition resource.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Update MfaServerDefinition Properties."""
        try:
            mfa = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        # Check whether requested properties are modifiable
        check_writable(
            method, uri, body,
            [
                'name',
                'description',
                'hostname-ipaddr',
                'port',
            ])
        mfa.update(body)


class CpcsHandler:
    """
    Handler class for HTTP methods on set of Cpc resources.
    """

    valid_query_parms_get = ['name']

    returned_props = [
        'object-uri', 'name', 'status',
        # Added in HMC version 2.14.0:
        'has-unacceptable-status', 'dpm-enabled', 'se-version',
    ]

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List CPCs."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        result_cpcs = []
        for cpc in hmc.cpcs.list(filter_args):
            result_cpc = {}
            for prop in cls.returned_props:
                result_cpc[prop] = prop_copy(cpc.properties.get(prop))
            result_cpcs.append(result_cpc)
        return {'cpcs': result_cpcs}


class CpcHandler(GenericGetPropertiesHandler,
                 GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single Cpc resource.
    """

    valid_query_parms_get = ['properties', 'cached-acceptable', 'group-uri']


class CpcSetPowerSaveHandler:
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
                                  message="Invalid power-saving value: "
                                  f"{power_saving!r}")

        cpc.properties['cpc-power-saving'] = power_saving
        cpc.properties['cpc-power-saving-state'] = power_saving
        cpc.properties['zcpc-power-saving'] = power_saving
        cpc.properties['zcpc-power-saving-state'] = power_saving


class CpcSetPowerCappingHandler:
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
                                  f"{power_capping_state!r}")

        if power_capping_state == 'enabled' and power_cap_current is None:
            raise BadRequestError(method, uri, reason=7,
                                  message="Power-cap-current must be provided "
                                  "when enabling power capping")

        cpc.properties['cpc-power-capping-state'] = power_capping_state
        cpc.properties['cpc-power-cap-current'] = power_cap_current
        cpc.properties['zcpc-power-capping-state'] = power_capping_state
        cpc.properties['zcpc-power-cap-current'] = power_cap_current


class CpcGetEnergyManagementDataHandler:
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


class CpcStartHandler:
    """
    Handler class for operation: Start CPC (DPM mode).
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


class CpcStopHandler:
    """
    Handler class for operation: Stop CPC (DPM mode).
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


class CpcActivateHandler:
    """
    Handler class for operation: Activate CPC (classic mode)
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Activate CPC (requires classic mode)."""
        assert wait_for_completion is True  # async not supported yet
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['activation-profile-name'])
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)
        profile_name = body['activation-profile-name']
        force = body.get('force', False)
        status = cpc.properties['status']
        if status in CPC_BAD_STATUSES:
            raise ConflictError(
                method, uri, reason=1,
                message="The operation cannot be performed because the "
                f"targeted CPC {cpc.name} has a bad status {status!r}")
        if status in CPC_ACTIVE_STATUSES and not force:
            raise ConflictError(
                method, uri, reason=1,
                message="The operation cannot be performed because the "
                f"targeted CPC {cpc.name} already has an active status "
                f"{status!r} and force is not specified")
        cpc.properties['status'] = 'operating'
        cpc.properties['last-used-activation-profile'] = profile_name
        # TODO: Set last-used-iocds from profile


class CpcDeactivateHandler:
    """
    Handler class for operation: Deactivate CPC (classic mode).
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Deactivate CPC (requires classic mode)."""
        assert wait_for_completion is True  # async not supported yet
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)
        force = body.get('force', False)
        status = cpc.properties['status']
        if status in CPC_BAD_STATUSES:
            raise ConflictError(
                method, uri, reason=1,
                message="The operation cannot be performed because the "
                f"targeted CPC {cpc.name} has a bad status {status!r}")
        if status in CPC_ACTIVE_STATUSES and not force:
            raise ConflictError(
                method, uri, reason=1,
                message="The operation cannot be performed because the "
                f"targeted CPC {cpc.name} has an active status {status!r} "
                "and force is not specified")
        cpc.properties['status'] = 'no-power'


class CpcImportProfilesHandler:
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


class CpcExportProfilesHandler:
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


class CpcExportPortNamesListHandler:
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
                    message=f"Partition {partition.uri!r} specified in "
                    "'partitions' field is not in the targeted CPC with ID "
                    f"{cpc_oid!r} (but in the CPC with ID "
                    f"{partition_cpc.oid!r}).")
            partition_name = partition.properties.get('name', '')
            for hba in partition.hbas.list():
                port_uri = hba.properties['adapter-port-uri']
                port = hmc.lookup_by_uri(port_uri)
                adapter = port.manager.parent
                adapter_id = adapter.properties.get('adapter-id', '')
                devno = hba.properties.get('device-number', '')
                wwpn = hba.properties.get('wwpn', '')
                wwpn_str = f'{partition_name},{adapter_id},{devno},{wwpn}'
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


class CpcAddTempCapacityHandler:
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
                    message="Cannot activate temporary software model "
                    f"{software_model} because temporary software model "
                    f"{current_software_model} is already active")
            # We accept any software model, and imply the desired total number
            # of general purpose processors from the last two digits.
            pnum = int(software_model[1:])
            pname = 'processor-count-general-purpose'
            ptype = 'cp'
            if pnum < cpc.properties[pname]:
                raise BadRequestError(
                    method, uri, reason=276,
                    message="Cannot activate temporary software model "
                    f"{software_model} because its target number of {pnum} "
                    f"{ptype} processors is below the current number of "
                    f"{cpc.properties[pname]} {ptype} processors")
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
                        message=f"Invalid processor type {ptype} was "
                        "specified in a processor-info entry")
                pname = CPC_PROPNAME_FROM_PROCTYPE[ptype]
                if psteps is not None:
                    # TODO: Check against installed number of processors
                    cpc.properties[pname] += psteps


class CpcRemoveTempCapacityHandler:
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
                    message="Cannot deactivate temporary software model "
                    f"{software_model} because no temporary software model "
                    "is currently active")
            # We accept any software model, and imply the desired total number
            # of general purpose processors from the last two digits.
            pnum = int(software_model[1:])
            pname = 'processor-count-general-purpose'
            ptype = 'cp'
            if pnum > cpc.properties[pname]:
                raise BadRequestError(
                    method, uri, reason=276,
                    message="Cannot activate temporary software model "
                    f"{software_model} because its target number of {pnum} "
                    f"{ptype} processors is above the current number of "
                    f"{cpc.properties[pname]} {ptype} processors")
            cpc.properties[pname] = pnum
            cpc.properties['software-model-permanent-plus-temporary'] = None
        if processor_info is not None:
            for pitem in processor_info:
                ptype = pitem['processor-type']
                psteps = pitem.get('num-processor-steps', None)
                if ptype not in CPC_PROPNAME_FROM_PROCTYPE:
                    raise BadRequestError(
                        method, uri, reason=276,
                        message=f"Invalid processor type {ptype} was "
                        "specified in a processor-info entry")
                pname = CPC_PROPNAME_FROM_PROCTYPE[ptype]
                if psteps is not None:
                    if cpc.properties[pname] - psteps < 1:
                        raise BadRequestError(
                            method, uri, reason=276,
                            message="Cannot reduce the number of "
                            f"{cpc.properties[pname]} {ptype} processors by "
                            f"{psteps} because at least one processor must "
                            "remain.")
                    cpc.properties[pname] -= psteps


class CpcSetAutoStartListHandler:
    """
    Handler class for operation: Set Auto-start List.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Set Auto-start List."""
        assert wait_for_completion is True  # no async
        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['auto-start-list'])
        auto_start_list = body['auto-start-list']
        # Store it in the CPC
        cpc.properties['auto-start-list'] = auto_start_list


class GroupsHandler:
    """
    Handler class for HTTP methods on set of Group resources.
    """

    valid_query_parms_get = ['name']

    returned_props = ['object-uri', 'name']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Custom Groups."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_groups = []
        for group in console.groups.list(filter_args):
            result_group = {}
            for prop in cls.returned_props:
                result_group[prop] = prop_copy(group.properties.get(prop))
            result_groups.append(result_group)
        return {'groups': result_groups}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create Custom Group."""

        assert wait_for_completion is True  # async not supported yet
        try:
            console = hmc.consoles.lookup_by_oid(None)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['name'])

        properties = copy.deepcopy(body)

        # Set defaults for optional input properties
        properties.setdefault('description', '')
        properties.setdefault('match-info', None)

        # Set non-input properties
        properties['members'] = []

        # Reflect the result of creating the partition
        new_group = console.groups.add(properties)
        return {'object-uri': new_group.uri}


class GroupHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single Group resource.
    """

    @staticmethod
    def delete(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Delete Custom Group."""
        try:
            group = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        # Reflect the result of deleting the group
        group.manager.remove(group.oid)


class GroupAddMemberHandler:
    """
    Handler class for operation: Add Member to Custom Group.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Add Member to Custom Group."""
        assert wait_for_completion is True  # async not supported yet
        console_uri = '/api/console'
        try:
            console = hmc.lookup_by_uri(console_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        group_oid = uri_parms[0]
        try:
            group = console.groups.lookup_by_oid(group_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['object-uri'])

        object_uri = body['object-uri']

        group.properties['members'].append(object_uri)


class GroupRemoveMemberHandler:
    """
    Handler class for operation: Remove Member from Custom Group.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Remove Member from Custom Group."""
        assert wait_for_completion is True  # async not supported yet
        console_uri = '/api/console'
        try:
            console = hmc.lookup_by_uri(console_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        group_oid = uri_parms[0]
        try:
            group = console.groups.lookup_by_oid(group_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        check_required_fields(method, uri, body, ['object-uri'])

        object_uri = body['object-uri']

        group.properties['members'].remove(object_uri)


class GroupMembersHandler:
    """
    Handler class for operation: List Custom Group Members.
    """

    @staticmethod
    def get(method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Custom Group Members."""
        group_oid = uri_parms[0]
        console_uri = '/api/console'
        try:
            console = hmc.lookup_by_uri(console_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        try:
            group = console.groups.lookup_by_oid(group_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        member_uris = group.properties['members']
        members = []
        for member_uri in member_uris:
            try:
                member = hmc.lookup_by_uri(member_uri)
            except KeyError:
                new_exc = InvalidResourceError(method, member_uri)
                new_exc.__cause__ = None
                raise new_exc  # zhmcclient_mock.InvalidResourceError
            member_item = {'object-uri': member_uri, 'name': member.name}
            members.append(member_item)
        result = {'members': members}
        return result


# Functions for the "Get Inventory" operation, for each resource class:

def get_inventory_for_adapter(hmc):
    """Get inventory data for resource class 'adapter'"""
    result = []
    cpcs = hmc.cpcs.list()
    for cpc in cpcs:
        adapters = cpc.adapters.list()
        for adapter in adapters:
            result.append(properties_copy(adapter.properties))
            ports = adapter.ports.list()
            for port in ports:
                result.append(properties_copy(port.properties))
    return result


def get_inventory_for_partition(hmc):
    """Get inventory data for resource class 'partition'"""
    result = []
    cpcs = hmc.cpcs.list()
    for cpc in cpcs:
        partitions = cpc.partitions.list()
        for partition in partitions:
            result.append(properties_copy(partition.properties))
            nics = partition.nics.list()
            for nic in nics:
                result.append(properties_copy(nic.properties))
            hbas = partition.hbas.list()
            for hba in hbas:
                result.append(properties_copy(hba.properties))
            vfs = partition.virtual_functions.list()
            for vf in vfs:
                result.append(properties_copy(vf.properties))
    return result


def get_inventory_for_partition_link(hmc):
    # pylint: disable=unused-argument
    """Get inventory data for resource class 'partition-link'"""
    result = []
    # TODO: Implement mock support for this resource class; then enable:
    # partlinks = hmc.consoles.console.partition_links.list()
    # for partlink in partlinks:
    #     result.append(properties_copy(partlink.properties))
    return result


def get_inventory_for_virtual_switch(hmc):
    """Get inventory data for resource class 'virtual-switch'"""
    result = []
    cpcs = hmc.cpcs.list()
    for cpc in cpcs:
        vswitches = cpc.virtual_switches.list()
        for vswitch in vswitches:
            result.append(properties_copy(vswitch.properties))
    return result


def get_inventory_for_storage_site(hmc):
    # pylint: disable=unused-argument
    """Get inventory data for resource class 'storage-site'"""
    result = []
    # TODO: Implement mock support for this resource class; then enable:
    # stosites = hmc.consoles.console.storage_sites.list()
    # for stosite in stosites:
    #     result.append(properties_copy(stosite.properties))
    return result


def get_inventory_for_storage_fabric(hmc):
    # pylint: disable=unused-argument
    """Get inventory data for resource class 'storage-fabric'"""
    result = []
    # TODO: Implement mock support for this resource class; then enable:
    # stofabrics = hmc.consoles.console.storage_fabrics.list()
    # for stofabric in stofabrics:
    #     result.append(properties_copy(stofabric.properties))
    return result


def get_inventory_for_storage_switch(hmc):
    # pylint: disable=unused-argument
    """Get inventory data for resource class 'storage-switch'"""
    result = []
    # TODO: Implement mock support for this resource class; then enable:
    # stosites = hmc.consoles.console.storage_sites.list()
    # for stosite in stosites:
    #     stoswitches = stosite.storage_switches.list()
    #     for stoswitch in stoswitches:
    #         result.append(properties_copy(stoswitch.properties))
    return result


def get_inventory_for_storage_subsystem(hmc):
    # pylint: disable=unused-argument
    """Get inventory data for resource class 'storage-subsystem'"""
    result = []
    # TODO: Implement mock support for this resource class; then enable:
    # stosites = hmc.consoles.console.storage_sites.list()
    # for stosite in stosites:
    #     stosubsystems = stosite.storage_subsystems.list()
    #     for stosubsystem in stosubsystems:
    #         result.append(properties_copy(stosubsystem.properties))
    return result


def get_inventory_for_storage_control_unit(hmc):
    # pylint: disable=unused-argument
    """Get inventory data for resource class 'storage-control-unit'"""
    result = []
    # TODO: Implement mock support for this resource class; then enable:
    # stosites = hmc.consoles.console.storage_sites.list()
    # for stosite in stosites:
    #     stosubsystems = stosite.storage_subsystems.list()
    #     for stosubsystem in stosubsystems:
    #         stocus = stosubsystem.storage_control_units.list()
    #         for stocu in stocus:
    #             result.append(properties_copy(stocu.properties))
    return result


def get_inventory_for_storage_group(hmc):
    """Get inventory data for resource class 'storage-group'"""
    result = []
    stogroups = hmc.consoles.console.storage_groups.list()
    for stogroup in stogroups:
        result.append(properties_copy(stogroup.properties))
    return result


def get_inventory_for_storage_template(hmc):
    # pylint: disable=unused-argument
    """Get inventory data for resource class 'storage-template'"""
    result = []
    # TODO: Implement mock support for this resource class; then enable:
    # stotemplates = hmc.consoles.console.storage_templates.list()
    # for stotemplate in stotemplates:
    #     result.append(properties_copy(stotemplate.properties))
    return result


def get_inventory_for_tape_link(hmc):
    # pylint: disable=unused-argument
    """Get inventory data for resource class 'tape-link'"""
    result = []
    # TODO: Implement mock support for this resource class; then enable:
    # tapelinks = hmc.consoles.console.tape_links.list()
    # for tapelink in tapelinks:
    #     result.append(properties_copy(tapelink.properties))
    return result


def get_inventory_for_tape_library(hmc):
    # pylint: disable=unused-argument
    """Get inventory data for resource class 'tape-library'"""
    result = []
    # TODO: Implement mock support for this resource class; then enable:
    # tapelibs = hmc.consoles.console.tape_libraries.list()
    # result = []
    # for tapelib in tapelibs:
    #     result.append(properties_copy(tapelib.properties))
    return result


def get_inventory_for_cpc(hmc):
    """Get inventory data for resource class 'cpc'"""
    result = []
    cpcs = hmc.cpcs.list()
    for cpc in cpcs:
        result.append(properties_copy(cpc.properties))
    return result


def get_inventory_for_logical_partition(hmc):
    """Get inventory data for resource class 'logical-partition'"""
    result = []
    cpcs = hmc.cpcs.list()
    for cpc in cpcs:
        lpars = cpc.lpars.list()
        for lpar in lpars:
            result.append(properties_copy(lpar.properties))
    return result


def get_inventory_for_console(hmc):
    """Get inventory data for resource class 'console'"""
    console = hmc.console
    result = []
    result.append(properties_copy(console.properties))
    return result


def get_inventory_for_custom_group(hmc):
    """Get inventory data for resource class 'custom-group'"""
    groups = hmc.consoles.console.groups.list()
    result = []
    for group in groups:
        result.append(properties_copy(group.properties))
    return result


def get_inventory_for_user(hmc):
    """Get inventory data for resource class 'user'"""
    users = hmc.consoles.console.users.list()
    result = []
    for user in users:
        result.append(properties_copy(user.properties))
    return result


def get_inventory_for_user_role(hmc):
    """Get inventory data for resource class 'user-role'"""
    userroles = hmc.consoles.console.user_roles.list()
    result = []
    for userrole in userroles:
        result.append(properties_copy(userrole.properties))
    return result


def get_inventory_for_certificate(hmc):
    """Get inventory data for resource class 'certificate'"""
    certificates = hmc.consoles.console.certificates.list()
    result = []
    for certificate in certificates:
        result.append(properties_copy(certificate.properties))
    return result


class InventoryHandler:
    """
    Handler class for operation: Get Inventory.
    """

    # Resources classes for each category
    classes_from_category = {
        "dpm-resources": [
            "adapter",
            "partition",
            "partition-link",
            "virtual-switch",
            "storage-site",
            "storage-fabric",
            "storage-switch",
            "storage-subsystem",
            "storage-control-unit",
            "storage-group",
            "storage-template",
            "tape-link",
            "tape-library",
        ],
        "core-resources": [
            "cpc",
            "logical-partition",
        ],
        "console-resources": [
            "console",
            "custom-group",
            "user",
            "user-role",
        ],
        "certificate-resources": [
            "secure-boot-certificate",  # Resource class is 'certificate'
        ],
    }

    # Get inventory functions for each resource class
    get_inventory_for_rc = {
        "adapter": get_inventory_for_adapter,
        "partition": get_inventory_for_partition,
        "partition-link": get_inventory_for_partition_link,
        "virtual-switch": get_inventory_for_virtual_switch,
        "storage-site": get_inventory_for_storage_site,
        "storage-fabric": get_inventory_for_storage_fabric,
        "storage-switch": get_inventory_for_storage_switch,
        "storage-subsystem": get_inventory_for_storage_subsystem,
        "storage-control-unit": get_inventory_for_storage_control_unit,
        "storage-group": get_inventory_for_storage_group,
        "storage-template": get_inventory_for_storage_template,
        "tape-link": get_inventory_for_tape_link,
        "tape-library": get_inventory_for_tape_library,
        "cpc": get_inventory_for_cpc,
        "logical-partition": get_inventory_for_logical_partition,
        "console": get_inventory_for_console,
        "custom-group": get_inventory_for_custom_group,
        "user": get_inventory_for_user,
        "user-role": get_inventory_for_user_role,
        "secure-boot-certificate": get_inventory_for_certificate,
    }

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Get Inventory."""

        all_categories = list(InventoryHandler.classes_from_category.keys())
        resources = body.get('resources', all_categories)
        resource_classes = []
        for res in resources:
            try:
                rcs = InventoryHandler.classes_from_category[res]
            except KeyError:
                rcs = [res]
            resource_classes.extend(rcs)

        result = []
        for rc in resource_classes:
            get_func = InventoryHandler.get_inventory_for_rc[rc]
            result.extend(get_func(hmc))
        return result


class MetricsContextsHandler:
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


class MetricsContextHandler:
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


class AdaptersHandler:
    """
    Handler class for HTTP methods on set of Adapter resources.
    """

    valid_query_parms_get = ['name', 'adapter-id', 'adapter-family', 'type',
                             'status', 'additional-properties']

    returned_props = [
        'object-uri', 'name', 'adapter-id', 'adapter-family', 'type', 'status',
        # plus additional-properties
    ]

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Adapters of a CPC (empty result if not in DPM
        mode)."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        if 'additional-properties' in query_parms:
            add_props = query_parms.pop('additional-properties').split(',')
        else:
            add_props = []
        filter_args = query_parms

        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_adapters = []
        if cpc.dpm_enabled:
            for adapter in cpc.adapters.list(filter_args):
                result_adapter = {}
                for prop in cls.returned_props + add_props:
                    result_adapter[prop] = \
                        prop_copy(adapter.properties.get(prop))
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
        # the other properties are added in order to satisfy the end2end tests,
        # but some of their values are None or other dummy values.
        body2 = {
            'description': '',
            'status': 'active',
            'type': 'hipersockets',
            'adapter-id': None,  # TODO: Provide unique PCHID
            'adapter-family': 'hipersockets',
            'detected-card-type': 'hipersockets',
            'port-count': 1,
            'network-port-uris': [],  # Will be updated when adding port to HMC
            'state': 'online',
            'maximum-transmission-unit-size': 8,
            'configured-capacity': 42,
            'used-capacity': 42,
            'allowed-capacity': 42,
            'maximum-total-capacity': 42,
            'channel-path-id': None,  # TODO: Provide unique CHPID
            'physical-channel-status': 'operating',
        }
        body2.update(body)
        try:
            new_adapter = cpc.adapters.add(body2)
        except InputError as exc:
            new_exc = BadRequestError(method, uri, reason=5, message=str(exc))
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.BadRequestError

        # Create the VirtualSwitch for the new adapter
        vs_props = {
            'name': new_adapter.name,
            'type': 'hipersockets',
            'backing-adapter-uri': new_adapter.uri,
            'port': 0,
        }
        cpc.virtual_switches.add(vs_props)

        # Create the Port for the new adapter
        port_props = {
            'index': 0,
            'name': 'Port 0',
        }
        new_adapter.ports.add(port_props)

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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        adapter.manager.remove(adapter.oid)


class AdapterChangeCryptoTypeHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_required_fields(method, uri, body, ['crypto-type'])

        # Check the validity of the new crypto_type
        crypto_type = body['crypto-type']
        if crypto_type not in ['accelerator', 'cca-coprocessor',
                               'ep11-coprocessor']:
            raise BadRequestError(
                method, uri, reason=8,
                message=f"Invalid value for 'crypto-type' field: {crypto_type}")

        # Reflect the result of changing the crypto type
        adapter.properties['crypto-type'] = crypto_type


class AdapterChangeAdapterTypeHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_required_fields(method, uri, body, ['type'])

        new_adapter_type = body['type']

        # Check the validity of the adapter family
        adapter_family = adapter.properties.get('adapter-family', None)
        if adapter_family != 'ficon':
            raise BadRequestError(
                method, uri, reason=18,
                message="The adapter type cannot be changed for adapter "
                f"family: {adapter_family}")

        # Check the adapter status
        adapter_status = adapter.properties.get('status', None)
        if adapter_status == 'exceptions':
            raise BadRequestError(
                method, uri, reason=18,
                message="The adapter type cannot be changed for adapter "
                f"status: {adapter_status}")

        # Check the validity of the new adapter type
        if new_adapter_type not in ['fc', 'fcp', 'not-configured']:
            raise BadRequestError(
                method, uri, reason=8,
                message="Invalid new value for 'type' field: "
                f"{new_adapter_type}")

        # Check that the new adapter type is not already set
        adapter_type = adapter.properties.get('type', None)
        if new_adapter_type == adapter_type:
            raise BadRequestError(
                method, uri, reason=8,
                message="New value for 'type' field is already set: "
                f"{new_adapter_type}")

        # TODO: Reject if adapter is attached to a partition.

        # Reflect the result of changing the adapter type
        adapter.properties['type'] = new_adapter_type


class AdapterGetAssignedPartitionsHandler:
    """
    Handler class for operation: Get Partitions Assigned to Adapter.
    """

    valid_query_parms_get = ['name', 'status']

    returned_props = ['object-uri', 'name', 'status']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: Get Partitions Assigned to Adapter (requires DPM mode)."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        adapter_uri = uri.split('/operations/')[0]
        try:
            adapter = hmc.lookup_by_uri(adapter_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = adapter.manager.parent
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)

        adapter_family = adapter.properties['adapter-family']
        filter_args = query_parms
        assigned_partitions = []
        for partition in cpc.partitions.list(filter_args):

            if adapter_family in ('hipersockets', 'osa', 'roce', 'cna'):
                # Check if partition has a NIC backed by this adapter
                for nic in partition.nics.list():
                    if nic.properties['type'] in ('iqd', 'osd'):
                        vswitch_uri = nic.properties['virtual-switch-uri']
                        try:
                            vswitch = hmc.lookup_by_uri(vswitch_uri)
                        except KeyError:
                            new_exc = InvalidResourceError(method, vswitch_uri)
                            new_exc.__cause__ = None
                            raise new_exc
                        backing_adapter_uri = vswitch.properties[
                            'backing-adapter-uri']
                        if backing_adapter_uri == adapter_uri:
                            assigned_partitions.append(partition)
                            break  # Finding one NIC is sufficient
                    else:
                        # roce, cna
                        backing_port_uri = nic.properties[
                            'network-adapter-port-uri']
                        try:
                            port = hmc.lookup_by_uri(backing_port_uri)
                        except KeyError:
                            new_exc = InvalidResourceError(
                                method, backing_port_uri)
                            new_exc.__cause__ = None
                            raise new_exc
                        if port.manager.parent.uri == adapter_uri:
                            assigned_partitions.append(partition)
                            break  # Finding one NIC is sufficient

            # TODO: Finish implementaton when FakedStorageGroup supports VSRs
            # elif adapter_family in ('ficon'):
            #     # Check if partition has a storage group attached that has
            #     # a VSR backed by this adapter
            #     console = hmc.consoles.console
            #     for sg in console.storage_groups.list({'cpc-uri': cpc.uri}):
            #         found_partition = None
            #         for vsr_uri in sg.virtual_storage_resources.list():
            #             try:
            #                 vsr = hmc.lookup_by_uri(vsr_uri)
            #             except KeyError:
            #                 new_exc = InvalidResourceError(method, vsr_uri)
            #                 new_exc.__cause__ = None
            #                 raise new_exc
            #             if vsr.properties['partition-uri'] != partition.uri:
            #                 continue
            #             port_uri = vsr.properties['adapter-port-uri']
            #             try:
            #                 port = hmc.lookup_by_uri(port_uri)
            #             except KeyError:
            #                 new_exc = InvalidResourceError(method, port_uri)
            #                 new_exc.__cause__ = None
            #                 raise new_exc
            #             if port.manager.parent.uri == adapter_uri:
            #                 found_partition = partition
            #                 break  # Finding one VSR is sufficient
            #         if found_partition:
            #             assigned_partitions.append(found_partition)
            #             break  # Finding one VSR is sufficient

            elif adapter_family in ('crypto'):
                # Check if partition has a crypto config that includes this
                # adapter
                crypto_config = partition.properties['crypto-configuration']
                crypto_adapter_uris = crypto_config['crypto-adapter-uris']
                if adapter_uri in crypto_adapter_uris:
                    assigned_partitions.append(partition)

            elif adapter_family in ('accelerator'):
                # Check if partition has a virtual function backed by this
                # adapter
                for vf in partition.virtual_functions.list():
                    vf_adapter_uri = vf.properties['adapter-uri']
                if vf_adapter_uri == adapter_uri:
                    assigned_partitions.append(partition)
            else:
                pass
                # TODO: Enable check again when FakedStorageGroup supports VSRs
                # raise AssertionError(
                #     f"Adapter card with family {adapter_family} is not "
                #     "supported in zhmcclient_mock")

            # TODO: Add support for "nvme" - NVMA storage card.
            # TODO: Add support for "coupling" - Coupling card.
            # TODO: Add support for "ism" - Internal Shared Memory card.
            # TODO: Add support for "zhyperlink" - zHyperLink Express.

        part_infos = []
        for partition in assigned_partitions:
            part_info = {}
            for prop in cls.returned_props:
                part_info[prop] = partition.properties.get(prop)
            part_infos.append(part_info)

        return {'partitions-assigned-to-adapter': part_infos}


class NetworkPortHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single NetworkPort resource.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Update NetworkPort Properties."""
        try:
            network_port = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        # Check whether requested properties are modifiable
        check_writable(
            method, uri, body,
            [
                'description',
            ])
        network_port.update(body)


class StoragePortHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single StoragePort resource.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Update StoragePort Properties."""
        try:
            storage_port = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        # Check whether requested properties are modifiable
        check_writable(
            method, uri, body,
            [
                'description',
                'connection-endpoint-uri',
            ])
        storage_port.update(body)


class PartitionsHandler:
    """
    Handler class for HTTP methods on set of Partition resources.
    """

    valid_query_parms_get = ['name', 'status', 'type', 'additional-properties']

    returned_props = [
        'object-uri', 'name', 'status', 'type',
        # plus additional-properties
    ]

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Partitions of a CPC (empty result if not in DPM
        mode)."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        if 'additional-properties' in query_parms:
            add_props = query_parms.pop('additional-properties').split(',')
        else:
            add_props = []
        filter_args = query_parms

        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        # Reflect the result of listing the partition
        result_partitions = []
        if cpc.dpm_enabled:
            for partition in cpc.partitions.list(filter_args):
                result_partition = {}
                for prop in cls.returned_props + add_props:
                    result_partition[prop] = \
                        prop_copy(partition.properties.get(prop))
                result_partitions.append(result_partition)
        return {'partitions': result_partitions}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create Partition (requires DPM mode)."""

        def _partition_shortname(partition_name):
            """"
            Return 8-char short name from full name.

            Note: Does not guarantee to be reproducable.
            Note: Has a small chance to not be unique.
            """
            random_str = randrange(16 ^ 4)  # nosec B311
            return f"{partition_name.upper():_<4.4s}{random_str:04X}"

        def _partition_id():
            """"
            Generate a partition ID.

            Note: Does not guarantee to be reproducable.
            Note: Has a chance to not be unique.
            """
            random_str = randrange(80)  # nosec B311
            return f"{random_str:02X}"

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

        properties = copy.deepcopy(body)
        partition_name = properties['name']

        # Set defaults for optional input properties
        properties.setdefault('description', '')
        properties.setdefault('type', 'linux')
        properties.setdefault('short-name',
                              _partition_shortname(partition_name))
        properties.setdefault('autogenerate-partition-id', True)
        properties.setdefault('processor-mode', 'shared')
        properties.setdefault('reserve-resources', False)
        properties.setdefault('boot-device', 'none')
        properties.setdefault('boot-timeout', 60)
        properties.setdefault('access-global-performance-data', False)
        properties.setdefault('permit-cross-partition-commands', False)
        properties.setdefault('access-basic-counter-set', False)
        properties.setdefault('access-problem-state-counter-set', False)
        properties.setdefault('access-crypto-activity-counter-set', False)
        properties.setdefault('access-extended-counter-set', False)
        properties.setdefault('access-coprocessor-group-set', False)
        properties.setdefault('access-basic-sampling', False)
        properties.setdefault('access-diagnostic-sampling', False)
        properties.setdefault('permit-des-key-import-functions', True)
        properties.setdefault('permit-aes-key-import-functions', True)
        properties.setdefault('permit-ecc-key-import-functions', True)
        properties.setdefault('ssc-ipv4-gateway', None)
        properties.setdefault('ssc-ipv6-gateway', None)
        properties.setdefault('ssc-dns-servers', [])
        properties.setdefault('initial-ifl-processing-weight', 100)
        properties.setdefault('initial-cp-processing-weight', 100)
        properties.setdefault('acceptable-status', ['stopped', 'active'])
        properties.setdefault('cp-absolute-processor-capping', False)
        properties.setdefault('cp-absolute-processor-capping-value', 1.0)
        properties.setdefault('cp-processing-weight-capped', False)
        properties.setdefault('ifl-absolute-processor-capping', False)
        properties.setdefault('ifl-absolute-processor-capping-value', 1.0)
        properties.setdefault('ifl-processing-weight-capped', False)
        properties.setdefault('maximum-cp-processing-weight', 999)
        properties.setdefault('maximum-ifl-processing-weight', 999)
        properties.setdefault('minimum-cp-processing-weight', 1)
        properties.setdefault('minimum-ifl-processing-weight', 1)
        properties.setdefault('processor-management-enabled', False)

        # Set initial values for non-input properties
        check_set_noninput(method, uri, properties, 'status', 'stopped')
        check_set_noninput(method, uri, properties,
                           'has-unacceptable-status', False)
        check_set_noninput(method, uri, properties,
                           'is-locked', False)
        check_set_noninput(method, uri, properties, 'os-name', '')
        check_set_noninput(method, uri, properties, 'os-type', '')
        check_set_noninput(method, uri, properties, 'os-version', '')
        check_set_noninput(method, uri, properties, 'degraded-adapters', [])
        check_set_noninput(method, uri, properties,
                           'current-ifl-processing-weight', 100)
        check_set_noninput(method, uri, properties,
                           'current-cp-processing-weight', 100)
        reserved_memory = properties['maximum-memory'] - \
            properties['initial-memory']
        check_set_noninput(method, uri, properties,
                           'reserved-memory', reserved_memory)
        check_set_noninput(method, uri, properties, 'auto-start', False)
        check_set_noninput(method, uri, properties, 'boot-network-device', None)
        check_set_noninput(method, uri, properties,
                           'boot-configuration-selector', 0)
        check_set_noninput(method, uri, properties, 'boot-record-lba', 0)
        check_set_noninput(method, uri, properties, 'boot-load-parameters', '')
        check_set_noninput(method, uri, properties,
                           'boot-os-specific-parameters', '')
        check_set_noninput(method, uri, properties, 'boot-storage-device', None)
        check_set_noninput(method, uri, properties, 'boot-storage-volume', None)
        check_set_noninput(method, uri, properties,
                           'boot-logical-unit-number', '')
        check_set_noninput(method, uri, properties,
                           'boot-world-wide-port-name', '')
        check_set_noninput(method, uri, properties, 'boot-iso-image-name', None)
        check_set_noninput(method, uri, properties, 'boot-iso-ins-file', None)
        check_set_noninput(method, uri, properties, 'secure-execution', False)
        check_set_noninput(method, uri, properties, 'secure-boot', False)
        check_set_noninput(method, uri, properties, 'threads-per-processor', 0)
        check_set_noninput(method, uri, properties, 'virtual-function-uris', [])
        check_set_noninput(method, uri, properties, 'nic-uris', [])
        check_set_noninput(method, uri, properties, 'hba-uris', [])
        check_set_noninput(method, uri, properties, 'storage-group-uris', [])
        check_set_noninput(method, uri, properties, 'tape-link-uris', [])
        check_set_noninput(method, uri, properties, 'partition-link-uris', [])
        check_set_noninput(method, uri, properties,
                           'crypto-configuration', None)
        check_set_noninput(method, uri, properties,
                           'ssc-boot-selection', 'installer')
        check_set_noninput(method, uri, properties,
                           'available-features-list',
                           [
                               {
                                   'name': 'dpm-storage-management',
                                   'description': 'dpm-storage-management',
                                   'state': True,
                               },
                               {
                                   'name': 'dpm-fcp-tape-management',
                                   'description': 'dpm-fcp-tape-management',
                                   'state': True,
                               },
                           ])

        # Check conditionally required properties

        boot_device = properties['boot-device']

        if boot_device == 'ftp':
            check_required_fields(method, uri, body, [
                'boot-ftp-host',
                'boot-ftp-username',
                'boot-ftp-password',
                'boot-ftp-insfile',
            ])
        else:
            check_set_noninput(method, uri, properties, 'boot-ftp-host', None)
            check_set_noninput(method, uri, properties,
                               'boot-ftp-username', None)
            check_set_noninput(method, uri, properties,
                               'boot-ftp-password', None)
            check_set_noninput(method, uri, properties,
                               'boot-ftp-insfile', None)

        if boot_device == 'removable-media':
            check_required_fields(method, uri, body, [
                'boot-removable-media',
                'boot-removable-media-type',
            ])
        else:
            check_set_noninput(method, uri, properties,
                               'boot-removable-media', None)
            check_set_noninput(method, uri, properties,
                               'boot-removable-media-type', None)

        # Note: The other boot device types cannot be configured during creation

        auto_partition_id = properties['autogenerate-partition-id']
        if auto_partition_id:
            check_set_noninput(
                method, uri, properties, 'partition-id', _partition_id())
        else:
            check_required_fields(method, uri, body, ['partition-id'])

        partition_type = properties['type']
        if partition_type == 'ssc':
            check_required_fields(method, uri, body,
                                  ['ssc-host-name', 'ssc-master-userid',
                                   'ssc-master-pw'])
        else:
            check_set_noninput(method, uri, properties, 'ssc-host-name', None)
            check_set_noninput(method, uri, properties,
                               'ssc-master-userid', None)
            check_set_noninput(method, uri, properties, 'ssc-master-pw', None)

        ifl_processors = properties.get('ifl-processors', None)
        cp_processors = properties.get('cp-processors', None)
        if not ifl_processors and not cp_processors:
            new_exc = BadRequestError(
                method, uri, reason=1,
                message="At least one of 'ifl-processors' or 'cp-processors' "
                "is required")
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.BadRequestError
        properties.setdefault('ifl-processors', 0)
        properties.setdefault('cp-processors', 0)

        # Reflect the result of creating the partition
        new_partition = cpc.partitions.add(properties)
        return {'object-uri': new_partition.uri}


class PartitionHandler(GenericGetPropertiesHandler,
                       GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single Partition resource.
    """

    valid_query_parms_get = ['properties']

    # TODO: Add check_valid_cpc_status() in Update Partition Properties
    # TODO: Add check_partition_status(transitional) in Update Partition Props
    # TODO: Add check whether properties are modifiable in Update Part. Props
    # TODO: Remove 'ssc-master-pw' property from result

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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['stopped'])

        # Reflect the result of deleting the partition
        partition.manager.remove(partition.oid)


class PartitionStartHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['stopped'])

        # Reflect the result of starting the partition
        partition.properties['status'] = 'active'
        return {}


class PartitionStopHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
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


class PartitionScsiDumpHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
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


class PartitionStartDumpProgramHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['active', 'degraded', 'paused',
                                               'terminated'])
        check_required_fields(method, uri, body,
                              ['dump-program-info',
                               'dump-program-type'])

        # We don't reflect the dump in the mock state.
        return {}


class PartitionPswRestartHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               valid_statuses=['active', 'paused',
                                               'terminated'])

        # We don't reflect the PSW restart in the mock state.
        return {}


class PartitionMountIsoImageHandler:
    """
    Handler class for operation: Mount ISO Image.
    """

    valid_query_parms_post = ['image-name', 'ins-file-name']

    @classmethod
    def post(cls, method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Mount ISO Image (requires DPM mode)."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_post)

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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])

        # Parse and check required query parameters
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


class PartitionUnmountIsoImageHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
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


class PartitionIncreaseCryptoConfigHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
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


class PartitionDecreaseCryptoConfigHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
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


class PartitionChangeCryptoConfigHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
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


class HbasHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])

        partition.hbas.remove(hba.oid)


class HbaReassignPortHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])
        check_required_fields(method, uri, body, ['adapter-port-uri'])

        # Reflect the effect of the operation on the HBA
        new_port_uri = body['adapter-port-uri']
        hba.properties['adapter-port-uri'] = new_port_uri


class NicsHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
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
                message=f"The input properties for creating a NIC {nic_name!r} "
                f"in partition {partition.name!r} must specify either the "
                "'network-adapter-port-uri' or the "
                "'virtual-switch-uri' property.")

        # We have ensured that the vswitch exists, so no InputError handling
        new_nic = partition.nics.add(body)

        return {'element-uri': new_nic.uri}


class NicHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single Nic resource.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Update NIC Properties."""
        try:
            nic = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        partition = nic.manager.parent
        cpc = partition.manager.parent
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])
        # Check whether requested properties are modifiable
        check_writable(
            method, uri, body,
            [
                'description',
                'name',
                'device-number',
                'network-adapter-port-uri',
                'ssc-management-nic',
                'ssc-ip-address-type',
                'ssc-ip-address',
                'ssc-mask-prefix',
                'vlan-id',
                'mac-address',
                'vlan-type',
                'function-number',
                'function-range',
            ])
        nic.update(body)

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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])

        partition.nics.remove(nic.oid)


class VirtualFunctionsHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)
        check_partition_status(method, uri, partition,
                               invalid_statuses=['starting', 'stopping'])

        partition.virtual_functions.remove(vf.oid)


class VirtualSwitchesHandler:
    """
    Handler class for HTTP methods on set of VirtualSwitch resources.
    """

    valid_query_parms_get = ['name', 'type', 'additional-properties']

    returned_props = [
        'object-uri', 'name', 'type',
        # plus additional-properties
    ]

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Virtual Switches of a CPC (empty result if not in
        DPM mode)."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        if 'additional-properties' in query_parms:
            add_props = query_parms.pop('additional-properties').split(',')
        else:
            add_props = []
        filter_args = query_parms

        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_vswitches = []
        if cpc.dpm_enabled:
            for vswitch in cpc.virtual_switches.list(filter_args):
                result_vswitch = {}
                for prop in cls.returned_props + add_props:
                    result_vswitch[prop] = \
                        prop_copy(vswitch.properties.get(prop))
                result_vswitches.append(result_vswitch)
        return {'virtual-switches': result_vswitches}


class VirtualSwitchHandler(GenericGetPropertiesHandler,
                           GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single VirtualSwitch resource.
    """
    pass


class VirtualSwitchGetVnicsHandler:
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
        if not cpc.dpm_enabled:
            raise CpcNotInDpmError(method, uri, cpc)

        connected_vnic_uris = vswitch.properties['connected-vnic-uris']
        return {'connected-vnic-uris': connected_vnic_uris}


class StorageGroupsHandler:
    """
    Handler class for HTTP methods on set of StorageGroup resources.
    """

    valid_query_parms_get = ['cpc-uri', 'name', 'fulfillment-state', 'type']

    returned_props = ['object-uri', 'cpc-uri', 'name', 'fulfillment-state',
                      'type']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Storage Groups (always global but with filters)."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        result_storage_groups = []
        for sg in hmc.consoles.console.storage_groups.list(filter_args):
            result_sg = {}
            for prop in cls.returned_props:
                result_sg[prop] = prop_copy(sg.properties.get(prop))
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
        body2.setdefault('shared', True)
        body2.setdefault('description', '')
        body2['fulfillment-state'] = 'pending'
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
                        f"field: {operation}")

        return {
            'object-uri': new_storage_group.uri,
            'element-uris': sv_uris,
        }


class StorageGroupHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single StorageGroup resource.
    """
    pass


class StorageGroupModifyHandler:
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
                    # Add other properties with default values
                    sv_props.setdefault('fulfillment-state', 'pending')
                    sv_props.setdefault('usage', 'data')
                    if 'element-uri' in sv_props:
                        raise BadRequestError(
                            method, uri, 7,
                            "The 'element-uri' field in storage-volumes is "
                            "invalid for the create operation")
                    sv_obj = storage_group.storage_volumes.add(sv_props)
                    sv_uris.append(sv_obj.uri)
                elif operation == 'modify':
                    check_required_fields(method, uri, sv_req, ['element-uri'])
                    sv_uri = sv_req['element-uri']
                    sv_props = sv_req.copy()
                    del sv_props['operation']
                    storage_volume = hmc.lookup_by_uri(sv_uri)
                    storage_volume.update(sv_props)
                elif operation == 'delete':
                    check_required_fields(method, uri, sv_req, ['element-uri'])
                    sv_uri = sv_req['element-uri']
                    storage_volume = hmc.lookup_by_uri(sv_uri)
                    storage_group.storage_volumes.remove(storage_volume.oid)
                else:
                    raise BadRequestError(
                        method, uri, 5,
                        "Invalid value for storage-volumes 'operation' "
                        f"field: {operation}")

        return {
            'element-uris': sv_uris,  # SVs created, maintaining the order
        }


class StorageGroupDeleteHandler:
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


class StorageGroupRequestFulfillmentHandler:
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


class StorageGroupAddCandidatePortsHandler:
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
                                    "list of storage group "
                                    f"{storage_group.name}: {ap_uri}")
            candidate_adapter_port_uris.append(ap_uri)


class StorageGroupRemoveCandidatePortsHandler:
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
                                    "list of storage group "
                                    f"{storage_group.name}: {ap_uri}")
            candidate_adapter_port_uris.remove(ap_uri)


class StorageVolumesHandler:
    """
    Handler class for HTTP methods on set of StorageVolume resources.
    """

    valid_query_parms_get = ['name', 'fulfillment-state', 'maximum-size',
                             'minimum-size', 'usage']

    returned_props = ['element-uri', 'name', 'fulfillment-state', 'size',
                      'usage']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Storage Volumes of a Storage Group."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        sg_uri = re.sub('/storage-volumes$', '', uri)
        try:
            sg = hmc.lookup_by_uri(sg_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_storage_volumes = []
        for sv in sg.storage_volumes.list(filter_args):
            result_sv = {}
            for prop in cls.returned_props:
                result_sv[prop] = prop_copy(sv.properties.get(prop))
            result_storage_volumes.append(result_sv)
        return {'storage-volumes': result_storage_volumes}


class StorageVolumeHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single StorageVolume resource.
    """
    pass


class VirtualStorageResourcesHandler:
    """
    Handler class for HTTP methods on set of VirtualStorageResource resources.
    """

    valid_query_parms_get = ['name', 'device-number', 'adapter-port-uri',
                             'partition-uri']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Storage Volumes of a Storage Group."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        sg_uri = re.sub('/virtual-storage-resources$', '', uri)
        try:
            sg = hmc.lookup_by_uri(sg_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_vsrs = []
        for vsr in sg.virtual_storage_resources.list(filter_args):
            result_vsr = {}
            for prop in vsr.properties:
                if prop in ('element-uri', 'name', 'device-number',
                            'adapter-port-uri', 'partition-uri'):
                    result_vsr[prop] = prop_copy(vsr.properties[prop])
            result_vsrs.append(result_vsr)
        return {'virtual-storage-resources': result_vsrs}


class VirtualStorageResourceHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single VirtualStorageResource resource.
    """
    pass


class StorageTemplatesHandler:
    """
    Handler class for HTTP methods on set of StorageGroupTemplate resources.
    """

    valid_query_parms_get = ['cpc-uri', 'name', 'type']

    returned_props = ['object-uri', 'cpc-uri', 'name', 'type']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """
        Operation: List Storage Templates (always global but with filters).
        """
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        result_storage_group_templates = []
        for sgt in hmc.consoles.console.storage_group_templates.list(
                filter_args):
            result_sgt = {}
            for prop in cls.returned_props:
                result_sgt[prop] = prop_copy(sgt.properties.get(prop))
            result_storage_group_templates.append(result_sgt)
        return {'storage-templates': result_storage_group_templates}

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Create Storage Template."""
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
        sv_requests = body2.pop('storage-template-volumes', None)
        body2.setdefault('shared', True)
        body2.setdefault('description', '')
        body2['fulfillment-state'] = 'pending'
        new_sgt = hmc.consoles.console.storage_group_templates.add(body2)

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
                            "The 'element-uri' field in "
                            "storage-template-volumes is "
                            "invalid for the create operation")
                    sv_uri = new_sgt.storage_volume_templates.add(sv_props)
                    sv_uris.append(sv_uri)
                else:
                    raise BadRequestError(
                        method, uri, 5,
                        "Invalid value for storage-template-volumes "
                        f"'operation' field: {operation}")

        return {
            'object-uri': new_sgt.uri,
            'element-uris': sv_uris,
        }


class StorageTemplateHandler(GenericGetPropertiesHandler,
                             GenericDeleteHandler):
    """
    Handler class for HTTP methods on single StorageGroupTemplate resource.
    """
    pass


class StorageTemplateModifyHandler:
    """
    Handler class for operation: Modify Storage Template Properties.
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Modify Storage Template Properties."""
        assert wait_for_completion is True  # async not supported yet
        # The URI is a POST operation, so we need to construct the SG URI
        sgt_oid = uri_parms[0]
        sgt_uri = '/api/storage-templates/' + sgt_oid
        try:
            sgt = hmc.lookup_by_uri(sgt_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError

        # Reflect the result of modifying the storage group template

        body2 = body.copy()
        sv_requests = body2.pop('storage-template-volumes', None)
        sgt.update(body2)

        sv_uris = []
        if sv_requests:
            for sv_req in sv_requests:
                check_required_fields(method, uri, sv_req, ['operation'])
                operation = sv_req['operation']
                if operation == 'create':
                    sv_props = sv_req.copy()
                    del sv_props['operation']
                    # Add other properties with default values
                    sv_props.setdefault('usage', 'data')
                    if 'element-uri' in sv_props:
                        raise BadRequestError(
                            method, uri, 7,
                            "The 'element-uri' field in "
                            "storage-template-volumes is "
                            "invalid for the create operation")
                    sv_obj = sgt.storage_volume_templates.add(sv_props)
                    sv_uris.append(sv_obj.uri)
                elif operation == 'modify':
                    check_required_fields(method, uri, sv_req, ['element-uri'])
                    sv_uri = sv_req['element-uri']
                    sv_props = sv_req.copy()
                    del sv_props['operation']
                    storage_volume = hmc.lookup_by_uri(sv_uri)
                    storage_volume.update(sv_props)
                elif operation == 'delete':
                    check_required_fields(method, uri, sv_req, ['element-uri'])
                    sv_uri = sv_req['element-uri']
                    storage_volume = hmc.lookup_by_uri(sv_uri)
                    sgt.storage_volume_templates.remove(storage_volume.oid)
                else:
                    raise BadRequestError(
                        method, uri, 5,
                        "Invalid value for storage-volumes 'operation' "
                        f"field: {operation}")

        return {
            'element-uris': sv_uris,  # SVs created, maintaining the order
        }


class StorageTemplateVolumesHandler:
    """
    Handler class for HTTP methods on set of StorageGroupTemplate resources.
    """

    valid_query_parms_get = ['name', 'maximum-size', 'minimum-size', 'usage']

    returned_props = ['element-uri', 'name', 'size', 'usage']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Storage Volumes of a Storage (Group) Template."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        sgt_uri = re.sub('/storage-template-volumes$', '', uri)
        try:
            sgt = hmc.lookup_by_uri(sgt_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_storage_volume_templates = []
        for sv in sgt.storage_volume_templates.list(filter_args):
            result_sv = {}
            for prop in cls.returned_props:
                result_sv[prop] = prop_copy(sv.properties.get(prop))
            result_storage_volume_templates.append(result_sv)
        return {'storage-template-volumes': result_storage_volume_templates}


class StorageTemplateVolumeHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single StorageGroupTemplate resource.
    """
    pass


class CapacityGroupsHandler:
    """
    Handler class for HTTP methods on set of CapacityGroup resources.
    """

    valid_query_parms_get = ['name']

    returned_props = ['element-uri', 'name']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Capacity Groups (always global but with filters)."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        cpc_oid = uri_parms[0]
        cpc_uri = '/api/cpcs/' + cpc_oid
        try:
            cpc = hmc.lookup_by_uri(cpc_uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_capacity_groups = []
        for cg in cpc.capacity_groups.list(filter_args):
            result_cg = {}
            for prop in cls.returned_props:
                result_cg[prop] = prop_copy(cg.properties.get(prop))
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
                message=f"Capacity group {capacity_group.name!r} is not empty "
                f"and contains partitions with URIs {partition_uris!r}")

        # Delete the mocked resource
        capacity_group.manager.remove(capacity_group.oid)


class CapacityGroupAddPartitionHandler:
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
                                f"Partition {partition.name} is in "
                                f"{processor_mode} processor mode")

        # Check the partition is not in this capacity group
        partition_uris = capacity_group.properties['partition-uris']
        if partition.uri in partition_uris:
            raise ConflictError(method, uri, 130,
                                f"Partition {partition.name} is already a "
                                "member of this capacity group "
                                f"{capacity_group.name}")

        # Check the partition is not in any other capacity group
        for cg in cpc.capacity_groups.list():
            if partition.uri in cg.properties['partition-uris']:
                raise ConflictError(method, uri, 120,
                                    f"Partition {partition.name} is already a "
                                    "member of another capacity group "
                                    f"{cg.name}")

        # Reflect the result of adding the partition to the capacity group
        capacity_group.properties['partition-uris'].append(partition.uri)


class CapacityGroupRemovePartitionHandler:
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
                                f"Partition {partition.name} is not a member "
                                f"of capacity group {capacity_group.name}")

        # Reflect the result of removing the partition from the capacity group
        capacity_group.properties['partition-uris'].remove(partition.uri)


class LparsHandler:
    """
    Handler class for HTTP methods on set of Lpar resources.
    """

    valid_query_parms_get = ['name']

    returned_props = ['object-uri', 'name', 'status']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """Operation: List Logical Partitions of CPC (empty result in DPM
        mode."""
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_lpars = []
        if not cpc.dpm_enabled:
            for lpar in cpc.lpars.list(filter_args):
                result_lpar = {}
                for prop in cls.returned_props:
                    result_lpar[prop] = prop_copy(lpar.properties.get(prop))
                result_lpars.append(result_lpar)
        return {'logical-partitions': result_lpars}


class LparHandler(GenericGetPropertiesHandler):
    """
    Handler class for HTTP methods on single Lpar resource.
    """

    valid_query_parms_get = ['properties', 'cached-acceptable', 'group-uri']

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Update Logical Partition Properties."""
        assert wait_for_completion is True  # async not supported yet
        try:
            lpar = hmc.lookup_by_uri(uri)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        cpc = lpar.manager.parent
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)
        check_valid_cpc_status(method, uri, cpc)
        status = lpar.properties.get('status', None)
        if status not in ('not-operating', 'operating', 'exceptions'):
            # LPAR permits property updates only when a active
            new_exc = ConflictError(
                method, uri, 1,
                f"Cannot update LPAR properties in status {status}")
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.ConflictError
        # TODO: Add check whether requested properties are modifiable
        lpar.update(body)


class LparActivateHandler:
    """
    A handler class for the "Activate Logical Partition" operation.
    """

    @staticmethod
    def get_status():
        """
        Status retrieval method that returns the status the faked Lpar will
        have after completion of the "Activate Logical Partition" operation.

        This method returns the successful status 'not-operating' for LPARs that
        do not auto-load their OSs, and can be mocked by testcases to return a
        different status (e.g. 'operating' for LPARs that do auto-load, or
        'acceptable' or 'exceptions').
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
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)

        status = lpar.properties.get('status', None)
        force = body.get('force', False) if body else False
        if status == 'operating' and not force:
            raise ServerError(
                method, uri, reason=263,
                message=f"LPAR {lpar.name!r} could not be activated because "
                f"the LPAR is in status {status} (and force was not "
                "specified).")

        act_profile_name = body.get('activation-profile-name', None)
        if not act_profile_name:
            act_profile_name = lpar.properties.get(
                'next-activation-profile-name', None)
        if act_profile_name is None:
            act_profile_name = ''

        # Perform the check between LPAR name and profile name
        if act_profile_name != lpar.name:
            raise ServerError(
                method, uri, reason=263,
                message=f"LPAR {lpar.name!r} could not be activated because "
                "the name of the image activation profile "
                f"{act_profile_name!r} is different from the LPAR name.")

        # Reflect the activation in the resource
        lpar.properties['status'] = LparActivateHandler.get_status()
        lpar.properties['last-used-activation-profile'] = act_profile_name


class LparDeactivateHandler:
    """
    A handler class for the "Deactivate Logical Partition" operation.
    """

    @staticmethod
    def get_status():
        """
        Status retrieval method that returns the status the faked Lpar will
        have after completion of the "Deactivate Logical Partition" operation.

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
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)

        status = lpar.properties.get('status', None)
        force = body.get('force', False) if body else False
        if status == 'not-activated' and not force:
            # Note that the current behavior (on EC12) is that force=True
            # still causes this error to be returned (different behavior
            # compared to the Activate and Load operations).
            raise ServerError(
                method, uri, reason=263,
                message=f"LPAR {lpar.name!r} could not be deactivated because "
                "the LPAR is already deactivated (and force was not "
                "specified).")
        if status == 'operating' and not force:
            raise ServerError(
                method, uri, reason=263,
                message=f"LPAR {lpar.name!r} could not be deactivated because "
                f"the LPAR is in status {status} (and force was not "
                "specified).")

        # Reflect the deactivation in the resource
        lpar.properties['status'] = LparDeactivateHandler.get_status()


class LparLoadHandler:
    """
    A handler class for the "Load Logical Partition" operation.
    """

    @staticmethod
    def get_status():
        """
        Status retrieval method that returns the status the faked Lpar will
        have after completion of the "Load Logical Partition" operation.

        This method returns the successful status 'operating', and can be
        mocked by testcases to return a different status (e.g. 'acceptable' or
        'exceptions').
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
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)

        status = lpar.properties.get('status', None)
        force = body.get('force', False) if body else False
        clear_indicator = body.get('clear-indicator', True) if body else True
        store_status_indicator = body.get('store-status-indicator',
                                          False) if body else False
        if status == 'not-activated':
            raise ConflictError(
                method, uri, reason=0,
                message=f"LPAR {lpar.name!r} could not be loaded because "
                f"the LPAR is in status {status}.")
        if status == 'operating' and not force:
            raise ServerError(
                method, uri, reason=263,
                message=f"LPAR {lpar.name!r} could not be loaded because the "
                "LPAR is already loaded (and force was not specified).")

        load_address = body.get('load-address', None) if body else None
        if not load_address:
            # Starting with z14, this parameter is optional and a last-used
            # property is available.
            load_address = lpar.properties.get('last-used-load-address', None)
        if load_address is None:
            # TODO: Verify actual error for this case on a z14.
            raise BadRequestError(
                method, uri, reason=5,
                message=f"LPAR {lpar.name!r} could not be loaded because a "
                "load address is not specified in the request or in the Lpar "
                "last-used property")

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


class LparScsiLoadHandler:
    """
    A handler class for the "SCSI Load" operation.
    """

    @staticmethod
    def get_status():
        """
        Status retrieval method that returns the status the faked Lpar will
        have after completion of the "SCSI Load" operation.

        This method returns the successful status 'operating', and can be
        mocked by testcases to return a different status (e.g. 'acceptable' or
        'exceptions').
        """
        return 'operating'

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: SCSI Load (requires classic mode)."""
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
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)

        check_required_fields(method, uri, body,
                              ['load-address', 'world-wide-port-name',
                               'logical-unit-number'])

        status = lpar.properties.get('status', None)
        force = body.get('force', False)

        if status == 'not-activated':
            raise ConflictError(
                method, uri, reason=0,
                message=f"LPAR {lpar.name!r} could not be loaded because the "
                f"LPAR is in status {status}.")
        if status == 'operating' and not force:
            raise ServerError(
                method, uri, reason=263,
                message=f"LPAR {lpar.name!r} could not be loaded because the "
                "LPAR is already loaded (and force was not specified).")

        hmc_version_str = cpc.manager.hmc.hmc_version
        hmc_version = tuple(map(int, hmc_version_str.split('.')))

        # Update the LPAR resource

        desired_status = LparScsiLoadHandler.get_status()
        lpar.properties['status'] = desired_status

        if hmc_version >= (2, 14, 0):
            load_address = body.get('load-address')
            load_parameter = body.get('load-parameter', '')
            lpar.properties['last-used-load-address'] = load_address
            lpar.properties['last-used-load-parameter'] = load_parameter

        if hmc_version >= (2, 14, 1):
            wwpn = body.get('world-wide-port-name')
            lun = body.get('logical-unit-number')
            disk_partition_id = body.get('disk-partition-id', 0)
            os_load_parameters = body.get(
                'operating-system-specific-load-parameters', '')
            boot_record_lba = body.get('boot-record-logical-block-address', '0')
            lpar.properties['last-used-world-wide-port-name'] = wwpn
            lpar.properties['last-used-logical-unit-number'] = lun
            lpar.properties['last-used-disk-partition-id'] = disk_partition_id
            lpar.properties[
                'last-used-operating-system-specific-load-parameters'] = \
                os_load_parameters
            lpar.properties['last-used-boot-record-logical-block-address'] = \
                boot_record_lba

        if hmc_version >= (2, 15, 0):
            secure_boot = body.get('secure-boot', False)
            lpar.properties['last-used-load-type'] = 'ipltype-scsi'
            lpar.properties['last-used-secure-boot'] = secure_boot

        if hmc_version >= (2, 16, 0):
            clear_indicator = body.get('clear-indicator', True)
            lpar.properties['last-used-clear-indicator'] = clear_indicator


class LparScsiDumpHandler:
    """
    A handler class for the "SCSI Dump" operation.
    """

    @staticmethod
    def get_status():
        """
        Status retrieval method that returns the status the faked Lpar will
        have after completion of the "SCSI Dump" operation.

        This method returns the successful status 'operating', and can be
        mocked by testcases to return a different status (e.g. 'acceptable' or
        'exceptions').
        """
        return 'operating'

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: SCSI Dump (requires classic mode)."""
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
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)

        check_required_fields(method, uri, body,
                              ['load-address', 'world-wide-port-name',
                               'logical-unit-number'])

        status = lpar.properties.get('status', None)
        force = body.get('force', False)

        if status == 'not-activated':
            raise ConflictError(
                method, uri, reason=0,
                message=f"LPAR {lpar.name!r} could not be loaded because "
                f"the LPAR is in status {status}.")
        if status == 'operating' and not force:
            raise ServerError(
                method, uri, reason=263,
                message=f"LPAR {lpar.name!r} could not be loaded because the "
                "LPAR is already loaded (and force was not specified).")

        hmc_version_str = cpc.manager.hmc.hmc_version
        hmc_version = tuple(map(int, hmc_version_str.split('.')))

        # Update the LPAR resource

        desired_status = LparScsiLoadHandler.get_status()
        lpar.properties['status'] = desired_status

        if hmc_version >= (2, 14, 0):
            load_address = body.get('load-address')
            load_parameter = body.get('load-parameter', '')
            lpar.properties['last-used-load-address'] = load_address
            lpar.properties['last-used-load-parameter'] = load_parameter

        if hmc_version >= (2, 14, 1):
            wwpn = body.get('world-wide-port-name')
            lun = body.get('logical-unit-number')
            disk_partition_id = body.get('disk-partition-id', 0)
            os_load_parameters = body.get(
                'operating-system-specific-load-parameters', '')
            boot_record_lba = body.get('boot-record-logical-block-address', '0')
            lpar.properties['last-used-world-wide-port-name'] = wwpn
            lpar.properties['last-used-logical-unit-number'] = lun
            lpar.properties['last-used-disk-partition-id'] = disk_partition_id
            lpar.properties[
                'last-used-operating-system-specific-load-parameters'] = \
                os_load_parameters
            lpar.properties['last-used-boot-record-logical-block-address'] = \
                boot_record_lba

        if hmc_version >= (2, 15, 0):
            secure_boot = body.get('secure-boot', False)
            lpar.properties['last-used-load-type'] = 'ipltype-scsidump'
            lpar.properties['last-used-secure-boot'] = secure_boot

        # Note: 'last-used-clear-indicator' is not changed, since this operation
        # does not have a corresponding parameter.


class LparNvmeLoadHandler:
    """
    A handler class for the "NVME Load" operation.
    """

    @staticmethod
    def get_status():
        """
        Status retrieval method that returns the status the faked Lpar will
        have after completion of the "NVME Load" operation.

        This method returns the successful status 'operating', and can be
        mocked by testcases to return a different status (e.g. 'acceptable' or
        'exceptions').
        """
        return 'operating'

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: NVME Load (requires classic mode)."""
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
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)

        check_required_fields(method, uri, body, ['load-address'])

        status = lpar.properties.get('status', None)
        force = body.get('force', False)

        if status == 'not-activated':
            raise ConflictError(
                method, uri, reason=0,
                message=f"LPAR {lpar.name!r} could not be loaded because the "
                f"LPAR is in status {status}.")
        if status == 'operating' and not force:
            raise ServerError(
                method, uri, reason=263,
                message=f"LPAR {lpar.name!r} could not be loaded because the "
                "LPAR is already loaded (and force was not specified).")

        hmc_version_str = cpc.manager.hmc.hmc_version
        hmc_version = tuple(map(int, hmc_version_str.split('.')))

        # Update the LPAR resource

        desired_status = LparNvmeLoadHandler.get_status()
        lpar.properties['status'] = desired_status

        if hmc_version >= (2, 14, 0):
            load_address = body.get('load-address')
            load_parameter = body.get('load-parameter', '')
            lpar.properties['last-used-load-address'] = load_address
            lpar.properties['last-used-load-parameter'] = load_parameter

        if hmc_version >= (2, 14, 1):
            disk_partition_id = body.get('disk-partition-id', 0)
            os_load_parameters = body.get(
                'operating-system-specific-load-parameters', '')
            boot_record_lba = body.get('boot-record-logical-block-address', '0')
            lpar.properties['last-used-disk-partition-id'] = disk_partition_id
            lpar.properties[
                'last-used-operating-system-specific-load-parameters'] = \
                os_load_parameters
            lpar.properties['last-used-boot-record-logical-block-address'] = \
                boot_record_lba

        if hmc_version >= (2, 15, 0):
            secure_boot = body.get('secure-boot', False)
            lpar.properties['last-used-load-type'] = 'ipltype-nvme'
            lpar.properties['last-used-secure-boot'] = secure_boot

        if hmc_version >= (2, 16, 0):
            clear_indicator = body.get('clear-indicator', True)
            lpar.properties['last-used-clear-indicator'] = clear_indicator


class LparNvmeDumpHandler:
    """
    A handler class for the "NVME Dump" operation.
    """

    @staticmethod
    def get_status():
        """
        Status retrieval method that returns the status the faked Lpar will
        have after completion of the "NVME Dump" operation.

        This method returns the successful status 'operating', and can be
        mocked by testcases to return a different status (e.g. 'acceptable' or
        'exceptions').
        """
        return 'operating'

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: NVME Dump (requires classic mode)."""
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
        if cpc.dpm_enabled:
            raise CpcInDpmError(method, uri, cpc)

        check_required_fields(method, uri, body, ['load-address'])

        status = lpar.properties.get('status', None)
        force = body.get('force', False)

        if status == 'not-activated':
            raise ConflictError(
                method, uri, reason=0,
                message=f"LPAR {lpar.name!r} could not be loaded because the "
                f"LPAR is in status {status}.")
        if status == 'operating' and not force:
            raise ServerError(
                method, uri, reason=263,
                message=f"LPAR {lpar.name!r} could not be loaded because the "
                "LPAR is already loaded (and force was not specified).")

        hmc_version_str = cpc.manager.hmc.hmc_version
        hmc_version = tuple(map(int, hmc_version_str.split('.')))

        # Update the LPAR resource

        desired_status = LparNvmeLoadHandler.get_status()
        lpar.properties['status'] = desired_status

        if hmc_version >= (2, 14, 0):
            load_address = body.get('load-address')
            load_parameter = body.get('load-parameter', '')
            lpar.properties['last-used-load-address'] = load_address
            lpar.properties['last-used-load-parameter'] = load_parameter

        if hmc_version >= (2, 14, 1):
            disk_partition_id = body.get('disk-partition-id', 0)
            os_load_parameters = body.get(
                'operating-system-specific-load-parameters', '')
            boot_record_lba = body.get('boot-record-logical-block-address', '0')
            lpar.properties['last-used-disk-partition-id'] = disk_partition_id
            lpar.properties[
                'last-used-operating-system-specific-load-parameters'] = \
                os_load_parameters
            lpar.properties['last-used-boot-record-logical-block-address'] = \
                boot_record_lba

        if hmc_version >= (2, 15, 0):
            secure_boot = body.get('secure-boot', False)
            lpar.properties['last-used-load-type'] = 'ipltype-nvmedump'
            lpar.properties['last-used-secure-boot'] = secure_boot

        # Note: 'last-used-clear-indicator' is not changed, since this operation
        # does not have a corresponding parameter.


class ResetActProfilesHandler:
    """
    Handler class for HTTP methods on set of Reset ActivationProfile resources.
    """

    valid_query_parms_get = ['name']

    returned_props = ['element-uri', 'name']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """
        Operation: List Reset Activation Profiles.
        In case of DPM mode, an empty list is returned.
        """
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_profiles = []
        if not cpc.dpm_enabled:
            for profile in cpc.reset_activation_profiles.list(filter_args):
                result_profile = {}
                for prop in cls.returned_props:
                    result_profile[prop] = \
                        prop_copy(profile.properties.get(prop))
                result_profiles.append(result_profile)
        return {'reset-activation-profiles': result_profiles}


class ResetActProfileHandler(GenericGetPropertiesHandler,
                             GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single Reset ActivationProfile resource.
    """

    valid_query_parms_get = ['properties', 'cached-acceptable']


class ImageActProfilesHandler:
    """
    Handler class for HTTP methods on set of Image ActivationProfile resources.
    """

    valid_query_parms_get = ['name', 'additional-properties']

    returned_props = [
        'element-uri', 'name',
        # plus additional-properties
    ]

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """
        Operation: List Image Activation Profiles.
        In case of DPM mode, an empty list is returned.
        """
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        if 'additional-properties' in query_parms:
            add_props = query_parms.pop('additional-properties').split(',')
        else:
            add_props = []
        filter_args = query_parms

        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_profiles = []
        if not cpc.dpm_enabled:
            for profile in cpc.image_activation_profiles.list(filter_args):
                result_profile = {}
                for prop in cls.returned_props + add_props:
                    result_profile[prop] = \
                        prop_copy(profile.properties.get(prop))
                result_profiles.append(result_profile)
        return {'image-activation-profiles': result_profiles}


class ImageActProfileHandler(GenericGetPropertiesHandler,
                             GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single Image ActivationProfile resource.
    """

    valid_query_parms_get = ['properties', 'cached-acceptable']


class LoadActProfilesHandler:
    """
    Handler class for HTTP methods on set of Load ActivationProfile resources.
    """

    valid_query_parms_get = ['name']

    returned_props = ['element-uri', 'name']

    @classmethod
    def get(cls, method, hmc, uri, uri_parms, logon_required):
        # pylint: disable=unused-argument
        """
        Operation: List Load Activation Profiles.
        In case of DPM mode, an empty list is returned.
        """
        uri, query_parms = parse_query_parms(method, uri)
        check_invalid_query_parms(
            method, uri, query_parms, cls.valid_query_parms_get)
        filter_args = query_parms

        cpc_oid = uri_parms[0]
        try:
            cpc = hmc.cpcs.lookup_by_oid(cpc_oid)
        except KeyError:
            new_exc = InvalidResourceError(method, uri)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient_mock.InvalidResourceError
        result_profiles = []
        if not cpc.dpm_enabled:
            for profile in cpc.load_activation_profiles.list(filter_args):
                result_profile = {}
                for prop in cls.returned_props:
                    result_profile[prop] = \
                        prop_copy(profile.properties.get(prop))
                result_profiles.append(result_profile)
        return {'load-activation-profiles': result_profiles}


class LoadActProfileHandler(GenericGetPropertiesHandler,
                            GenericUpdatePropertiesHandler):
    """
    Handler class for HTTP methods on single Load ActivationProfile resource.
    """

    valid_query_parms_get = ['properties', 'cached-acceptable']


class SubmitRequestsHandler:
    """
    Handler class for "Submit Requests" operation (= aggregation service).
    """

    @staticmethod
    def post(method, hmc, uri, uri_parms, body, logon_required,
             wait_for_completion):
        # pylint: disable=unused-argument
        """Operation: Submit Requests."""
        assert wait_for_completion is True  # async not supported yet

        check_required_fields(method, uri, body, ['requests'])

        # Process each operation in the request list
        # We process this serially, ignoring the 'threads' paramneter.
        responses = []
        # TODO: Support for general 'req-headers' and 'resp-headers'
        for request in body['requests']:
            check_required_subfields(method, uri, request, "requests",
                                     ['method', 'uri'])
            op_id = request['id']
            op_uri = request['uri']
            op_method = request['method']
            # TODO: Support for op-specific 'req-headers' and 'resp-headers'
            if op_method == 'GET':
                try:
                    result = hmc.session.get(op_uri)
                except HTTPError_zhmc as exc:
                    op_uri_plain, op_query_parms = parse_query_parms(
                        op_method, op_uri)
                    result = {
                        'request-method': op_method,
                        'request-uri': op_uri_plain,
                        'request-headers': [],  # TODO: Implement
                        'request-authenticated-as': hmc.session.userid,
                        'http-status': exc.http_status,
                        'reason': exc.reason,
                        'message': exc.message,
                    }
                    if op_query_parms:
                        result['request-query-parms'] = op_query_parms
                    status = exc.http_status
                else:
                    status = 200
            elif op_method == 'POST':
                body = request.get('body', None)
                try:
                    result = hmc.session.post(op_uri, body=body)
                except HTTPError_zhmc as exc:
                    op_uri_plain, op_query_parms = parse_query_parms(
                        op_method, op_uri)
                    result = {
                        'request-method': op_method,
                        'request-uri': op_uri_plain,
                        'request-headers': [],  # TODO: Implement
                        'request-authenticated-as': hmc.session.userid,
                        'request-body': body,
                        'http-status': exc.http_status,
                        'reason': exc.reason,
                        'message': exc.message,
                    }
                    if op_query_parms:
                        result['request-query-parms'] = op_query_parms
                    status = exc.http_status
                else:
                    status = 200
            elif op_method == 'DELETE':
                try:
                    result = hmc.session.delete(op_uri)
                except HTTPError_zhmc as exc:
                    op_uri_plain, op_query_parms = parse_query_parms(
                        op_method, op_uri)

                    result = {
                        'request-method': op_method,
                        'request-uri': op_uri_plain,
                        'request-headers': [],  # TODO: Implement
                        'request-authenticated-as': hmc.session.userid,
                        'http-status': exc.http_status,
                        'reason': exc.reason,
                        'message': exc.message,
                    }
                    if op_query_parms:
                        result['request-query-parms'] = op_query_parms
                    status = exc.http_status
                else:
                    status = 200
            response = {
                # pylint: disable=possibly-used-before-assignment
                'status': status,
                'headers': [],  # TODO: Implement
            }
            response['body'] = result if result else None
            if op_id:
                response['id'] = op_id
            responses.append(response)
        return responses


# URIs to be handled
# Note: This list covers only the HMC operations implemented in the zhmcclient.
# The HMC supports several more operations.
URIS = (
    # (uri_regexp, handler_class)

    # In all modes:

    (r'/api/version', VersionHandler),

    (r'/api/sessions', SessionsHandler),
    (r'/api/sessions/this-session', ThisSessionHandler),

    (r'/api/console(?:\?(.*))?', ConsoleHandler),
    (r'/api/console/operations/restart', ConsoleRestartHandler),
    (r'/api/console/operations/shutdown', ConsoleShutdownHandler),
    (r'/api/console/operations/make-primary', ConsoleMakePrimaryHandler),
    # make-primary was removed in HMC 2.15.0
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
    (r'/api/console/operations/list-permitted-adapters(?:\?(.*))?',
     ConsoleListPermittedAdaptersHandler),

    (r'/api/console/users(?:\?(.*))?', UsersHandler),
    (r'/api/users/([^?/]+)(?:\?(.*))?', UserHandler),
    (r'/api/users/([^/]+)/operations/add-user-role',
     UserAddUserRoleHandler),
    (r'/api/users/([^/]+)/operations/remove-user-role',
     UserRemoveUserRoleHandler),

    (r'/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
    (r'/api/user-roles/([^?/]+)(?:\?(.*))?', UserRoleHandler),
    (r'/api/user-roles/([^/]+)/operations/add-permission',
     UserRoleAddPermissionHandler),
    (r'/api/user-roles/([^/]+)/operations/remove-permission',
     UserRoleRemovePermissionHandler),

    (r'/api/console/tasks(?:\?(.*))?', TasksHandler),
    (r'/api/console/tasks/([^?/]+)(?:\?(.*))?', TaskHandler),

    (r'/api/console/user-patterns(?:\?(.*))?', UserPatternsHandler),
    (r'/api/console/user-patterns/([^?/]+)(?:\?(.*))?', UserPatternHandler),

    (r'/api/console/password-rules(?:\?(.*))?', PasswordRulesHandler),
    (r'/api/console/password-rules/([^?/]+)(?:\?(.*))?', PasswordRuleHandler),

    (r'/api/console/ldap-server-definitions(?:\?(.*))?',
     LdapServerDefinitionsHandler),
    (r'/api/console/ldap-server-definitions/([^?/]+)(?:\?(.*))?',
     LdapServerDefinitionHandler),

    (r'/api/console/mfa-server-definitions(?:\?(.*))?',
     MfaServerDefinitionsHandler),
    (r'/api/console/mfa-server-definitions/([^?/]+)(?:\?(.*))?',
     MfaServerDefinitionHandler),

    (r'/api/cpcs(?:\?(.*))?', CpcsHandler),
    (r'/api/cpcs/([^?/]+)(?:\?(.*))?', CpcHandler),
    (r'/api/cpcs/([^/]+)/operations/set-cpc-power-save',
     CpcSetPowerSaveHandler),
    (r'/api/cpcs/([^/]+)/operations/set-cpc-power-capping',
     CpcSetPowerCappingHandler),
    (r'/api/cpcs/([^/]+)/energy-management-data',
     CpcGetEnergyManagementDataHandler),

    (r'/api/groups(?:\?(.*))?', GroupsHandler),
    (r'/api/groups/([^?/]+)(?:\?(.*))?', GroupHandler),
    (r'/api/groups/([^/]+)/operations/add-member', GroupAddMemberHandler),
    (r'/api/groups/([^/]+)/operations/remove-member', GroupRemoveMemberHandler),
    (r'/api/groups/([^/]+)/members', GroupMembersHandler),

    (r'/api/services/inventory', InventoryHandler),

    (r'/api/services/metrics/context', MetricsContextsHandler),
    (r'/api/services/metrics/context/([^/]+)', MetricsContextHandler),

    # Only in DPM mode:

    (r'/api/cpcs/([^/]+)/operations/start', CpcStartHandler),
    (r'/api/cpcs/([^/]+)/operations/stop', CpcStopHandler),
    (r'/api/cpcs/([^/]+)/operations/activate', CpcActivateHandler),
    (r'/api/cpcs/([^/]+)/operations/deactivate', CpcDeactivateHandler),
    (r'/api/cpcs/([^/]+)/operations/export-port-names-list',
     CpcExportPortNamesListHandler),

    (r'/api/cpcs/([^/]+)/adapters(?:\?(.*))?', AdaptersHandler),
    (r'/api/adapters/([^?/]+)(?:\?(.*))?', AdapterHandler),
    (r'/api/adapters/([^/]+)/operations/change-crypto-type',
     AdapterChangeCryptoTypeHandler),
    (r'/api/adapters/([^/]+)/operations/change-adapter-type',
     AdapterChangeAdapterTypeHandler),
    (r'/api/adapters/([^/]+)/operations/'
     r'get-partitions-assigned-to-adapter(?:\?(.*))?',
     AdapterGetAssignedPartitionsHandler),

    (r'/api/adapters/([^/]+)/network-ports/([^?/]+)(?:\?(.*))?',
     NetworkPortHandler),

    (r'/api/adapters/([^/]+)/storage-ports/([^?/]+)(?:\?(.*))?',
     StoragePortHandler),

    (r'/api/cpcs/([^/]+)/partitions(?:\?(.*))?', PartitionsHandler),
    (r'/api/partitions/([^?/]+)(?:\?(.*))?', PartitionHandler),
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
    (r'/api/partitions/([^/]+)/hbas/([^?/]+)(?:\?(.*))?', HbaHandler),
    (r'/api/partitions/([^/]+)/hbas/([^/]+)/operations/'
     'reassign-storage-adapter-port', HbaReassignPortHandler),

    (r'/api/partitions/([^/]+)/nics(?:\?(.*))?', NicsHandler),
    (r'/api/partitions/([^/]+)/nics/([^?/]+)(?:\?(.*))?', NicHandler),

    (r'/api/partitions/([^/]+)/virtual-functions(?:\?(.*))?',
     VirtualFunctionsHandler),
    (r'/api/partitions/([^/]+)/virtual-functions/([^?/]+)(?:\?(.*))?',
     VirtualFunctionHandler),

    (r'/api/cpcs/([^/]+)/virtual-switches(?:\?(.*))?', VirtualSwitchesHandler),
    (r'/api/virtual-switches/([^?/]+)(?:\?(.*))?', VirtualSwitchHandler),
    (r'/api/virtual-switches/([^/]+)/operations/get-connected-vnics',
     VirtualSwitchGetVnicsHandler),

    (r'/api/storage-groups(?:\?(.*))?', StorageGroupsHandler),
    (r'/api/storage-groups/([^?/]+)(?:\?(.*))?', StorageGroupHandler),
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

    (r'/api/storage-groups/([^/]+)/storage-volumes(?:\?(.*))?',
     StorageVolumesHandler),
    (r'/api/storage-groups/([^/]+)/storage-volumes/([^?/]+)(?:\?(.*))?',
     StorageVolumeHandler),

    (r'/api/storage-groups/([^/]+)/virtual-storage-resources(?:\?(.*))?',
     VirtualStorageResourcesHandler),
    (r'/api/storage-groups/([^/]+)/virtual-storage-resources/'
     r'([^?/]+)(?:\?(.*))?', VirtualStorageResourceHandler),

    (r'/api/storage-templates(?:\?(.*))?', StorageTemplatesHandler),
    (r'/api/storage-templates/([^?/]+)(?:\?(.*))?', StorageTemplateHandler),
    (r'/api/storage-templates/([^/]+)/operations/modify',
     StorageTemplateModifyHandler),

    (r'/api/storage-templates/([^/]+)/storage-template-volumes(?:\?(.*))?',
     StorageTemplateVolumesHandler),
    (r'/api/storage-templates/([^/]+)/storage-template-volumes/'
     r'([^?/]+)(?:\?(.*))?', StorageTemplateVolumeHandler),

    (r'/api/cpcs/([^/]+)/capacity-groups(?:\?(.*))?', CapacityGroupsHandler),
    (r'/api/cpcs/([^/]+)/capacity-groups/([^?/]+)(?:\?(.*))?',
     CapacityGroupHandler),
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

    (r'/api/cpcs/([^/]+)/operations/set-auto-start-list',
     CpcSetAutoStartListHandler),

    (r'/api/cpcs/([^/]+)/logical-partitions(?:\?(.*))?', LparsHandler),
    (r'/api/logical-partitions/([^?/]+)(?:\?(.*))?', LparHandler),
    (r'/api/logical-partitions/([^/]+)/operations/activate',
     LparActivateHandler),
    (r'/api/logical-partitions/([^/]+)/operations/deactivate',
     LparDeactivateHandler),
    (r'/api/logical-partitions/([^/]+)/operations/load', LparLoadHandler),
    (r'/api/logical-partitions/([^/]+)/operations/scsi-load',
     LparScsiLoadHandler),
    (r'/api/logical-partitions/([^/]+)/operations/scsi-dump',
     LparScsiDumpHandler),
    (r'/api/logical-partitions/([^/]+)/operations/nvme-load',
     LparNvmeLoadHandler),
    (r'/api/logical-partitions/([^/]+)/operations/nvme-dump',
     LparNvmeDumpHandler),
    # TODO: Add support for start
    # TODO: Add support for stop
    # TODO: Add support for psw-restart
    # TODO: Add support for reset-clear
    # TODO: Add support for reset-normal

    (r'/api/cpcs/([^/]+)/reset-activation-profiles(?:\?(.*))?',
     ResetActProfilesHandler),
    (r'/api/cpcs/([^/]+)/reset-activation-profiles/([^?/]+)(?:\?(.*))?',
     ResetActProfileHandler),

    (r'/api/cpcs/([^/]+)/image-activation-profiles(?:\?(.*))?',
     ImageActProfilesHandler),
    (r'/api/cpcs/([^/]+)/image-activation-profiles/([^?/]+)(?:\?(.*))?',
     ImageActProfileHandler),

    (r'/api/cpcs/([^/]+)/load-activation-profiles(?:\?(.*))?',
     LoadActProfilesHandler),
    (r'/api/cpcs/([^/]+)/load-activation-profiles/([^?/]+)(?:\?(.*))?',
     LoadActProfileHandler),

    (r'/api/services/aggregation/submit',
     SubmitRequestsHandler),

)
