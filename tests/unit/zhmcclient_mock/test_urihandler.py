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

# pylint: disable=attribute-defined-outside-init

"""
Unit tests for _urihandler module of the zhmcclient_mock package.
"""


from datetime import datetime
# TODO: Migrate mock to zhmcclient_mock
from unittest.mock import MagicMock
from dateutil import tz
import pytz
from requests.packages import urllib3
import pytest

from zhmcclient_mock._session import FakedSession
from zhmcclient_mock._hmc import FakedMetricObjectValues
from zhmcclient_mock._urihandler import HTTPError, InvalidResourceError, \
    InvalidMethodError, CpcNotInDpmError, CpcInDpmError, BadRequestError, \
    ConflictError, \
    parse_query_parms, UriHandler, \
    GenericGetPropertiesHandler, GenericUpdatePropertiesHandler, \
    GenericDeleteHandler, \
    VersionHandler, \
    ConsoleHandler, ConsoleRestartHandler, ConsoleShutdownHandler, \
    ConsoleMakePrimaryHandler, ConsoleReorderUserPatternsHandler, \
    ConsoleGetAuditLogHandler, ConsoleGetSecurityLogHandler, \
    ConsoleListUnmanagedCpcsHandler, \
    UsersHandler, UserHandler, UserAddUserRoleHandler, \
    UserRemoveUserRoleHandler, \
    UserRolesHandler, UserRoleHandler, UserRoleAddPermissionHandler, \
    UserRoleRemovePermissionHandler, \
    TasksHandler, TaskHandler, \
    UserPatternsHandler, UserPatternHandler, \
    PasswordRulesHandler, PasswordRuleHandler, \
    LdapServerDefinitionsHandler, LdapServerDefinitionHandler, \
    MfaServerDefinitionsHandler, MfaServerDefinitionHandler, \
    CpcsHandler, CpcHandler, CpcSetPowerSaveHandler, \
    CpcSetPowerCappingHandler, CpcGetEnergyManagementDataHandler, \
    CpcStartHandler, CpcStopHandler, \
    CpcActivateHandler, CpcDeactivateHandler, \
    CpcImportProfilesHandler, CpcExportProfilesHandler, \
    CpcExportPortNamesListHandler, CpcSetAutoStartListHandler, \
    MetricsContextsHandler, MetricsContextHandler, \
    PartitionsHandler, PartitionHandler, PartitionStartHandler, \
    PartitionStopHandler, PartitionScsiDumpHandler, \
    PartitionStartDumpProgramHandler, \
    PartitionPswRestartHandler, PartitionMountIsoImageHandler, \
    PartitionUnmountIsoImageHandler, PartitionIncreaseCryptoConfigHandler, \
    PartitionDecreaseCryptoConfigHandler, PartitionChangeCryptoConfigHandler, \
    HbasHandler, HbaHandler, HbaReassignPortHandler, \
    NicsHandler, NicHandler, \
    VirtualFunctionsHandler, VirtualFunctionHandler, \
    AdaptersHandler, AdapterHandler, AdapterChangeCryptoTypeHandler, \
    AdapterChangeAdapterTypeHandler, AdapterGetAssignedPartitionsHandler, \
    NetworkPortHandler, \
    StoragePortHandler, \
    VirtualSwitchesHandler, VirtualSwitchHandler, \
    VirtualSwitchGetVnicsHandler, \
    StorageGroupsHandler, StorageGroupHandler, \
    StorageVolumesHandler, StorageVolumeHandler, \
    VirtualStorageResourcesHandler, VirtualStorageResourceHandler, \
    StorageTemplatesHandler, StorageTemplateHandler, \
    StorageTemplateVolumesHandler, StorageTemplateVolumeHandler, \
    CapacityGroupsHandler, CapacityGroupHandler, \
    CapacityGroupAddPartitionHandler, CapacityGroupRemovePartitionHandler, \
    LparsHandler, LparHandler, LparActivateHandler, LparDeactivateHandler, \
    LparLoadHandler, LparScsiLoadHandler, LparScsiDumpHandler, \
    LparNvmeLoadHandler, LparNvmeDumpHandler, \
    ResetActProfilesHandler, ResetActProfileHandler, \
    ImageActProfilesHandler, ImageActProfileHandler, \
    LoadActProfilesHandler, LoadActProfileHandler, \
    SubmitRequestsHandler
# pylint: disable=redefined-builtin
from zhmcclient_mock._urihandler import ConnectionError

urllib3.disable_warnings()


def test_httperror_attrs():
    """
    Test HTTPError initialization and attributes.
    """
    method = 'GET'
    uri = '/api/cpcs'
    http_status = 500
    reason = 42
    message = "fake message"

    exc = HTTPError(method, uri, http_status, reason, message)

    assert exc.method == method
    assert exc.uri == uri
    assert exc.http_status == http_status
    assert exc.reason == reason
    assert exc.message == message


def test_httperror_response():
    """
    Test HTTPError.response().
    """
    method = 'GET'
    uri = '/api/cpcs'
    http_status = 500
    reason = 42
    message = "fake message"
    expected_response = {
        'request-method': method,
        'request-uri': uri,
        'http-status': http_status,
        'reason': reason,
        'message': message,
    }
    exc = HTTPError(method, uri, http_status, reason, message)

    response = exc.response()

    assert response == expected_response


def test_connectionerror_attrs():
    """
    Test ConnectionError initialization and attributes.
    """
    msg = "fake error message"

    exc = ConnectionError(msg)

    assert exc.message == msg


class DummyHandler1:
    # pylint: disable=too-few-public-methods
    """
    Dummy URI handler class.
    """
    pass


class DummyHandler2:
    # pylint: disable=too-few-public-methods
    """
    Dummy URI handler class.
    """
    pass


class DummyHandler3:
    # pylint: disable=too-few-public-methods
    """
    Dummy URI handler class.
    """
    pass


def test_invreserr_attrs_with_handler():
    """
    Test InvalidResourceError initialization and attributes, with a dummy
    handler.
    """
    method = 'GET'
    uri = '/api/cpcs'
    exp_http_status = 404
    exp_reason = 1

    exc = InvalidResourceError(method, uri, DummyHandler1)

    assert exc.method == method
    assert exc.uri == uri
    assert exc.http_status == exp_http_status
    assert exc.reason == exp_reason
    assert uri in exc.message

    # next test case
    exp_reason = 2

    exc = InvalidResourceError(method, uri, DummyHandler1,
                               reason=exp_reason)

    assert exc.reason == exp_reason

    # next test case
    exp_resource_uri = '/api/resource'

    exc = InvalidResourceError(method, uri, DummyHandler1,
                               resource_uri=exp_resource_uri)

    assert exp_resource_uri in exc.message


def test_invreserr_attrs_no_handler():
    """
    Test InvalidResourceError initialization and attributes, without a
    handler.
    """
    method = 'GET'
    uri = '/api/cpcs'
    exp_http_status = 404
    exp_reason = 1

    exc = InvalidResourceError(method, uri, None)

    assert exc.method == method
    assert exc.uri == uri
    assert exc.http_status == exp_http_status
    assert exc.reason == exp_reason


def test_invmetherr_attrs_with_handler():
    """
    Test InvalidMethodError initialization and attributes, with a dummy
    handler.
    """
    method = 'DELETE'
    uri = '/api/cpcs'
    exp_http_status = 404
    exp_reason = 1

    exc = InvalidMethodError(method, uri, DummyHandler1)

    assert exc.method == method
    assert exc.uri == uri
    assert exc.http_status == exp_http_status
    assert exc.reason == exp_reason


def test_invmetherr_attrs_no_handler():
    """
    Test InvalidMethodError initialization and attributes, without a
    handler.
    """
    method = 'DELETE'
    uri = '/api/cpcs'
    exp_http_status = 404
    exp_reason = 1

    exc = InvalidMethodError(method, uri, None)

    assert exc.method == method
    assert exc.uri == uri
    assert exc.http_status == exp_http_status
    assert exc.reason == exp_reason


def test_cpcnotindpmerror_attrs():
    """
    Test CpcNotInDpmError attributes.
    """

    # Set up a faked Cpc for use in exception
    session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
    hmc = session.hmc
    cpc1 = hmc.cpcs.add({'name': 'cpc1'})

    method = 'GET'
    uri = '/api/cpcs/1/partitions'
    exp_http_status = 409
    exp_reason = 5

    exc = CpcNotInDpmError(method, uri, cpc1)

    assert exc.method == method
    assert exc.uri == uri
    assert exc.http_status == exp_http_status
    assert exc.reason == exp_reason


def test_cpcindpmerror_attrs():
    """
    Test CpcInDpmError attributes.
    """

    # Set up a faked Cpc for use in exception
    session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
    hmc = session.hmc
    cpc1 = hmc.cpcs.add({'name': 'cpc1'})

    method = 'GET'
    uri = '/api/cpcs/1/logical-partitions'
    exp_http_status = 409
    exp_reason = 4

    exc = CpcInDpmError(method, uri, cpc1)

    assert exc.method == method
    assert exc.uri == uri
    assert exc.http_status == exp_http_status
    assert exc.reason == exp_reason


TESTCASES_PARSE_QUERY_PARMS = [
    # Testcases for parse_query_parms()

    # Each testcase is a tuple of:
    # * desc: testcase description
    # * uri: URI with query parameter to be parsed
    # * exp_result: expected return value, or expected exception object

    (
        "URI without query parms",
        'fake-uri',
        ('fake-uri', {})
    ),
    (
        "URI without query parms but with ?",
        'fake-uri?',
        ('fake-uri', {})
    ),
    (
        "a normal parameter",
        'fake-uri?a=b',
        ('fake-uri', {'a': 'b'})
    ),
    (
        "two normal parameters",
        'fake-uri?a=b&c=d',
        ('fake-uri', {'a': 'b', 'c': 'd'})
    ),
    (
        "trailing ampersand",
        'fake-uri?a=b&',
        ('fake-uri', {'a': 'b'})
    ),
    (
        "leading ampersand",
        'fake-uri?&a=b',
        ('fake-uri', {'a': 'b'})
    ),
    (
        "parameter with missing value",
        'fake-uri?a=',
        ('fake-uri', {'a': ''})
    ),
    (
        "parameter with missing name",
        'fake-uri?=b',
        ('fake-uri', {'': 'b'})
    ),
    (
        "two occurrences of same parameter",
        'fake-uri?a=b&a=c',
        ('fake-uri', {'a': ['b', 'c']})
    ),
    (
        "two occurrences of same parameter and another in between",
        'fake-uri?a=b&d=e&a=c',
        ('fake-uri', {'a': ['b', 'c'], 'd': 'e'})
    ),
    (
        "parameter value with percent-escaped space in middle",
        'fake-uri?a=b%20c',
        ('fake-uri', {'a': 'b c'})
    ),
    (
        "parameter value with percent-escaped space at begin",
        'fake-uri?a=%20c',
        ('fake-uri', {'a': ' c'})
    ),
    (
        "parameter value with percent-escaped space at end",
        'fake-uri?a=b%20',
        ('fake-uri', {'a': 'b '})
    ),
    (
        "parameter value that is a percent-escaped space",
        'fake-uri?a=%20',
        ('fake-uri', {'a': ' '})
    ),
    (
        "parameter name with percent-escaped space in middle",
        'fake-uri?a%20b=c',
        ('fake-uri', {'a b': 'c'})
    ),
    (
        "parameter name with percent-escaped space at begin",
        'fake-uri?%20b=c',
        ('fake-uri', {' b': 'c'})
    ),
    (
        "parameter name with percent-escaped space at end",
        'fake-uri?a%20=c',
        ('fake-uri', {'a ': 'c'})
    ),
    (
        "parameter name that is a percent-escaped space",
        'fake-uri?%20=c',
        ('fake-uri', {' ': 'c'})
    ),
    (
        "two equal signs (invalid format)",
        'fake-uri?a==b',
        HTTPError('fake-meth', 'fake-uri', 400, 1, "invalid format")
    ),
    (
        "two assignments (invalid format)",
        'fake-uri?a=b=c',
        HTTPError('fake-meth', 'fake-uri', 400, 1, "invalid format")
    ),
    (
        "missing assignment (invalid format)",
        'fake-uri?a',
        HTTPError('fake-meth', 'fake-uri', 400, 1, "invalid format")
    ),
]


@pytest.mark.parametrize(
    "desc, uri, exp_result",
    TESTCASES_PARSE_QUERY_PARMS
)
def test_parse_query_parms(desc, uri, exp_result):
    # pylint: disable=unused-argument
    """
    Test function for parse_query_parms().
    """

    if isinstance(exp_result, Exception):

        with pytest.raises(type(exp_result)) as exc_info:

            # The code to be tested
            parse_query_parms('fake-meth', uri)

        if isinstance(exp_result, HTTPError):
            exc = exc_info.value
            assert exc.http_status == 400
            assert exc.reason == 1

    else:

        # The code to be tested
        filter_args = parse_query_parms('fake-meth', uri)

        assert filter_args == exp_result


def test_urihandler_empty_1():
    """
    Test UriHandler.handler() with empty URIs on normal URI
    """
    uris = ()
    urihandler = UriHandler(uris)
    with pytest.raises(InvalidResourceError):
        urihandler.handler('/api/cpcs', 'GET')


def test_urihandler_empty_2():
    """
    Test UriHandler.handler() with empty URIs on empty URI
    """
    uris = ()
    urihandler = UriHandler(uris)
    with pytest.raises(InvalidResourceError):
        urihandler.handler('', 'GET')


def uri_handler_cpcs_dummy():
    """
    Returns a URI handler for CPCs, using the dummy handlers.
    """
    uris = (
        (r'/api/cpcs', DummyHandler1),
        (r'/api/cpcs/([^/]+)', DummyHandler2),
        (r'/api/cpcs/([^/]+)/child', DummyHandler3),
    )
    return UriHandler(uris)


TESTCASES_URIHANDLER_HANDLE_CPCS = [
    # Testcases for UriHandler.handler() for CPCS

    # Each testcase is a tuple of:
    # * desc: description
    # * uri: uri argument for handler()
    # * method: method argument for handler()
    # * exc_exp: Expected exception object, or None
    # * exp_handler_class: expected handler class, or None
    # * exp_uri_parms: expected tuple of URI parms, or None

    (
        "ok1",
        '/api/cpcs', 'GET',
        None, DummyHandler1, ()
    ),
    (
        "ok2",
        '/api/cpcs/fake-id1', 'GET',
        None, DummyHandler2, ('fake-id1',)
    ),
    (
        "ok3",
        '/api/cpcs/fake-id1/child', 'GET',
        None, DummyHandler3, ('fake-id1',)
    ),
    (
        "missing leading slash",
        'api/cpcs', 'GET',
        InvalidResourceError, None, None
    ),
    (
        "extra leading segment without slash",
        'x/api/cpcs', 'GET',
        InvalidResourceError, None, None
    ),
    (
        "last segment misses a character",
        '/api/cpc', 'GET',
        InvalidResourceError, None, None
    ),
    (
        "invalid last segment",
        '/api/cpcs_x', 'GET',
        InvalidResourceError, None, None
    ),
    (
        "trailing slash after last segment",
        '/api/cpcs/', 'GET',
        InvalidResourceError, None, None
    ),
    (
        "last segment #2 with trailing slash",
        '/api/cpcs/fake-id1/', 'GET',
        InvalidResourceError, None, None
    ),
    (
        "last segment #2 misses a character",
        '/api/cpcs/fake-id1/chil', 'GET',
        InvalidResourceError, None, None
    ),
    (
        "invalid last segment #2",
        '/api/cpcs/fake-id1/child_x', 'GET',
        InvalidResourceError, None, None
    ),
]


@pytest.mark.parametrize(
    "desc, uri, method, exc_exp, exp_handler_class, exp_uri_parms",
    TESTCASES_URIHANDLER_HANDLE_CPCS
)
def test_urihandler_handle_cpcs(
        desc, uri, method, exc_exp, exp_handler_class, exp_uri_parms):
    # pylint: disable=unused-argument
    """
    Test function for UriHandler.handler() for CPCs.
    """

    if exc_exp is None:

        urihandler = uri_handler_cpcs_dummy()

        # The code to be tested
        handler_class, uri_parms = urihandler.handler(uri, method)

        assert handler_class == exp_handler_class
        assert uri_parms == exp_uri_parms

    else:

        urihandler = uri_handler_cpcs_dummy()

        with pytest.raises(exc_exp):

            # The code to be tested
            urihandler.handler(uri, method)


class TestUriHandlerMethod:
    """
    All tests for get(), post(), delete() methods of class UriHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with mocked URI handlers for /api/cpcs, with two
        CPCs. Performs mock setup on the handler classes.
        """
        self.uris = (
            (r'/api/cpcs', DummyHandler1),
            (r'/api/cpcs/([^/]+)', DummyHandler2),
        )
        self.cpc1 = {
            'object-id': '1',
            'object-uri': '/api/cpcs/1',
            'name': 'cpc1',
        }
        self.cpc2 = {
            'object-id': '2',
            'object-uri': '/api/cpcs/2',
            'name': 'cpc2',
        }
        self.new_cpc = {
            'object-id': '3',
            'object-uri': '/api/cpcs/3',
            'name': 'cpc3',
        }
        self.cpcs = {
            'cpcs': [self.cpc1, self.cpc2]
        }
        DummyHandler1.get = staticmethod(MagicMock(
            return_value=self.cpcs))
        DummyHandler1.post = staticmethod(MagicMock(
            return_value=self.new_cpc))
        DummyHandler2.get = staticmethod(MagicMock(
            return_value=self.cpc1))
        DummyHandler2.delete = staticmethod(MagicMock(
            return_value=None))
        self.urihandler = UriHandler(self.uris)
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc

    def teardown_method(self):
        # pylint: disable=no-self-use
        """
        Called by pytest after each test method.

        Tears down the mock setup on the handler classes.
        """
        delattr(DummyHandler1, 'get')
        delattr(DummyHandler1, 'post')
        delattr(DummyHandler2, 'get')
        delattr(DummyHandler2, 'delete')

    def test_urihandler_list(self):
        """
        Test GET method of URI handler on resource set (list), using CPCs.
        """

        # the function to be tested
        result = self.urihandler.get(self.hmc, '/api/cpcs', True)

        assert result == self.cpcs

        DummyHandler1.get.assert_called_with(
            'GET', self.hmc, '/api/cpcs', tuple(), True)
        assert DummyHandler1.post.called == 0
        assert DummyHandler2.get.called == 0
        assert DummyHandler2.delete.called == 0

    def test_urihandler_get(self):
        """
        Test GET method of URI handler on single resource, using a CPC.
        """

        # the function to be tested
        result = self.urihandler.get(self.hmc, '/api/cpcs/1', True)

        assert result == self.cpc1

        assert DummyHandler1.get.called == 0
        assert DummyHandler1.post.called == 0
        DummyHandler2.get.assert_called_with(
            'GET', self.hmc, '/api/cpcs/1', tuple('1'), True)
        assert DummyHandler2.delete.called == 0

    def test_urihandler_create(self):
        """
        Test POST method of URI handler on resource set (create), creating a
        CPC.
        """

        # the function to be tested
        result = self.urihandler.post(self.hmc, '/api/cpcs', {}, True, True)

        assert result == self.new_cpc

        assert DummyHandler1.get.called == 0
        DummyHandler1.post.assert_called_with(
            'POST', self.hmc, '/api/cpcs', tuple(), {}, True, True)
        assert DummyHandler2.get.called == 0
        assert DummyHandler2.delete.called == 0

    def test_urihandler_delete(self):
        """
        Test DELETE method of URI handler on a resource, deleting a CPC.
        """

        # the function to be tested
        self.urihandler.delete(self.hmc, '/api/cpcs/2', True)

        assert DummyHandler1.get.called == 0
        assert DummyHandler1.post.called == 0
        assert DummyHandler2.get.called == 0
        DummyHandler2.delete.assert_called_with(
            'DELETE', self.hmc, '/api/cpcs/2', tuple('2'), True)


def standard_test_hmc():
    """
    Return a FakedHmc object that is prepared with a few standard resources
    for testing.
    """

    hmc_resources = {
        'consoles': [
            {
                'properties': {
                    'name': 'fake_console_name',
                },
                'users': [
                    {
                        'properties': {
                            'object-id': 'fake-user-oid-1',
                            'name': 'fake_user_name_1',
                            'description': 'User #1',
                            'type': 'system-defined',
                        },
                    },
                ],
                'user_roles': [
                    {
                        'properties': {
                            'object-id': 'fake-user-role-oid-1',
                            'name': 'fake_user_role_name_1',
                            'description': 'User Role #1',
                            'type': 'system-defined',
                        },
                    },
                    {
                        # default system-defined user role
                        'properties': {
                            'object-id': 'fake-hmc-operator-tasks',
                            'name': 'hmc-operator-tasks',
                            'description': 'Operator Tasks',
                            'type': 'system-defined',
                        },
                    },
                ],
                'user_patterns': [
                    {
                        'properties': {
                            'element-id': 'fake-user-pattern-oid-1',
                            'name': 'fake_user_pattern_name_1',
                            'description': 'User Pattern #1',
                            'pattern': 'fake_user_name_*',
                            'type': 'glob-like',
                            'retention-time': 0,
                            'specific-template-uri':
                            '/api/users/fake-user-oid-1',
                        },
                    },
                ],
                'password_rules': [
                    {
                        'properties': {
                            'element-id': 'fake-password-rule-oid-1',
                            'name': 'fake_password_rule_name_1',
                            'description': 'Password Rule #1',
                            'type': 'system-defined',
                        },
                    },
                ],
                'tasks': [
                    {
                        'properties': {
                            'element-id': 'fake-task-oid-1',
                            'name': 'fake_task_name_1',
                            'description': 'Task #1',
                        },
                    },
                    {
                        'properties': {
                            'element-id': 'fake-task-oid-2',
                            'name': 'fake_task_name_2',
                            'description': 'Task #2',
                        },
                    },
                ],
                'ldap_server_definitions': [
                    {
                        'properties': {
                            'element-id': 'fake-ldap-srv-def-oid-1',
                            'name': 'fake_ldap_srv_def_name_1',
                            'description': 'LDAP Srv Def #1',
                            'primary-hostname-ipaddr': '10.11.12.13',
                        },
                    },
                ],
                'mfa_server_definitions': [
                    {
                        'properties': {
                            'element-id': 'fake-mfa-srv-def-oid-1',
                            'name': 'fake_mfa_srv_def_name_1',
                            'description': 'MFA Srv Def #1',
                            'hostname-ipaddr': '10.11.12.13',
                        },
                    },
                ],
                'storage_groups': [
                    {
                        'properties': {
                            'object-id': 'fake-stogrp-oid-1',
                            'name': 'fake_stogrp_name_1',
                            'description': 'Storage Group #1',
                            'cpc-uri': '/api/cpcs/2',
                            'type': 'fcp',
                            'shared': False,
                            'fulfillment-state': 'complete',
                            'candidate-adapter-port-uris': [
                                '/api/cpcs/2/adapters/2',
                            ],
                            # 'storage-volume-uris' managed automatically
                            # 'virtual-storage-resource-uris' managed autom.
                        },
                        'storage_volumes': [
                            {
                                'properties': {
                                    'element-id': 'fake-stovol-oid-1',
                                    'name': 'fake_stovol_name_1',
                                    'description': 'Storage Volume #1',
                                    'fulfillment-state': 'complete',
                                    'size': 10.0,
                                    'usage': 'boot',
                                },
                            },
                        ],
                        'virtual_storage_resources': [
                            {
                                'properties': {
                                    'element-id': 'fake-vsr-oid-1',
                                    'name': 'fake_vsr_name_1',
                                    'description':
                                    'Virtual Storage Resource #1',
                                    'device-number': '1300',
                                    'partition-uri': None,
                                    'adapter-port-uri': None,
                                },
                            },
                        ],
                    },
                ],
                'storage_group_templates': [
                    {
                        'properties': {
                            'object-id': 'fake-stotpl-oid-1',
                            'name': 'fake_stotpl_name_1',
                            'description': 'Storage Group Template #1',
                            'cpc-uri': '/api/cpcs/2',
                            'type': 'fcp',
                            'shared': False,
                            # 'storage-template-volume-uris' managed automatic.
                        },
                        'storage_volume_templates': [
                            {
                                'properties': {
                                    'element-id': 'fake-stotvl-oid-1',
                                    'name': 'fake_stotvl_name_1',
                                    'description': 'Storage Volume Template #1',
                                    'size': 10.0,
                                    'usage': 'boot',
                                },
                            },
                        ],
                    },
                ],
            }
        ],
        'cpcs': [
            {
                'properties': {
                    'object-id': '1',
                    'name': 'cpc_1',
                    'dpm-enabled': False,
                    'description': 'CPC #1 (classic mode)',
                    'status': 'operating',
                    'has-unacceptable-status': False,
                    'se-version': '2.15.0',
                },
                'lpars': [
                    {
                        'properties': {
                            'object-id': '1',
                            'name': 'lpar_1',
                            'description': 'LPAR #1 in CPC #1',
                            'status': 'not-activated',
                        },
                    },
                ],
                'reset_activation_profiles': [
                    {
                        'properties': {
                            'name': 'r1',
                            'description': 'Reset profile #1 in CPC #1',
                        },
                    },
                ],
                'image_activation_profiles': [
                    {
                        'properties': {
                            'name': 'i1',
                            'description': 'Image profile #1 in CPC #1',
                        },
                    },
                ],
                'load_activation_profiles': [
                    {
                        'properties': {
                            'name': 'L1',
                            'description': 'Load profile #1 in CPC #1',
                        },
                    },
                ],
            },
            {
                'properties': {
                    'object-id': '2',
                    'name': 'cpc_2',
                    'dpm-enabled': True,
                    'description': 'CPC #2 (DPM mode)',
                    'status': 'active',
                    'has-unacceptable-status': False,
                    'se-version': '2.16.0',
                },
                'partitions': [
                    {
                        'properties': {
                            'object-id': '1',
                            'name': 'partition_1',
                            'type': 'linux',
                            'description': 'Partition #1 in CPC #2',
                            'status': 'stopped',
                            'hba-uris': [],   # updated automatically
                            'nic-uris': [],   # updated automatically
                            'virtual-function-uris': [],   # updated autom.
                            'crypto-configuration': {
                                'crypto-adapter-uris': ['/api/adapters/4'],
                                'crypto-domain-configurations': [
                                    {
                                        'domain-index': 0,
                                        'access-mode': 'control-usage',
                                    },
                                ],
                            },
                        },
                        'hbas': [
                            {
                                'properties': {
                                    'element-id': '1',
                                    'name': 'hba_1',
                                    'description': 'HBA #1 in Partition #1',
                                    'adapter-port-uri':
                                        '/api/adapters/2/storage-ports/1',
                                    'wwpn': 'CFFEAFFE00008001',
                                    'device-number': '1001',
                                },
                            },
                        ],
                        'nics': [
                            {
                                'properties': {
                                    'element-id': '1',
                                    'name': 'nic_1',
                                    'description': 'NIC #1 in Partition #1',
                                    'type': 'roce',
                                    'network-adapter-port-uri':
                                        '/api/adapters/3/network-ports/1',
                                    'device-number': '2001',
                                },
                            },
                        ],
                        'virtual_functions': [
                            {
                                'properties': {
                                    'element-id': '1',
                                    'name': 'vf_1',
                                    'description': 'VF #1 in Partition #1',
                                    'device-number': '3001',
                                    'adapter-uri': '/api/adapters/5',
                                },
                            },
                        ],
                    },
                ],
                'adapters': [
                    {
                        'properties': {
                            'object-id': '1',
                            'name': 'osa_1',
                            'description': 'OSA #1 in CPC #2',
                            'adapter-family': 'osa',
                            'network-port-uris': [],   # updated automatically
                            'status': 'active',
                            'adapter-id': 'BEF',
                            'type': 'osd',
                        },
                        'ports': [
                            {
                                'properties': {
                                    'element-id': '1',
                                    'name': 'osa_1_port_1',
                                    'description': 'Port #1 of OSA #1',
                                },
                            },
                        ],
                    },
                    {
                        'properties': {
                            'object-id': '2',
                            'name': 'fcp_2',
                            'description': 'FCP #2 in CPC #2',
                            'adapter-family': 'ficon',
                            'storage-port-uris': [],   # updated automatically
                            'adapter-id': 'CEF',
                            'type': 'fcp',
                        },
                        'ports': [
                            {
                                'properties': {
                                    'element-id': '1',
                                    'name': 'fcp_2_port_1',
                                    'description': 'Port #1 of FCP #2',
                                },
                            },
                        ],
                    },
                    {
                        'properties': {
                            'object-id': '2a',
                            'name': 'fcp_2a',
                            'description': 'FCP #2a in CPC #2',
                            'adapter-family': 'ficon',
                            'storage-port-uris': [],   # updated automatically
                            'adapter-id': 'CEE',
                            'type': 'fcp',
                        },
                        'ports': [
                            {
                                'properties': {
                                    'element-id': '1',
                                    'name': 'fcp_2a_port_1',
                                    'description': 'Port #1 of FCP #2a',
                                },
                            },
                        ],
                    },
                    {
                        'properties': {
                            'object-id': '3',
                            'name': 'roce_3',
                            'description': 'ROCE #3 in CPC #2',
                            'adapter-family': 'roce',
                            'network-port-uris': [],   # updated automatically
                            'adapter-id': 'DEF',
                            'type': 'roce',
                        },
                        'ports': [
                            {
                                'properties': {
                                    'element-id': '1',
                                    'name': 'roce_3_port_1',
                                    'description': 'Port #1 of ROCE #3',
                                },
                            },
                        ],
                    },
                    {
                        'properties': {
                            'object-id': '4',
                            'name': 'crypto_4',
                            'description': 'Crypto #4 in CPC #2',
                            'adapter-family': 'crypto',
                            'adapter-id': 'EEF',
                            'type': 'crypto',
                            'detected-card-type': 'crypto-express-5s',
                            'crypto-number': 7,
                            'crypto-type': 'accelerator',
                        },
                    },
                    {
                        'properties': {
                            'object-id': '5',
                            'name': 'zedc_5',
                            'description': 'zEDC compression #5 in CPC #2',
                            'adapter-family': 'accelerator',
                            'adapter-id': 'FEF',
                            'type': 'zedc',
                            'detected-card-type': 'zedc-express',
                        },
                    },
                ],
                'virtual_switches': [
                    {
                        'properties': {
                            'object-id': '1',
                            'name': 'vswitch_osa_1',
                            'description': 'Vswitch for OSA #1 in CPC #2',
                            'type': 'osd',
                        },
                    },
                ],
                'capacity_groups': [
                    {
                        'properties': {
                            'element-id': '1',
                            'name': 'capacity_group1',
                            'description': 'Capacity Group #1',
                        },
                    },
                ],
            },
        ],
    }
    session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
    hmc = session.hmc
    hmc.add_resources(hmc_resources)
    return hmc, hmc_resources


class TestGenericGetPropertiesHandler:
    """
    All tests for class GenericGetPropertiesHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with generic get
        URI handler for a resource (CPC).
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)', GenericGetPropertiesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_generic_get(self):
        """
        Test GET on resource with GenericGetPropertiesHandler.
        """

        # the function to be tested:
        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)

        exp_cpc1 = {
            'object-id': '1',
            'object-uri': '/api/cpcs/1',
            'class': 'cpc',
            'parent': None,
            'name': 'cpc_1',
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'description': 'CPC #1 (classic mode)',
            'status': 'operating',
            'has-unacceptable-status': False,
            'se-version': '2.15.0',
        }
        assert cpc1 == exp_cpc1

    def test_generic_get_err_disconn(self):
        """
        Test GET with disconnected HMC.
        """

        self.hmc.disable()

        with pytest.raises(ConnectionError):
            # the function to be tested:
            self.urihandler.get(self.hmc, '/api/cpcs/1', True)


class _GenericGetUpdatePropertiesHandler(GenericGetPropertiesHandler,
                                         GenericUpdatePropertiesHandler):
    """
    Combines get and update handlers.
    """
    pass


class TestGenericUpdatePropertiesHandler:
    """
    All tests for class GenericUpdatePropertiesHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with generic get/update
        URI handler for a resource (CPC).
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)', _GenericGetUpdatePropertiesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_generic_update_verify(self):
        """
        Test POST CPC (update CPC).
        """

        update_cpc1 = {
            'description': 'CPC #1 (updated)',
        }

        # the function to be tested:
        resp = self.urihandler.post(self.hmc, '/api/cpcs/1', update_cpc1, True,
                                    True)

        assert resp is None
        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['description'] == 'CPC #1 (updated)'

    def test_generic_post_err_disconn(self):
        """
        Test POST with disconnected HMC.
        """

        self.hmc.disable()

        update_cpc1 = {
            'description': 'CPC #1 (updated)',
        }

        with pytest.raises(ConnectionError):
            # the function to be tested:
            self.urihandler.post(self.hmc, '/api/cpcs/1', update_cpc1, True,
                                 True)


class TestGenericDeleteHandler:
    """
    All tests for class GenericDeleteHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with generic delete
        URI handler for a resource (LDAP Server Definitions).
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/console/ldap-server-definitions/([^/]+)',
             GenericDeleteHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_generic_delete_verify(self):
        """
        Test DELETE with generic delete handler.
        """

        uri = '/api/console/ldap-server-definitions/fake-ldap-srv-def-oid-1'

        # the function to be tested:
        # pylint: disable=assignment-from-no-return
        ret = self.urihandler.delete(self.hmc, uri, True)

        assert ret is None

        # Verify it no longer exists:
        with pytest.raises(KeyError):
            self.hmc.lookup_by_uri(uri)

    def test_generic_delete_err_disconn(self):
        """
        Test DELETE with disconnected HMC.
        """

        self.hmc.disable()

        uri = '/api/console/ldap-server-definitions/fake-ldap-srv-def-oid-1'

        with pytest.raises(ConnectionError):
            # the function to be tested:
            self.urihandler.delete(self.hmc, uri, True)


class TestVersionHandler:
    """
    All tests for class VersionHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with VersionHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/version', VersionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_get_version(self):
        """
        Test GET version.
        """

        # the function to be tested:
        resp = self.urihandler.get(self.hmc, '/api/version', True)

        api_major, api_minor = self.hmc.api_version.split('.')
        exp_resp = {
            'hmc-name': self.hmc.hmc_name,
            'hmc-version': self.hmc.hmc_version,
            'api-major-version': int(api_major),
            'api-minor-version': int(api_minor),
        }
        assert resp == exp_resp


class TestConsoleHandler:
    """
    All tests for class ConsoleHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with ConsoleHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/console', ConsoleHandler),
        )
        self.urihandler = UriHandler(self.uris)

    # Note: There is no test_list() function because there is no List
    # operation for Console resources.

    def test_cons_get(self):
        """
        Test GET console.
        """

        # the function to be tested:
        console = self.urihandler.get(self.hmc, '/api/console', True)

        exp_console = {
            'object-uri': '/api/console',
            'name': 'fake_console_name',
            'class': 'console',
            'parent': None,
        }
        assert console == exp_console


class TestConsoleRestartHandler:
    """
    All tests for class ConsoleRestartHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        ConsoleRestartHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/console', ConsoleHandler),
            (r'/api/console/operations/restart', ConsoleRestartHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cons_restart(self):
        """
        Test POST console restart.
        """

        body = {
            'force': False,
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/operations/restart', body, True, True)

        assert self.hmc.enabled
        assert resp is None

    def test_cons_restart_err_no_console(self):
        """
        Test POST console restart when console does not exist in the faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        body = {
            'force': False,
        }
        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(
                self.hmc, '/api/console/operations/restart', body, True, True)

        exc = exc_info.value
        assert exc.reason == 1


class TestConsoleShutdownHandler:
    """
    All tests for class ConsoleShutdownHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        ConsoleShutdownHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/console', ConsoleHandler),
            (r'/api/console/operations/shutdown', ConsoleShutdownHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cons_shutdown(self):
        """
        Test POST console shutdown.
        """

        body = {
            'force': False,
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/operations/shutdown', body, True, True)

        assert not self.hmc.enabled
        assert resp is None

    def test_cons_shutdown_err_no_console(self):
        """
        Test POST console shutdown when console does not exist in the faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        body = {
            'force': False,
        }
        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(
                self.hmc, '/api/console/operations/shutdown', body, True, True)

        exc = exc_info.value
        assert exc.reason == 1


class TestConsoleMakePrimaryHandler:
    """
    All tests for class ConsoleMakePrimaryHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        ConsoleMakePrimaryHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/console', ConsoleHandler),
            (r'/api/console/operations/make-primary',
             ConsoleMakePrimaryHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cons_makeprim(self):
        """
        Test POST console make primary.
        """

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/operations/make-primary', None, True, True)

        assert self.hmc.enabled
        assert resp is None

    def test_cons_makeprim_err_no_console(self):
        """
        Test POST console make primary when console does not exist in the
        faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        body = {
            'force': False,
        }
        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(
                self.hmc, '/api/console/operations/make-primary', body, True,
                True)

        exc = exc_info.value
        assert exc.reason == 1


class TestConsoleReorderUserPatternsHandler:
    """
    All tests for class ConsoleReorderUserPatternsHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        ConsoleReorderUserPatternsHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()

        # Remove the standard User Pattern objects for this test
        console = self.hmc.lookup_by_uri('/api/console')
        user_pattern_objs = console.user_patterns.list()
        for obj in user_pattern_objs:
            console.user_patterns.remove(obj.oid)

        self.uris = (
            (r'/api/console', ConsoleHandler),
            (r'/api/console/user-patterns(?:\?(.*))?', UserPatternsHandler),
            (r'/api/console/user-patterns/([^/]+)', UserPatternHandler),
            (r'/api/console/operations/reorder-user-patterns',
             ConsoleReorderUserPatternsHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cons_reorderupat_all(self):
        """
        Test POST reorder user patterns.
        """

        testcases = [
            # (initial_order, new_order)
            (['a', 'b'], ['a', 'b']),
            (['a', 'b'], ['b', 'a']),
            (['a', 'b', 'c'], ['a', 'c', 'b']),
            (['a', 'b', 'c'], ['c', 'b', 'a']),
        ]
        for initial_order, new_order in testcases:
            self._test_cons_reorderupat_one(initial_order, new_order)

    def _test_cons_reorderupat_one(self, initial_order, new_order):
        """
        Internal helper function that tests POST reorder user patterns for one
        user.
        """

        # Create User Pattern objects in the initial order and build
        # name-to-URI mapping
        uri_by_name = {}
        for name in initial_order:
            user_pattern = {
                'element-id': name + '-oid',
                'name': name,
                'pattern': name + '*',
                'type': 'glob-like',
                'retention-time': 0,
                'specific-template-uri': 'fake-uri',
            }
            resp = self.urihandler.post(self.hmc, '/api/console/user-patterns',
                                        user_pattern, True, True)
            uri = resp['element-uri']
            uri_by_name[name] = uri

        new_uris = [uri_by_name[name] for name in new_order]

        body = {
            'user-pattern-uris': new_uris
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/operations/reorder-user-patterns', body,
            True, True)

        # Retrieve the actual order of User Pattern objects
        resp = self.urihandler.get(self.hmc, '/api/console/user-patterns',
                                   True)
        act_user_patterns = resp['user-patterns']
        act_uris = [up['element-uri'] for up in act_user_patterns]

        # Verify that the actual order is the new (expected) order:
        assert act_uris == new_uris

    def test_cons_reorderupat_err_no_console(self):
        """
        Test POST reorder user patterns when console does not exist in the
        faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        body = {
            'user-pattern-uris': []
        }
        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:

            self.urihandler.post(
                self.hmc, '/api/console/operations/reorder-user-patterns',
                body, True, True)

        exc = exc_info.value
        assert exc.reason == 1


class TestConsoleGetAuditLogHandler:
    """
    All tests for class ConsoleGetAuditLogHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        ConsoleGetAuditLogHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/console', ConsoleHandler),
            (r'/api/console/operations/get-audit-log',
             ConsoleGetAuditLogHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cons_get_audlog(self):
        """
        Test GET console get-audit-log.
        """

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc, '/api/console/operations/get-audit-log', True)

        assert resp == []

    # TODO: Add testcases with non-empty audit log (once supported in mock)

    def test_cons_get_audlog_err_no_console(self):
        """
        Test GET console get-audit-log when console does not exist in the
        faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(
                self.hmc, '/api/console/operations/get-audit-log', True)

        exc = exc_info.value
        assert exc.reason == 1


class TestConsoleGetSecurityLogHandler:
    """
    All tests for class ConsoleGetSecurityLogHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        ConsoleGetSecurityLogHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/console', ConsoleHandler),
            (r'/api/console/operations/get-security-log',
             ConsoleGetSecurityLogHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cons_get_seclog(self):
        """
        Test GET console get-security-log.
        """

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc, '/api/console/operations/get-security-log', True)

        assert resp == []

    # TODO: Add testcases with non-empty security log (once supported in mock)

    def test_cons_get_seclog_err_no_console(self):
        """
        Test GET console get-security-log when console does not exist in the
        faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(
                self.hmc, '/api/console/operations/get-security-log', True)

        exc = exc_info.value
        assert exc.reason == 1


class TestConsoleListUnmanagedCpcsHandler:
    """
    All tests for class ConsoleListUnmanagedCpcsHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        ConsoleListUnmanagedCpcsHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/console', ConsoleHandler),
            (r'/api/console/operations/list-unmanaged-cpcs(?:\?(.*))?',
             ConsoleListUnmanagedCpcsHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_umcpc_list(self):
        """
        Test GET console list-unmanaged-cpcs.
        """

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc, '/api/console/operations/list-unmanaged-cpcs', True)

        cpcs = resp['cpcs']
        assert cpcs == []

    # TODO: Add testcases for non-empty list of unmanaged CPCs

    def test_umcpc_list_err_no_console(self):
        """
        Test GET console list-unmanaged-cpcs when console does not exist in the
        faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(
                self.hmc, '/api/console/operations/list-unmanaged-cpcs', True)

        exc = exc_info.value
        assert exc.reason == 1


class TestUserHandlers:
    """
    All tests for classes UsersHandler and UserHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        UsersHandler and UserHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            (r'/api/console/users(?:\?(.*))?', UsersHandler),
            (r'/api/users/([^/]+)', UserHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_user_list(self):
        """
        Test GET users (list).
        """

        # the function to be tested:
        users = self.urihandler.get(self.hmc, '/api/console/users', True)

        exp_users = {  # properties reduced to those returned by List
            'users': [
                {
                    'object-uri': '/api/users/fake-user-oid-1',
                    'name': 'fake_user_name_1',
                    'type': 'system-defined',
                },
            ]
        }
        assert users == exp_users

    def test_user_list_err_no_console(self):
        """
        Test GET users when console does not exist in the faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(self.hmc, '/api/console/users', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_user_get(self):
        """
        Test GET user.
        """

        # the function to be tested:
        user1 = self.urihandler.get(self.hmc, '/api/users/fake-user-oid-1',
                                    True)

        exp_user1 = {  # properties reduced to those in standard test HMC
            'object-id': 'fake-user-oid-1',
            'object-uri': '/api/users/fake-user-oid-1',
            'class': 'user',
            'parent': '/api/console',
            'name': 'fake_user_name_1',
            'description': 'User #1',
            'type': 'system-defined',
            'disabled': False,
        }
        assert user1 == exp_user1

    def test_user_create_verify(self):
        """
        Test POST users (create user).
        """

        new_user2 = {
            'object-id': '2',
            'name': 'user_2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
            'password': 'bla',
            'password-rule-uri': '/api/console/password-rules/dummy',
        }

        # the function to be tested:
        resp = self.urihandler.post(self.hmc, '/api/console/users',
                                    new_user2, True, True)

        assert len(resp) == 1
        assert 'object-uri' in resp
        new_user2_uri = resp['object-uri']
        assert new_user2_uri == '/api/users/2'

        exp_user2 = {
            'object-id': '2',
            'object-uri': '/api/users/2',
            'class': 'user',
            'parent': '/api/console',
            'name': 'user_2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
            'password-rule-uri': '/api/console/password-rules/dummy',
            'disabled': False,
        }

        # the function to be tested:
        user2 = self.urihandler.get(self.hmc, '/api/users/2', True)

        for name, exp_value in exp_user2.items():
            assert name in user2
            value = user2[name]
            assert value == exp_value, \
                f"Unexpected value for property {name!r}: actual: {value!r}, " \
                f"expected: {exp_value!r}"

    def test_user_create_err_no_console(self):
        """
        Test POST users (create) when console does not exist in the faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        new_user2 = {
            'object-id': '2',
            'name': 'user_2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
        }

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, '/api/console/users', new_user2,
                                 True, True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_user_update_verify(self):
        """
        Test POST user (update).
        """

        update_user1 = {
            'description': 'updated user #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/users/fake-user-oid-1',
                             update_user1, True, True)

        user1 = self.urihandler.get(self.hmc, '/api/users/fake-user-oid-1',
                                    True)
        assert user1['description'] == 'updated user #1'

    def test_user_delete_verify(self):
        """
        Test DELETE user.
        """

        testcases = [
            # (user_props, exp_exc_tuple)
            ({
                'object-id': '2',
                'name': 'user_2',
                'description': 'User #2',
                'type': 'standard',
                'authentication-type': 'local',
                'password': 'bla',
                'password-rule-uri': '/api/console/password-rules/dummy'},
             None),
            ({
                'object-id': '3',
                'name': 'user_3',
                'description': 'User #3',
                'type': 'template',
                'authentication-type': 'local',
                'password': 'bla',
                'password-rule-uri': '/api/console/password-rules/dummy'},
             None),
            ({
                'object-id': '4',
                'name': 'user_4',
                'description': 'User #4',
                'type': 'pattern-based',
                'authentication-type': 'local',
                'password': 'bla',
                'password-rule-uri': '/api/console/password-rules/dummy'},
             (400, 312)),
        ]
        for user_props, exp_exc_tuple in testcases:
            self._test_user_delete_verify_one(user_props, exp_exc_tuple)

    def _test_user_delete_verify_one(self, user_props, exp_exc_tuple):
        """
        Internal helper function that tests deleting a user.
        """

        user_oid = user_props['object-id']
        user_uri = f'/api/users/{user_oid}'

        # Create the user
        self.urihandler.post(self.hmc, '/api/console/users', user_props, True,
                             True)

        # Verify that it exists
        self.urihandler.get(self.hmc, user_uri, True)

        if exp_exc_tuple is not None:

            with pytest.raises(HTTPError) as exc_info:

                # Execute the code to be tested
                self.urihandler.delete(self.hmc, user_uri, True)

            exc = exc_info.value
            assert exc.http_status == exp_exc_tuple[0]
            assert exc.reason == exp_exc_tuple[1]

            # Verify that it still exists
            self.urihandler.get(self.hmc, user_uri, True)

        else:

            # Execute the code to be tested
            self.urihandler.delete(self.hmc, user_uri, True)

            # Verify that it has been deleted
            with pytest.raises(InvalidResourceError):
                self.urihandler.get(self.hmc, user_uri, True)


class TestUserAddUserRoleHandler:
    """
    All tests for class UserAddUserRoleHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        UserAddUserRoleHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        # Has a system-defined User (oid=fake-user-oid-1)
        # Has a system-defined User Role (oid=fake-user-role-oid-1)

        self.uris = (
            (r'/api/console/users(?:\?(.*))?', UsersHandler),
            (r'/api/users/([^/]+)', UserHandler),
            (r'/api/users/([^/]+)/operations/add-user-role',
             UserAddUserRoleHandler),
            (r'/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
            (r'/api/user-roles/([^/]+)', UserRoleHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_urole_add(self):
        """
        Test successful addition of a user role to a user.
        """

        # Add a user-defined User for our tests
        user2 = {
            'name': 'user2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
            'password': 'bla',
            'password-rule-uri': '/api/console/password-rules/dummy',
        }
        resp = self.urihandler.post(
            self.hmc, '/api/console/users', user2, True, True)
        self.user2_uri = resp['object-uri']
        self.user2_props = self.urihandler.get(
            self.hmc, self.user2_uri, True)

        # Add a user-defined User Role for our tests
        user_role2 = {
            'name': 'user_role_2',
            'description': 'User Role #2',
        }
        resp = self.urihandler.post(
            self.hmc, '/api/console/user-roles', user_role2, True, True)
        self.user_role2_uri = resp['object-uri']
        self.user_role2_props = self.urihandler.get(
            self.hmc, self.user_role2_uri, True)

        uri = self.user2_uri + '/operations/add-user-role'
        input_parms = {
            'user-role-uri': self.user_role2_uri
        }

        # the function to be tested:
        resp = self.urihandler.post(self.hmc, uri, input_parms, True, True)

        assert resp is None
        user2_props = self.urihandler.get(self.hmc, self.user2_uri, True)
        assert 'user-roles' in user2_props
        user_roles = user2_props['user-roles']
        assert len(user_roles) == 1
        user_role_uri = user_roles[0]
        assert user_role_uri == self.user_role2_uri

    def test_urole_add_err_bad_user(self):
        """
        Test failed addition of a user role to a bad user.
        """

        # Add a user-defined User Role for our tests
        user_role2 = {
            'name': 'user_role_2',
            'description': 'User Role #2',
        }
        resp = self.urihandler.post(
            self.hmc, '/api/console/user-roles', user_role2, True, True)
        self.user_role2_uri = resp['object-uri']
        self.user_role2_props = self.urihandler.get(
            self.hmc, self.user_role2_uri, True)

        bad_user_uri = '/api/users/not-found-oid'

        uri = bad_user_uri + '/operations/add-user-role'
        input_parms = {
            'user-role-uri': self.user_role2_uri
        }
        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, uri, input_parms, True, True)

        exc = exc_info.value
        assert exc.reason == 1

    # TODO: Add testcase for adding to system-defined or pattern-based user

    def test_urole_add_err_bad_user_role(self):
        """
        Test failed addition of a bad user role to a user.
        """

        # Add a user-defined User for our tests
        user2 = {
            'name': 'user2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
            'password': 'bla',
            'password-rule-uri': '/api/console/password-rules/dummy',
        }
        resp = self.urihandler.post(
            self.hmc, '/api/console/users', user2, True, True)
        self.user2_uri = resp['object-uri']
        self.user2_props = self.urihandler.get(
            self.hmc, self.user2_uri, True)

        bad_user_role_uri = '/api/user-roles/not-found-oid'

        uri = self.user2_uri + '/operations/add-user-role'
        input_parms = {
            'user-role-uri': bad_user_role_uri
        }
        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, uri, input_parms, True, True)

        exc = exc_info.value
        assert exc.reason == 2


class TestUserRemoveUserRoleHandler:
    """
    All tests for class UserRemoveUserRoleHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        UserRemoveUserRoleHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        # Has a system-defined User (oid=fake-user-oid-1)
        # Has a system-defined User Role (oid=fake-user-role-oid-1)

        self.uris = (
            (r'/api/console/users(?:\?(.*))?', UsersHandler),
            (r'/api/users/([^/]+)', UserHandler),
            (r'/api/users/([^/]+)/operations/add-user-role',
             UserAddUserRoleHandler),
            (r'/api/users/([^/]+)/operations/remove-user-role',
             UserRemoveUserRoleHandler),
            (r'/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
            (r'/api/user-roles/([^/]+)', UserRoleHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_urole_remove(self):
        """
        Test successful removal of a user role from a user.
        """

        # Add a user-defined User for our tests
        user2 = {
            'name': 'user2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
            'password': 'bla',
            'password-rule-uri': '/api/console/password-rules/dummy',
        }
        resp = self.urihandler.post(
            self.hmc, '/api/console/users', user2, True, True)
        self.user2_uri = resp['object-uri']
        self.user2_props = self.urihandler.get(
            self.hmc, self.user2_uri, True)

        # Add a user-defined User Role for our tests
        user_role2 = {
            'name': 'user_role_2',
            'description': 'User Role #2',
        }
        resp = self.urihandler.post(
            self.hmc, '/api/console/user-roles', user_role2, True, True)
        self.user_role2_uri = resp['object-uri']
        self.user_role2_props = self.urihandler.get(
            self.hmc, self.user_role2_uri, True)

        # Add the user role to the user
        uri = self.user2_uri + '/operations/add-user-role'
        input_parms = {
            'user-role-uri': self.user_role2_uri
        }
        self.urihandler.post(self.hmc, uri, input_parms, True, True)

        uri = self.user2_uri + '/operations/remove-user-role'
        input_parms = {
            'user-role-uri': self.user_role2_uri
        }

        # the function to be tested:
        resp = self.urihandler.post(self.hmc, uri, input_parms, True, True)

        assert resp is None
        user2_props = self.urihandler.get(self.hmc, self.user2_uri, True)
        assert 'user-roles' in user2_props
        user_roles = user2_props['user-roles']
        assert len(user_roles) == 0

    def test_urole_remove_err_bad_user(self):
        """
        Test failed removal of a user role from a bad user.
        """

        # Add a user-defined User Role for our tests
        user_role2 = {
            'name': 'user_role_2',
            'description': 'User Role #2',
        }
        resp = self.urihandler.post(
            self.hmc, '/api/console/user-roles', user_role2, True, True)
        self.user_role2_uri = resp['object-uri']
        self.user_role2_props = self.urihandler.get(
            self.hmc, self.user_role2_uri, True)

        bad_user_uri = '/api/users/not-found-oid'

        uri = bad_user_uri + '/operations/remove-user-role'
        input_parms = {
            'user-role-uri': self.user_role2_uri
        }
        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, uri, input_parms, True, True)

        exc = exc_info.value
        assert exc.reason == 1

    # TODO: Add testcase for removing from system-defined or pattern-based user

    def test_urole_remove_err_bad_user_role(self):
        """
        Test failed removal of a bad user role from a user.
        """

        # Add a user-defined User for our tests
        user2 = {
            'name': 'user2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
            'password': 'bla',
            'password-rule-uri': '/api/console/password-rules/dummy',
        }
        resp = self.urihandler.post(
            self.hmc, '/api/console/users', user2, True, True)
        self.user2_uri = resp['object-uri']
        self.user2_props = self.urihandler.get(
            self.hmc, self.user2_uri, True)

        bad_user_role_uri = '/api/user-roles/not-found-oid'

        uri = self.user2_uri + '/operations/remove-user-role'
        input_parms = {
            'user-role-uri': bad_user_role_uri
        }
        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, uri, input_parms, True, True)

        exc = exc_info.value
        assert exc.reason == 2

    def test_urole_remove_err_no_user_role(self):
        """
        Test failed removal of a user role that a user does not have.
        """

        # Add a user-defined User for our tests
        user2 = {
            'name': 'user2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
            'password': 'bla',
            'password-rule-uri': '/api/console/password-rules/dummy',
        }
        resp = self.urihandler.post(
            self.hmc, '/api/console/users', user2, True, True)
        self.user2_uri = resp['object-uri']
        self.user2_props = self.urihandler.get(
            self.hmc, self.user2_uri, True)

        # Add a user-defined User Role for our tests
        user_role2 = {
            'name': 'user_role_2',
            'description': 'User Role #2',
        }
        resp = self.urihandler.post(
            self.hmc, '/api/console/user-roles', user_role2, True, True)
        self.user_role2_uri = resp['object-uri']
        self.user_role2_props = self.urihandler.get(
            self.hmc, self.user_role2_uri, True)

        # Do not(!) add the user role to the user

        uri = self.user2_uri + '/operations/remove-user-role'
        input_parms = {
            'user-role-uri': self.user_role2_uri
        }
        with pytest.raises(ConflictError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, uri, input_parms, True, True)

        exc = exc_info.value
        assert exc.reason == 316


class TestUserRoleHandlers:
    """
    All tests for classes UserRolesHandler and UserRoleHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        UserRolesHandler and UserRoleHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
            (r'/api/user-roles/([^/]+)', UserRoleHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_urole_list(self):
        """
        Test GET user roles (list).
        """

        # the function to be tested:
        user_roles = self.urihandler.get(self.hmc, '/api/console/user-roles',
                                         True)

        exp_user_roles = {  # properties reduced to those returned by List
            'user-roles': [
                {
                    'object-uri': '/api/user-roles/fake-user-role-oid-1',
                    'name': 'fake_user_role_name_1',
                    'type': 'system-defined',
                },
                {
                    'object-uri': '/api/user-roles/fake-hmc-operator-tasks',
                    'name': 'hmc-operator-tasks',
                    'type': 'system-defined',
                },
            ]
        }
        assert user_roles == exp_user_roles

    def test_urole_list_err_no_console(self):
        """
        Test GET user roles when console does not exist in the faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(self.hmc, '/api/console/user-roles', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_urole_get(self):
        """
        Test GET user role.
        """

        # the function to be tested:
        user_role1 = self.urihandler.get(
            self.hmc, '/api/user-roles/fake-user-role-oid-1', True)

        exp_user_role1 = {  # properties reduced to those in standard test HMC
            'object-id': 'fake-user-role-oid-1',
            'object-uri': '/api/user-roles/fake-user-role-oid-1',
            'class': 'user-role',
            'parent': '/api/console',
            'name': 'fake_user_role_name_1',
            'description': 'User Role #1',
            'type': 'system-defined',
            'is-inheritance-enabled': False,
        }
        assert user_role1 == exp_user_role1

    def test_urole_create_verify(self):
        """
        Test POST user roles (create).
        """

        new_user_role2 = {
            'name': 'user_role_2',
            'description': 'User Role #2',
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/user-roles', new_user_role2, True, True)

        assert len(resp) == 1
        assert 'object-uri' in resp
        new_user_role2_uri = resp['object-uri']

        # the function to be tested:
        user_role2 = self.urihandler.get(self.hmc, new_user_role2_uri, True)

        assert user_role2['type'] == 'user-defined'

    def test_urole_create_err_no_console(self):
        """
        Test POST user roles (create) when console does not exist in the
        faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        new_user_role2 = {
            'name': 'user_role_2',
            'description': 'User Role #2',
        }

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, '/api/console/user-roles',
                                 new_user_role2, True, True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_urole_create_err_type(self):
        """
        Test POST user roles (create) with invalid specification of type,
        which is implied and must not be specified.
        """

        new_user_role2 = {
            'name': 'user_role_2',
            'description': 'User Role #2',
            'type': 'user-defined',  # error: type is implied
        }

        with pytest.raises(BadRequestError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, '/api/console/user-roles',
                                 new_user_role2, True, True)

        exc = exc_info.value
        assert exc.reason == 6

    def test_urole_update_verify(self):
        """
        Test POST user role (update).
        """

        update_user_role1 = {
            'description': 'updated user #1',
        }

        # the function to be tested:
        self.urihandler.post(
            self.hmc, '/api/user-roles/fake-user-role-oid-1',
            update_user_role1, True, True)

        user_role1 = self.urihandler.get(
            self.hmc, '/api/user-roles/fake-user-role-oid-1', True)
        assert user_role1['description'] == 'updated user #1'

    def test_urole_delete_verify(self):
        """
        Test DELETE user role.
        """

        new_user_role2 = {
            'name': 'user_role_2',
            'description': 'User Role #2',
        }

        # Create the user role
        resp = self.urihandler.post(
            self.hmc, '/api/console/user-roles', new_user_role2, True, True)

        new_user_role2_uri = resp['object-uri']

        # Verify that it exists
        self.urihandler.get(self.hmc, new_user_role2_uri, True)

        # the function to be tested:
        self.urihandler.delete(self.hmc, new_user_role2_uri, True)

        # Verify that it has been deleted
        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc, new_user_role2_uri, True)


class TestUserRoleAddPermissionHandler:
    """
    All tests for class UserRoleAddPermissionHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        UserRoleAddPermissionHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        # Has a system-defined User Role (oid=fake-user-role-oid-1)

        self.uris = (
            (r'/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
            (r'/api/user-roles/([^/]+)', UserRoleHandler),
            (r'/api/user-roles/([^/]+)/operations/add-permission',
             UserRoleAddPermissionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_urole_addperm_all(self):
        """
        All tests for adding permissions to a User Role.
        """

        testcases = [
            # (input_permission, exp_permission)
            (
                {
                    'permitted-object': 'partition',
                    'permitted-object-type': 'object-class',
                    'include-members': True,
                    'view-only-mode': False,
                },
                {
                    'permitted-object': 'partition',
                    'permitted-object-type': 'object-class',
                    'include-members': True,
                    'view-only-mode': False,
                },
            ),
            (
                {
                    'permitted-object': 'adapter',
                    'permitted-object-type': 'object-class',
                },
                {
                    'permitted-object': 'adapter',
                    'permitted-object-type': 'object-class',
                    'include-members': False,
                    'view-only-mode': True,
                },
            ),
        ]
        for input_permission, exp_permission in testcases:
            self._test_urole_addperm_one(input_permission, exp_permission)

    def _test_urole_addperm_one(self, input_permission, exp_permission):
        """
        Internal helper function that tests adding a user role.
        """

        # Add a user-defined User Role for our tests
        user_role2 = {
            'name': 'user_role_2',
            'description': 'User Role #2',
        }
        resp = self.urihandler.post(
            self.hmc, '/api/console/user-roles', user_role2, True, True)
        self.user_role2_uri = resp['object-uri']
        self.user_role2_props = self.urihandler.get(
            self.hmc, self.user_role2_uri, True)

        uri = self.user_role2_uri + '/operations/add-permission'

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, uri, input_permission, True, True)

        assert resp is None
        props = self.urihandler.get(self.hmc, self.user_role2_uri, True)
        assert 'permissions' in props
        permissions = props['permissions']
        assert len(permissions) == 1
        perm = permissions[0]
        assert perm == exp_permission

    def test_urole_addperm_err_bad(self):
        """
        Test failed addition of a permission to a bad User Role.
        """

        bad_user_role_uri = '/api/user-roles/not-found-oid'

        uri = bad_user_role_uri + '/operations/add-permission'
        input_parms = {
            'permitted-object': 'partition',
            'permitted-object-type': 'object-class',
            'include-members': True,
            'view-only-mode': False,
        }
        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, uri, input_parms, True, True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_urole_addperm_err_system(self):
        """
        Test failed addition of a permission to a system-defined User Role.
        """

        system_user_role_uri = '/api/user-roles/fake-user-role-oid-1'

        uri = system_user_role_uri + '/operations/add-permission'
        input_parms = {
            'permitted-object': 'partition',
            'permitted-object-type': 'object-class',
            'include-members': True,
            'view-only-mode': False,
        }
        with pytest.raises(BadRequestError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, uri, input_parms, True, True)

        exc = exc_info.value
        assert exc.reason == 314


class TestUserRoleRemovePermissionHandler:
    """
    All tests for class UserRoleRemovePermissionHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        UserRoleRemovePermissionHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        # Has a system-defined User Role (oid=fake-user-role-oid-1)

        self.uris = (
            (r'/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
            (r'/api/user-roles/([^/]+)', UserRoleHandler),
            (r'/api/user-roles/([^/]+)/operations/add-permission',
             UserRoleAddPermissionHandler),
            (r'/api/user-roles/([^/]+)/operations/remove-permission',
             UserRoleRemovePermissionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_urole_rmperm_all(self):
        """
        All tests for removing permissions from a User Role.
        """

        testcases = [
            # (input_permission, removed_permission)
            (
                {
                    'permitted-object': 'partition',
                    'permitted-object-type': 'object-class',
                    'include-members': True,
                    'view-only-mode': False,
                },
                {
                    'permitted-object': 'partition',
                    'permitted-object-type': 'object-class',
                    'include-members': True,
                    'view-only-mode': False,
                },
            ),
            (
                {
                    'permitted-object': 'adapter',
                    'permitted-object-type': 'object-class',
                },
                {
                    'permitted-object': 'adapter',
                    'permitted-object-type': 'object-class',
                    'include-members': False,
                    'view-only-mode': True,
                },
            ),
        ]
        for input_permission, removed_permission in testcases:
            self._test_urole_rmperm_one(
                input_permission, removed_permission)

    def _test_urole_rmperm_one(
            self, input_permission, removed_permission):
        """
        Internal helper function that tests removing a user role.
        """

        # Add a user-defined User Role for our tests
        user_role2 = {
            'name': 'user_role_2',
            'description': 'User Role #2',
        }
        resp = self.urihandler.post(
            self.hmc, '/api/console/user-roles', user_role2, True, True)
        self.user_role2_uri = resp['object-uri']
        self.user_role2_props = self.urihandler.get(
            self.hmc, self.user_role2_uri, True)

        # Add the permission to be removed to the User Role:
        uri = self.user_role2_uri + '/operations/add-permission'
        resp = self.urihandler.post(
            self.hmc, uri, removed_permission, True, True)

        uri = self.user_role2_uri + '/operations/remove-permission'

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, uri, input_permission, True, True)

        assert resp is None
        props = self.urihandler.get(self.hmc, self.user_role2_uri, True)
        assert 'permissions' in props
        permissions = props['permissions']
        assert len(permissions) == 0

    def test_urole_rmperm_err_bad(self):
        """
        Test failed removal of a permission from a bad User Role.
        """

        bad_user_role_uri = '/api/user-roles/not-found-oid'

        uri = bad_user_role_uri + '/operations/remove-permission'
        input_parms = {
            'permitted-object': 'partition',
            'permitted-object-type': 'object-class',
            'include-members': True,
            'view-only-mode': False,
        }
        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, uri, input_parms, True, True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_urole_rmperm_err_system(self):
        """
        Test failed removal of a permission from a system-defined User Role.
        """

        system_user_role_uri = '/api/user-roles/fake-user-role-oid-1'

        uri = system_user_role_uri + '/operations/remove-permission'
        input_parms = {
            'permitted-object': 'partition',
            'permitted-object-type': 'object-class',
            'include-members': True,
            'view-only-mode': False,
        }
        with pytest.raises(BadRequestError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, uri, input_parms, True, True)

        exc = exc_info.value
        assert exc.reason == 314


class TestTaskHandlers:
    """
    All tests for classes TasksHandler and TaskHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        TasksHandler and TaskHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/console/tasks(?:\?(.*))?', TasksHandler),
            (r'/api/console/tasks/([^/]+)', TaskHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_task_list(self):
        """
        Test GET tasks (list).
        """

        # the function to be tested:
        tasks = self.urihandler.get(self.hmc, '/api/console/tasks', True)

        exp_tasks = {  # properties reduced to those returned by List
            'tasks': [
                {
                    'element-uri': '/api/console/tasks/fake-task-oid-1',
                    'name': 'fake_task_name_1',
                },
                {
                    'element-uri': '/api/console/tasks/fake-task-oid-2',
                    'name': 'fake_task_name_2',
                },
            ]
        }
        assert tasks == exp_tasks

    def test_task_list_err_no_console(self):
        """
        Test GET tasks (list) when console does not exist in the faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(self.hmc, '/api/console/tasks', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_task_get(self):
        """
        Test GET task.
        """

        # the function to be tested:
        task1 = self.urihandler.get(
            self.hmc, '/api/console/tasks/fake-task-oid-1', True)

        exp_task1 = {  # properties reduced to those in standard test HMC
            'element-id': 'fake-task-oid-1',
            'element-uri': '/api/console/tasks/fake-task-oid-1',
            'class': 'task',
            'parent': '/api/console',
            'name': 'fake_task_name_1',
            'description': 'Task #1',
        }
        assert task1 == exp_task1


class TestUserPatternHandlers:
    """
    All tests for classes UserPatternsHandler and UserPatternHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        UserPatternsHandler and UserPatternHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            (r'/api/console/user-patterns(?:\?(.*))?', UserPatternsHandler),
            (r'/api/console/user-patterns/([^/]+)', UserPatternHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_upat_list(self):
        """
        Test GET user patterns (list).
        """

        # the function to be tested:
        user_patterns = self.urihandler.get(
            self.hmc, '/api/console/user-patterns', True)

        exp_user_patterns = {  # properties reduced to those returned by List
            'user-patterns': [
                {
                    'element-uri':
                        '/api/console/user-patterns/fake-user-pattern-oid-1',
                    'name': 'fake_user_pattern_name_1',
                    'type': 'glob-like',
                },
            ]
        }
        assert user_patterns == exp_user_patterns

    def test_upat_list_err_no_console(self):
        """
        Test GET user patterns (list) when console does not exist in the
        faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(self.hmc, '/api/console/user-patterns', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_upat_get(self):
        """
        Test GET user pattern.
        """

        # the function to be tested:
        user_pattern1 = self.urihandler.get(
            self.hmc, '/api/console/user-patterns/fake-user-pattern-oid-1',
            True)

        exp_user_pattern1 = {  # properties reduced to those in std test HMC
            'element-id': 'fake-user-pattern-oid-1',
            'element-uri':
                '/api/console/user-patterns/fake-user-pattern-oid-1',
            'class': 'user-pattern',
            'parent': '/api/console',
            'name': 'fake_user_pattern_name_1',
            'description': 'User Pattern #1',
            'pattern': 'fake_user_name_*',
            'type': 'glob-like',
            'retention-time': 0,
            'specific-template-uri': '/api/users/fake-user-oid-1',
        }
        assert user_pattern1 == exp_user_pattern1

    def test_upat_create_verify(self):
        """
        Test POST user patterns (create).
        """

        new_user_pattern_input = {
            'name': 'user_pattern_X',
            'description': 'User Pattern #X',
            'pattern': 'user*',
            'type': 'glob-like',
            'retention-time': 0,
            'specific-template-uri': '/api/users/fake-user-oid-1',
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/user-patterns', new_user_pattern_input,
            True, True)

        assert len(resp) == 1
        assert 'element-uri' in resp
        new_user_pattern_uri = resp['element-uri']

        # the function to be tested:
        new_user_pattern = self.urihandler.get(
            self.hmc, new_user_pattern_uri, True)

        new_name = new_user_pattern['name']
        input_name = new_user_pattern_input['name']
        assert new_name == input_name

    def test_upat_create_err_no_console(self):
        """
        Test POST user patterns (create) when console does not exist in the
        faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        new_user_pattern_input = {
            'name': 'user_pattern_X',
            'description': 'User Pattern #X',
        }

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, '/api/console/user-patterns',
                                 new_user_pattern_input, True, True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_upat_update_verify(self):
        """
        Test POST user pattern (update).
        """

        update_user_pattern1 = {
            'description': 'updated user pattern #1',
        }

        # the function to be tested:
        self.urihandler.post(
            self.hmc, '/api/console/user-patterns/fake-user-pattern-oid-1',
            update_user_pattern1, True, True)

        user_pattern1 = self.urihandler.get(
            self.hmc, '/api/console/user-patterns/fake-user-pattern-oid-1',
            True)
        assert user_pattern1['description'] == 'updated user pattern #1'

    def test_upat_delete_verify(self):
        """
        Test DELETE user pattern.
        """

        new_user_pattern_input = {
            'name': 'user_pattern_x',
            'description': 'User Pattern #X',
            'pattern': 'user*',
            'type': 'glob-like',
            'retention-time': 0,
            'specific-template-uri': '/api/users/fake-user-oid-1',
        }

        # Create the User Pattern
        resp = self.urihandler.post(
            self.hmc, '/api/console/user-patterns', new_user_pattern_input,
            True, True)

        new_user_pattern_uri = resp['element-uri']

        # Verify that it exists
        self.urihandler.get(self.hmc, new_user_pattern_uri, True)

        # the function to be tested:
        self.urihandler.delete(self.hmc, new_user_pattern_uri, True)

        # Verify that it has been deleted
        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc, new_user_pattern_uri, True)


class TestPasswordRuleHandlers:
    """
    All tests for classes PasswordRulesHandler and PasswordRuleHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        PasswordRulesHandler and PasswordRuleHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            (r'/api/console/password-rules(?:\?(.*))?', PasswordRulesHandler),
            (r'/api/console/password-rules/([^/]+)', PasswordRuleHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_pwrule_list(self):
        """
        Test GET password rules (list).
        """

        # the function to be tested:
        password_rules = self.urihandler.get(
            self.hmc, '/api/console/password-rules', True)

        exp_password_rules = {  # properties reduced to those returned by List
            'password-rules': [
                {
                    'element-uri':
                        '/api/console/password-rules/fake-password-rule-oid-1',
                    'name': 'fake_password_rule_name_1',
                    'type': 'system-defined',
                },
            ]
        }
        assert password_rules == exp_password_rules

    def test_pwrule_list_err_no_console(self):
        """
        Test GET password rules (list) when console does not exist in the
        faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(self.hmc, '/api/console/password-rules', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_pwrule_get(self):
        """
        Test GET password rule.
        """

        # the function to be tested:
        password_rule1 = self.urihandler.get(
            self.hmc, '/api/console/password-rules/fake-password-rule-oid-1',
            True)

        exp_password_rule1 = {  # properties reduced to those in std test HMC
            'element-id': 'fake-password-rule-oid-1',
            'element-uri':
                '/api/console/password-rules/fake-password-rule-oid-1',
            'class': 'password-rule',
            'parent': '/api/console',
            'name': 'fake_password_rule_name_1',
            'description': 'Password Rule #1',
            'type': 'system-defined',
            'max-length': 256,
            'min-length': 8,
        }
        assert password_rule1 == exp_password_rule1

    def test_pwrule_create_verify(self):
        """
        Test POST password rules (create).
        """

        new_password_rule_input = {
            'name': 'password_rule_X',
            'description': 'Password Rule #X',
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/password-rules', new_password_rule_input,
            True, True)

        assert len(resp) == 1
        assert 'element-uri' in resp
        new_password_rule_uri = resp['element-uri']

        # the function to be tested:
        new_password_rule = self.urihandler.get(
            self.hmc, new_password_rule_uri, True)

        new_name = new_password_rule['name']
        input_name = new_password_rule_input['name']
        assert new_name == input_name

    def test_pwrule_create_err_no_console(self):
        """
        Test POST password rules (create) when console does not exist in the
        faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        new_password_rule_input = {
            'name': 'password_rule_X',
            'description': 'Password Rule #X',
        }

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(self.hmc, '/api/console/password-rules',
                                 new_password_rule_input, True, True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_pwrule_update_verify(self):
        """
        Test POST password rule (update).
        """

        update_password_rule1 = {
            'description': 'updated password rule #1',
        }

        # the function to be tested:
        self.urihandler.post(
            self.hmc, '/api/console/password-rules/fake-password-rule-oid-1',
            update_password_rule1, True, True)

        password_rule1 = self.urihandler.get(
            self.hmc, '/api/console/password-rules/fake-password-rule-oid-1',
            True)
        assert password_rule1['description'] == 'updated password rule #1'

    def test_pwrule_delete_verify(self):
        """
        Test DELETE password rule.
        """

        new_password_rule_input = {
            'name': 'password_rule_X',
            'description': 'Password Rule #X',
        }

        # Create the Password Rule
        resp = self.urihandler.post(
            self.hmc, '/api/console/password-rules', new_password_rule_input,
            True, True)

        new_password_rule_uri = resp['element-uri']

        # Verify that it exists
        self.urihandler.get(self.hmc, new_password_rule_uri, True)

        # the function to be tested:
        self.urihandler.delete(self.hmc, new_password_rule_uri, True)

        # Verify that it has been deleted
        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc, new_password_rule_uri, True)


class TestLdapServerDefinitionHandlers:
    """
    All tests for classes LdapServerDefinitionsHandler and
    LdapServerDefinitionHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        LdapServerDefinitionsHandler and LdapServerDefinitionHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/console/ldap-server-definitions(?:\?(.*))?',
             LdapServerDefinitionsHandler),
            (r'/api/console/ldap-server-definitions/([^/]+)',
             LdapServerDefinitionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_lsd_list(self):
        """
        Test GET LDAP server definitions (list).
        """

        # the function to be tested:
        ldap_srv_defs = self.urihandler.get(
            self.hmc, '/api/console/ldap-server-definitions', True)

        exp_ldap_srv_defs = {  # properties reduced to those returned by List
            'ldap-server-definitions': [
                {
                    'element-uri':
                        '/api/console/ldap-server-definitions/'
                        'fake-ldap-srv-def-oid-1',
                    'name': 'fake_ldap_srv_def_name_1',
                },
            ]
        }
        assert ldap_srv_defs == exp_ldap_srv_defs

    def test_lsd_list_err_no_console(self):
        """
        Test GET LDAP server definitions (list) when console does not exist
        in the faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(
                self.hmc, '/api/console/ldap-server-definitions', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_lsd_get(self):
        """
        Test GET LDAP server definition.
        """

        # the function to be tested:
        ldap_srv_def1 = self.urihandler.get(
            self.hmc,
            '/api/console/ldap-server-definitions/fake-ldap-srv-def-oid-1',
            True)

        exp_ldap_srv_def1 = {  # properties reduced to those in std test HMC
            'element-id': 'fake-ldap-srv-def-oid-1',
            'element-uri':
                '/api/console/ldap-server-definitions/'
                'fake-ldap-srv-def-oid-1',
            'class': 'ldap-server-definition',
            'parent': '/api/console',
            'name': 'fake_ldap_srv_def_name_1',
            'description': 'LDAP Srv Def #1',
            'primary-hostname-ipaddr': '10.11.12.13',
            'connection-port': None,
            'use-ssl': False,
            'backup-hostname-ipaddr': None,
            'bind-distinguished-name': None,
            'location-method': 'pattern',
            'replication-overwrite-possible': False,
            'search-filter': None,
            'search-scope': None,
            'tolerate-untrusted-certificates': None,
        }
        assert ldap_srv_def1 == exp_ldap_srv_def1

    def test_lsd_create_verify(self):
        """
        Test POST LDAP server definitions (create).
        """

        new_ldap_srv_def_input = {
            'name': 'ldap_srv_def_X',
            'description': 'LDAP Srv Def #X',
            'primary-hostname-ipaddr': '10.11.12.13',
            'search-distinguished-name': 'test{0}',
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/ldap-server-definitions',
            new_ldap_srv_def_input, True, True)

        assert len(resp) == 1
        assert 'element-uri' in resp
        new_ldap_srv_def_uri = resp['element-uri']

        # the function to be tested:
        new_ldap_srv_def = self.urihandler.get(
            self.hmc, new_ldap_srv_def_uri, True)

        new_name = new_ldap_srv_def['name']
        input_name = new_ldap_srv_def_input['name']
        assert new_name == input_name

    def test_lsd_create_err_no_console(self):
        """
        Test POST LDAP server definitions (create) when console does not exist
        in the faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        new_ldap_srv_def_input = {
            'name': 'ldap_srv_def_X',
            'description': 'LDAP Srv Def #X',
        }

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(
                self.hmc, '/api/console/ldap-server-definitions',
                new_ldap_srv_def_input, True, True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_lsd_update_verify(self):
        """
        Test POST LDAP server definition (update).
        """

        update_ldap_srv_def1 = {
            'description': 'updated LDAP Srv Def #1',
        }

        # the function to be tested:
        self.urihandler.post(
            self.hmc,
            '/api/console/ldap-server-definitions/fake-ldap-srv-def-oid-1',
            update_ldap_srv_def1, True, True)

        ldap_srv_def1 = self.urihandler.get(
            self.hmc,
            '/api/console/ldap-server-definitions/fake-ldap-srv-def-oid-1',
            True)
        assert ldap_srv_def1['description'] == 'updated LDAP Srv Def #1'

    def test_lsd_delete_verify(self):
        """
        Test DELETE LDAP server definition.
        """

        new_ldap_srv_def_input = {
            'name': 'ldap_srv_def_X',
            'description': 'LDAP Srv Def #X',
            'primary-hostname-ipaddr': '10.11.12.13',
            'search-distinguished-name': 'test{0}',
        }

        # Create the LDAP Srv Def
        resp = self.urihandler.post(
            self.hmc, '/api/console/ldap-server-definitions',
            new_ldap_srv_def_input, True, True)

        new_ldap_srv_def_uri = resp['element-uri']

        # Verify that it exists
        self.urihandler.get(self.hmc, new_ldap_srv_def_uri, True)

        # the function to be tested:
        self.urihandler.delete(self.hmc, new_ldap_srv_def_uri, True)

        # Verify that it has been deleted
        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc, new_ldap_srv_def_uri, True)


class TestMfaServerDefinitionHandlers:
    """
    All tests for classes MfaServerDefinitionsHandler and
    MfaServerDefinitionHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        MfaServerDefinitionsHandler and MfaServerDefinitionHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/console/mfa-server-definitions(?:\?(.*))?',
             MfaServerDefinitionsHandler),
            (r'/api/console/mfa-server-definitions/([^/]+)',
             MfaServerDefinitionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_mfa_list(self):
        """
        Test GET MFA server definitions (list).
        """

        # the function to be tested:
        mfa_srv_defs = self.urihandler.get(
            self.hmc, '/api/console/mfa-server-definitions', True)

        exp_mfa_srv_defs = {  # properties reduced to those returned by List
            'mfa-server-definitions': [
                {
                    'element-uri':
                        '/api/console/mfa-server-definitions/'
                        'fake-mfa-srv-def-oid-1',
                    'name': 'fake_mfa_srv_def_name_1',
                },
            ]
        }
        assert mfa_srv_defs == exp_mfa_srv_defs

    def test_mfa_list_err_no_console(self):
        """
        Test GET MFA server definitions (list) when console does not exist
        in the faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(
                self.hmc, '/api/console/mfa-server-definitions', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_mfa_get(self):
        """
        Test GET MFA server definition.
        """

        # the function to be tested:
        mfa_srv_def1 = self.urihandler.get(
            self.hmc,
            '/api/console/mfa-server-definitions/fake-mfa-srv-def-oid-1',
            True)

        exp_mfa_srv_def1 = {  # properties reduced to those in std test HMC
            'element-id': 'fake-mfa-srv-def-oid-1',
            'element-uri':
                '/api/console/mfa-server-definitions/'
                'fake-mfa-srv-def-oid-1',
            'class': 'mfa-server-definition',
            'parent': '/api/console',
            'name': 'fake_mfa_srv_def_name_1',
            'description': 'MFA Srv Def #1',
            'hostname-ipaddr': '10.11.12.13',
            'port': 6789,
            'replication-overwrite-possible': False,
        }
        assert mfa_srv_def1 == exp_mfa_srv_def1

    def test_mfa_create_verify(self):
        """
        Test POST MFA server definitions (create).
        """

        new_mfa_srv_def_input = {
            'name': 'mfa_srv_def_X',
            'description': 'MFA Srv Def #X',
            'hostname-ipaddr': '10.11.12.13',
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/mfa-server-definitions',
            new_mfa_srv_def_input, True, True)

        assert len(resp) == 1
        assert 'element-uri' in resp
        new_mfa_srv_def_uri = resp['element-uri']

        # the function to be tested:
        new_mfa_srv_def = self.urihandler.get(
            self.hmc, new_mfa_srv_def_uri, True)

        new_name = new_mfa_srv_def['name']
        input_name = new_mfa_srv_def_input['name']
        assert new_name == input_name

    def test_mfa_create_err_no_console(self):
        """
        Test POST MFA server definitions (create) when console does not exist
        in the faked HMC.
        """

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        new_mfa_srv_def_input = {
            'name': 'mfa_srv_def_X',
            'description': 'MFA Srv Def #X',
        }

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(
                self.hmc, '/api/console/mfa-server-definitions',
                new_mfa_srv_def_input, True, True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_mfa_update_verify(self):
        """
        Test POST MFA server definition (update).
        """

        update_mfa_srv_def1 = {
            'description': 'updated MFA Srv Def #1',
        }

        # the function to be tested:
        self.urihandler.post(
            self.hmc,
            '/api/console/mfa-server-definitions/fake-mfa-srv-def-oid-1',
            update_mfa_srv_def1, True, True)

        mfa_srv_def1 = self.urihandler.get(
            self.hmc,
            '/api/console/mfa-server-definitions/fake-mfa-srv-def-oid-1',
            True)
        assert mfa_srv_def1['description'] == 'updated MFA Srv Def #1'

    def test_mfa_delete_verify(self):
        """
        Test DELETE MFA server definition.
        """

        new_mfa_srv_def_input = {
            'name': 'mfa_srv_def_X',
            'description': 'MFA Srv Def #X',
            'hostname-ipaddr': '10.11.12.13',
        }

        # Create the MFA Srv Def
        resp = self.urihandler.post(
            self.hmc, '/api/console/mfa-server-definitions',
            new_mfa_srv_def_input, True, True)

        new_mfa_srv_def_uri = resp['element-uri']

        # Verify that it exists
        self.urihandler.get(self.hmc, new_mfa_srv_def_uri, True)

        # the function to be tested:
        self.urihandler.delete(self.hmc, new_mfa_srv_def_uri, True)

        # Verify that it has been deleted
        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc, new_mfa_srv_def_uri, True)


class TestCpcHandlers:
    """
    All tests for classes CpcsHandler and CpcHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CpcsHandler and CpcHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs(?:\?(.*))?', CpcsHandler),
            (r'/api/cpcs/([^/]+)', CpcHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cpc_list(self):
        """
        Test GET CPCs (list).
        """

        # the function to be tested:
        cpcs = self.urihandler.get(self.hmc, '/api/cpcs', True)

        exp_cpcs = {  # properties reduced to those returned by List
            'cpcs': [
                {
                    'object-uri': '/api/cpcs/1',
                    'name': 'cpc_1',
                    'status': 'operating',
                    'has-unacceptable-status': False,
                    'dpm-enabled': False,
                    'se-version': '2.15.0',
                },
                {
                    'object-uri': '/api/cpcs/2',
                    'name': 'cpc_2',
                    'status': 'active',
                    'has-unacceptable-status': False,
                    'dpm-enabled': True,
                    'se-version': '2.16.0',
                },
            ]
        }
        assert cpcs == exp_cpcs

    def test_cpc_get(self):
        """
        Test GET CPC.
        """

        # the function to be tested:
        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)

        exp_cpc1 = {
            'object-id': '1',
            'object-uri': '/api/cpcs/1',
            'class': 'cpc',
            'parent': None,
            'name': 'cpc_1',
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'description': 'CPC #1 (classic mode)',
            'status': 'operating',
            'has-unacceptable-status': False,
            'se-version': '2.15.0',
        }
        assert cpc1 == exp_cpc1

    def test_cpc_update_verify(self):
        """
        Test POST CPC (update).
        """

        update_cpc1 = {
            'description': 'updated cpc #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/cpcs/1',
                             update_cpc1, True, True)

        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['description'] == 'updated cpc #1'


class TestCpcSetPowerSaveHandler:
    """
    All tests for class CpcSetPowerSaveHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CpcSetPowerSaveHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/set-cpc-power-save',
             CpcSetPowerSaveHandler),
        )
        self.urihandler = UriHandler(self.uris)

    @pytest.mark.parametrize(
        "power_saving, exp_error",
        [
            (None, (400, 7)),
            ('invalid_power_save', (400, 7)),
            ('high-performance', None),
            ('low-power', None),
            ('custom', None),
        ]
    )
    def test_cpc_set_powersave(self, power_saving, exp_error):
        """
        Test POST CPC set-cpc-power-save.
        """

        operation_body = {
            'power-saving': power_saving,
        }

        if exp_error:

            with pytest.raises(HTTPError) as exc_info:
                # the function to be tested:
                resp = self.urihandler.post(
                    self.hmc, '/api/cpcs/1/operations/set-cpc-power-save',
                    operation_body, True, True)

            exc = exc_info.value

            assert exc.http_status == exp_error[0]
            assert exc.reason == exp_error[1]

        else:

            # the function to be tested:
            resp = self.urihandler.post(
                self.hmc, '/api/cpcs/1/operations/set-cpc-power-save',
                operation_body, True, True)

            assert resp is None

            cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)

            assert cpc1['cpc-power-saving'] == power_saving
            assert cpc1['zcpc-power-saving'] == power_saving


class TestCpcSetPowerCappingHandler:
    """
    All tests for class CpcSetPowerCappingHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CpcSetPowerCappingHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/set-cpc-power-capping',
             CpcSetPowerCappingHandler),
        )
        self.urihandler = UriHandler(self.uris)

    @pytest.mark.parametrize(
        "power_capping_state, power_cap_current, exp_error",
        [
            (None, None, (400, 7)),
            ('enabled', None, (400, 7)),
            ('enabled', 20000, None),
            ('disabled', None, None),
        ]
    )
    def test_cpc_setpowercap(
            self, power_capping_state, power_cap_current, exp_error):
        """
        Test POST CPC set-cpc-power-capping.
        """

        operation_body = {
            'power-capping-state': power_capping_state,
        }
        if power_cap_current is not None:
            operation_body['power-cap-current'] = power_cap_current

        if exp_error:

            with pytest.raises(HTTPError) as exc_info:
                # the function to be tested:
                resp = self.urihandler.post(
                    self.hmc, '/api/cpcs/1/operations/set-cpc-power-capping',
                    operation_body, True, True)

            exc = exc_info.value

            assert exc.http_status == exp_error[0]
            assert exc.reason == exp_error[1]

        else:

            # the function to be tested:
            resp = self.urihandler.post(
                self.hmc, '/api/cpcs/1/operations/set-cpc-power-capping',
                operation_body, True, True)

            assert resp is None

            cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)

            assert cpc1['cpc-power-capping-state'] == power_capping_state
            assert cpc1['cpc-power-cap-current'] == power_cap_current
            assert cpc1['zcpc-power-capping-state'] == power_capping_state
            assert cpc1['zcpc-power-cap-current'] == power_cap_current


class TestCpcGetEnergyManagementDataHandler:
    """
    All tests for class CpcGetEnergyManagementDataHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CpcGetEnergyManagementDataHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/energy-management-data',
             CpcGetEnergyManagementDataHandler),
        )
        self.urihandler = UriHandler(self.uris)

    @pytest.mark.parametrize(
        "cpc_uri, energy_props",
        [
            ('/api/cpcs/1', {
                'cpc-power-consumption': 14423,
                'cpc-power-rating': 28000,
                'cpc-power-save-allowed': 'allowed',
                'cpc-power-saving': 'high-performance',
                'cpc-power-saving-state': 'high-performance',
                'zcpc-ambient-temperature': 26.7,
                'zcpc-dew-point': 8.4,
                'zcpc-exhaust-temperature': 29.0,
                'zcpc-heat-load': 49246,
                'zcpc-heat-load-forced-air': 10370,
                'zcpc-heat-load-water': 38877,
                'zcpc-humidity': 31,
                'zcpc-maximum-potential-heat-load': 57922,
                'zcpc-maximum-potential-power': 16964,
                'zcpc-power-consumption': 14423,
                'zcpc-power-rating': 28000,
                'zcpc-power-save-allowed': 'under-group-control',
                'zcpc-power-saving': 'high-performance',
                'zcpc-power-saving-state': 'high-performance',
            }),
        ]
    )
    def test_cpc_get_energymgmtdata(self, cpc_uri, energy_props):
        """
        Test GET CPC energy-management-data.
        """

        # Setup the energy properties of the CPC
        self.urihandler.post(self.hmc, cpc_uri, energy_props, True, True)

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc, cpc_uri + '/operations/energy-management-data', True)

        em_objs = resp['objects']
        assert len(em_objs) == 1

        cpc_data = em_objs[0]
        assert cpc_data['object-uri'] == cpc_uri
        assert cpc_data['object-id'] in cpc_uri
        assert cpc_data['class'] == 'cpcs'
        assert cpc_data['error-occurred'] is False

        act_energy_props = cpc_data['properties']
        for p in energy_props:
            exp_value = energy_props[p]

            assert p in act_energy_props
            assert act_energy_props[p] == exp_value


class TestCpcStartStopHandler:
    """
    All tests for classes CpcStartHandler and CpcStopHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CpcStartHandler and CpcStopHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/start', CpcStartHandler),
            (r'/api/cpcs/([^/]+)/operations/stop', CpcStopHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cpc_stop_classic(self):
        """
        Test POST CPC stop, for a CPC in classic mode.
        """

        # CPC1 is in classic mode
        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['status'] == 'operating'

        # the function to be tested:
        with pytest.raises(CpcNotInDpmError):
            self.urihandler.post(self.hmc, '/api/cpcs/1/operations/stop',
                                 None, True, True)

        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['status'] == 'operating'

    def test_cpc_start_classic(self):
        """
        Test POST CPC start, for a CPC in classic mode.
        """

        # CPC1 is in classic mode
        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['status'] == 'operating'

        # the function to be tested:
        with pytest.raises(CpcNotInDpmError):
            self.urihandler.post(self.hmc, '/api/cpcs/1/operations/start',
                                 None, True, True)

        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['status'] == 'operating'

    def test_cpc_stop_start_dpm(self):
        """
        Test POST CPC stop and start, for a CPC in DPM mode.
        """

        # CPC2 is in DPM mode
        cpc2 = self.urihandler.get(self.hmc, '/api/cpcs/2', True)
        assert cpc2['status'] == 'active'

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/cpcs/2/operations/stop',
                             None, True, True)

        cpc2 = self.urihandler.get(self.hmc, '/api/cpcs/2', True)
        assert cpc2['status'] == 'not-operating'

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/cpcs/2/operations/start',
                             None, True, True)

        cpc2 = self.urihandler.get(self.hmc, '/api/cpcs/2', True)
        assert cpc2['status'] == 'active'


class TestCpcActivateDeactivateHandler:
    """
    All tests for classes CpcActivateHandler and CpcDeactivateHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CpcActivateHandler and CpcDeactivateHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/activate', CpcActivateHandler),
            (r'/api/cpcs/([^/]+)/operations/deactivate', CpcDeactivateHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cpc_deactivate_dpm(self):
        """
        Test POST CPC deactivate, for a CPC in DPM mode.
        """

        # CPC2 is in DPM mode
        cpc2 = self.urihandler.get(self.hmc, '/api/cpcs/2', True)
        assert cpc2['status'] == 'active'

        # the function to be tested:
        with pytest.raises(CpcInDpmError):
            body = {'force': True}
            self.urihandler.post(self.hmc, '/api/cpcs/2/operations/deactivate',
                                 body, True, True)

        cpc2 = self.urihandler.get(self.hmc, '/api/cpcs/2', True)
        assert cpc2['status'] == 'active'

    def test_cpc_activate_dpm(self):
        """
        Test POST CPC start, for a CPC in DPM mode.
        """

        # CPC2 is in DPM mode
        cpc2 = self.urihandler.get(self.hmc, '/api/cpcs/2', True)
        assert cpc2['status'] == 'active'

        # the function to be tested:
        with pytest.raises(CpcInDpmError):
            body = {'activation-profile-name': 'faked-rp', 'force': False}
            self.urihandler.post(self.hmc, '/api/cpcs/2/operations/activate',
                                 body, True, True)

        cpc2 = self.urihandler.get(self.hmc, '/api/cpcs/2', True)
        assert cpc2['status'] == 'active'

    def test_cpc_deactivate_activate_classic(self):
        """
        Test POST CPC deactivate and activate, for a CPC in classic mode.
        """

        # CPC1 is in classic mode
        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['status'] == 'operating'

        # the function to be tested:
        body = {'force': True}
        self.urihandler.post(self.hmc, '/api/cpcs/1/operations/deactivate',
                             body, True, True)

        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['status'] == 'no-power'

        # the function to be tested:
        body = {'activation-profile-name': 'faked-rp', 'force': False}
        self.urihandler.post(self.hmc, '/api/cpcs/1/operations/activate',
                             body, True, True)

        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['status'] == 'operating'


class TestCpcExportPortNamesListHandler:
    """
    All tests for class CpcExportPortNamesListHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CpcExportPortNamesListHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs(?:\?(.*))?', CpcsHandler),
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/export-port-names-list',
             CpcExportPortNamesListHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cpc_export_pnl_err_no_input(self):
        """
        Test POST CPC export-port-names-list, without providing input.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/cpcs/2/operations/export-port-names-list',
                None, True, True)

    def test_cpc_export_pnl(self):
        """
        Test POST CPC export-port-names-list.
        """

        operation_body = {
            'partitions': [
                '/api/partitions/1',
            ]
        }
        exp_wwpn_list = [
            'partition_1,CEF,1001,CFFEAFFE00008001',
        ]

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/cpcs/2/operations/export-port-names-list',
            operation_body, True, True)

        assert len(resp) == 1
        assert 'wwpn-list' in resp
        wwpn_list = resp['wwpn-list']
        assert wwpn_list == exp_wwpn_list


class TestCpcImportProfilesHandler:
    """
    All tests for class CpcImportProfilesHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CpcImportProfilesHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs(?:\?(.*))?', CpcsHandler),
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/import-profiles',
             CpcImportProfilesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cpc_import_profiles_err_no_input(self):
        """
        Test POST CPC import-profiles, without providing input.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/cpcs/1/operations/import-profiles',
                None, True, True)

    def test_cpc_import_profiles(self):
        """
        Test POST CPC import-profiles.
        """

        operation_body = {
            'profile-area': 2,
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/cpcs/1/operations/import-profiles',
            operation_body, True, True)

        assert resp is None


class TestCpcExportProfilesHandler:
    """
    All tests for class CpcExportProfilesHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CpcExportProfilesHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs(?:\?(.*))?', CpcsHandler),
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/export-profiles',
             CpcExportProfilesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cpc_export_profiles_err_no_input(self):
        """
        Test POST CPC export-profiles, without providing input.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/cpcs/1/operations/export-profiles',
                None, True, True)

    def test_cpc_export_profiles(self):
        """
        Test POST CPC export-profiles.
        """

        operation_body = {
            'profile-area': 2,
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/cpcs/1/operations/export-profiles',
            operation_body, True, True)

        assert resp is None


class TestCpcSetAutoStartListHandler:
    """
    All tests for class CpcSetAutoStartListHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CpcSetAutoStartListHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs(?:\?(.*))?', CpcsHandler),
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/set-auto-start-list',
             CpcSetAutoStartListHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cpc_set_auto_start_list(self):
        """
        Test POST CPC set-auto-start-list.
        """

        operation_body = {
            'auto-start-list': [
                {
                    'type': 'partition',
                    'partition-uri': '/api/partitions/part-A-oid',
                    'post-start-delay': 10,
                },
            ]
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/cpcs/2/operations/set-auto-start-list',
            operation_body, True, True)

        assert resp is None


class TestMetricsContextHandlers:
    """
    All tests for classes MetricsContextsHandler and MetricsContextHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        MetricsContextsHandler and MetricsContextHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/services/metrics/context', MetricsContextsHandler),
            (r'/api/services/metrics/context/([^/]+)', MetricsContextHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_mc_create_get_delete(self):
        """
        Test POST metrics context (create), followed by get and delete.
        """

        faked_hmc = self.hmc

        # Prepare faked metric group definitions

        mg_name = 'partition-usage'
        mg_def = faked_hmc.metric_groups[mg_name]
        mg_info = {
            'group-name': mg_name,
            'metric-infos': [
                {'metric-name': t[0], 'metric-type': t[1]}
                for t in mg_def.types
            ],
        }

        mg_name2 = 'dpm-system-usage-overview'
        mg_def2 = faked_hmc.metric_groups[mg_name2]
        mg_info2 = {
            'group-name': mg_name2,
            'metric-infos': [
                {'metric-name': t[0], 'metric-type': t[1]}
                for t in mg_def2.types
            ],
        }

        # Prepare faked metric values

        ts1_input = datetime(2017, 9, 5, 12, 13, 10, 0, pytz.utc)
        ts1_exp = 1504613590000
        mo_val1_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid',
            timestamp=ts1_input,
            values=[
                ('processor-usage', 10),
                ('network-usage', 5),
            ])
        faked_hmc.add_metric_values(mo_val1_input)

        ts2_tz = pytz.timezone('CET')
        ts2_input = datetime(2017, 9, 5, 12, 13, 20, 0, ts2_tz)
        ts2_offset = int(ts2_tz.utcoffset(ts2_input).total_seconds())
        ts2_exp = 1504613600000 - 1000 * ts2_offset
        mo_val2_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid',
            timestamp=ts2_input,
            values=[
                ('processor-usage', 12),
                ('network-usage', 3),
            ])
        faked_hmc.add_metric_values(mo_val2_input)

        ts3_input = datetime(2017, 9, 5, 12, 13, 30, 0)  # timezone-naive
        ts3_offset = int(tz.tzlocal().utcoffset(ts3_input).total_seconds())
        ts3_exp = 1504613610000 - 1000 * ts3_offset
        mo_val3_input = FakedMetricObjectValues(
            group_name=mg_name2,
            resource_uri='/api/cpcs/fake-oid',
            timestamp=ts3_input,
            values=[
                ('processor-usage', 50),
                ('network-usage', 20),
            ])
        faked_hmc.add_metric_values(mo_val3_input)

        body = {
            'anticipated-frequency-seconds': '10',
            'metric-groups': [mg_name, mg_name2],
        }

        # the create function to be tested:
        resp = self.urihandler.post(self.hmc, '/api/services/metrics/context',
                                    body, True, True)

        assert isinstance(resp, dict)
        assert 'metrics-context-uri' in resp
        uri = resp['metrics-context-uri']
        assert uri.startswith('/api/services/metrics/context/')
        assert 'metric-group-infos' in resp
        mg_infos = resp['metric-group-infos']
        assert mg_infos == [mg_info, mg_info2]

        # the get function to be tested:
        mv_resp = self.urihandler.get(self.hmc, uri, True)

        exp_mv_resp = f'''"partition-usage"
"/api/partitions/fake-oid"
{ts1_exp}
10,5

"/api/partitions/fake-oid"
{ts2_exp}
12,3


"dpm-system-usage-overview"
"/api/cpcs/fake-oid"
{ts3_exp}
50,20



'''

        assert mv_resp == exp_mv_resp, (
            f"Actual response string:\n{mv_resp!r}\n"
            f"Expected response string:\n{exp_mv_resp!r}\n")

        # the delete function to be tested:
        self.urihandler.delete(self.hmc, uri, True)


class TestAdapterHandlers:
    """
    All tests for classes AdaptersHandler and AdapterHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        AdaptersHandler and AdapterHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/adapters(?:\?(.*))?', AdaptersHandler),
            (r'/api/adapters/([^/]+)', AdapterHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_adapter_list(self):
        """
        Test GET adapters (list).
        """

        # the function to be tested:
        adapters = self.urihandler.get(self.hmc, '/api/cpcs/2/adapters', True)

        exp_adapters = {  # properties reduced to those returned by List
            'adapters': [
                {
                    'object-uri': '/api/adapters/1',
                    'name': 'osa_1',
                    'status': 'active',
                    'adapter-family': 'osa',
                    'adapter-id': 'BEF',
                    'type': 'osd',
                },
                {
                    'object-uri': '/api/adapters/2',
                    'name': 'fcp_2',
                    'status': 'active',
                    'adapter-family': 'ficon',
                    'adapter-id': 'CEF',
                    'type': 'fcp',
                },
                {
                    'object-uri': '/api/adapters/2a',
                    'name': 'fcp_2a',
                    'status': 'active',
                    'adapter-family': 'ficon',
                    'adapter-id': 'CEE',
                    'type': 'fcp',
                },
                {
                    'object-uri': '/api/adapters/3',
                    'name': 'roce_3',
                    'status': 'active',
                    'adapter-family': 'roce',
                    'adapter-id': 'DEF',
                    'type': 'roce',
                },
                {
                    'object-uri': '/api/adapters/4',
                    'name': 'crypto_4',
                    'status': 'active',
                    'adapter-family': 'crypto',
                    'adapter-id': 'EEF',
                    'type': 'crypto',
                },
                {
                    'object-uri': '/api/adapters/5',
                    'name': 'zedc_5',
                    'status': 'active',
                    'adapter-family': 'accelerator',
                    'adapter-id': 'FEF',
                    'type': 'zedc',
                },
            ]
        }
        assert adapters == exp_adapters

    def test_adapter_get(self):
        """
        Test GET adapter.
        """

        # the function to be tested:
        adapter1 = self.urihandler.get(self.hmc, '/api/adapters/1', True)

        exp_adapter1 = {
            'object-id': '1',
            'object-uri': '/api/adapters/1',
            'class': 'adapter',
            'parent': '/api/cpcs/2',
            'name': 'osa_1',
            'description': 'OSA #1 in CPC #2',
            'status': 'active',
            'adapter-family': 'osa',
            'network-port-uris': ['/api/adapters/1/network-ports/1'],
            'adapter-id': 'BEF',
            'type': 'osd',
        }
        assert adapter1 == exp_adapter1

    def test_adapter_update_verify(self):
        """
        Test POST adapter (update).
        """

        update_adapter1 = {
            'description': 'updated adapter #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/adapters/1',
                             update_adapter1, True, True)

        adapter1 = self.urihandler.get(self.hmc, '/api/adapters/1', True)
        assert adapter1['description'] == 'updated adapter #1'


class TestAdapterChangeCryptoTypeHandler:
    """
    All tests for class AdapterChangeCryptoTypeHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        AdapterChangeCryptoTypeHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/adapters(?:\?(.*))?', AdaptersHandler),
            (r'/api/adapters/([^/]+)', AdapterHandler),
            (r'/api/adapters/([^/]+)/operations/change-crypto-type',
             AdapterChangeCryptoTypeHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_adapter_cct_err_no_body(self):
        """
        Test POST adapter change-crypto-type, with missing request body.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/adapters/4/operations/change-crypto-type',
                None, True, True)

    def test_adapter_cct_err_no_crypto_type(self):
        """
        Test POST adapter change-crypto-type, with missing 'crypto-type' field
        in request body.
        """

        operation_body = {
            # no 'crypto-type' field
        }

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/adapters/4/operations/change-crypto-type',
                operation_body, True, True)

    def test_adapter_cct(self):
        """
        Test POST adapter change-crypto-type, successful.
        """

        operation_body = {
            'crypto-type': 'cca-coprocessor',
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc,
            '/api/adapters/4/operations/change-crypto-type',
            operation_body, True, True)

        assert resp is None


class TestAdapterChangeAdapterTypeHandler:
    """
    All tests for class AdapterChangeAdapterTypeHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        AdapterChangeCryptoTypeHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/adapters(?:\?(.*))?', AdaptersHandler),
            (r'/api/adapters/([^/]+)', AdapterHandler),
            (r'/api/adapters/([^/]+)/operations/change-adapter-type',
             AdapterChangeAdapterTypeHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_adapter_cat_err_no_body(self):
        """
        Test POST adapter change-adapter-type, with missing request body.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/adapters/2/operations/change-adapter-type',
                None, True, True)

    def test_adapter_cat_err_no_type(self):
        """
        Test POST adapter change-adapter-type, with missing 'type' field in
        request body.
        """

        operation_body = {
            # no 'type' field
        }

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/adapters/2/operations/change-adapter-type',
                operation_body, True, True)

    def test_adapter_cat(self):
        """
        Test POST adapter change-adapter-type, successful.
        """

        operation_body = {
            'type': 'fc',
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc,
            '/api/adapters/2/operations/change-adapter-type',
            operation_body, True, True)

        assert resp is None


class TestAdapterGetAssignedPartitionsHandler:
    """
    All tests for class AdapterGetAssignedPartitionsHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        AdapterGetAssignedPartitionsHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/adapters(?:\?(.*))?', AdaptersHandler),
            (r'/api/adapters/([^/]+)', AdapterHandler),
            (r'/api/adapters/([^/]+)/operations/'
             r'get-partitions-assigned-to-adapter(?:\?(.*))?',
             AdapterGetAssignedPartitionsHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_adapter_part_nic_nofilter(self):
        """
        Test network adapter without filters, successful.
        """

        exp_partition_uri = '/api/partitions/1'
        exp_partition_name = 'partition_1'
        exp_partition_status = 'stopped'

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc,
            '/api/adapters/3/operations/get-partitions-assigned-to-adapter',
            True)

        partition_infos = resp['partitions-assigned-to-adapter']
        assert len(partition_infos) == 1

        part1_info = partition_infos[0]
        assert part1_info['object-uri'] == exp_partition_uri
        assert part1_info['name'] == exp_partition_name
        assert part1_info['status'] == exp_partition_status

    def test_adapter_part_nic_match_name(self):
        """
        Test network adapter with matching 'name' filter, successful.
        """

        exp_partition_uri = '/api/partitions/1'
        exp_partition_name = 'partition_1'
        exp_partition_status = 'stopped'

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc,
            '/api/adapters/3/operations/get-partitions-assigned-to-adapter'
            f'?name={exp_partition_name}',
            True)

        partition_infos = resp['partitions-assigned-to-adapter']
        assert len(partition_infos) == 1

        part1_info = partition_infos[0]
        assert part1_info['object-uri'] == exp_partition_uri
        assert part1_info['name'] == exp_partition_name
        assert part1_info['status'] == exp_partition_status

    def test_adapter_part_nic_nomatch_name(self):
        """
        Test network adapter with non-matching 'name' filter, successful.
        """

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc,
            '/api/adapters/3/operations/get-partitions-assigned-to-adapter'
            '?name=foo',
            True)

        partition_infos = resp['partitions-assigned-to-adapter']
        assert len(partition_infos) == 0

    def test_adapter_part_nic_match_status(self):
        """
        Test network adapter with matching 'status' filter, successful.
        """

        exp_partition_uri = '/api/partitions/1'
        exp_partition_name = 'partition_1'
        exp_partition_status = 'stopped'

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc,
            '/api/adapters/3/operations/get-partitions-assigned-to-adapter'
            f'?status={exp_partition_status}',
            True)

        partition_infos = resp['partitions-assigned-to-adapter']
        assert len(partition_infos) == 1

        part1_info = partition_infos[0]
        assert part1_info['object-uri'] == exp_partition_uri
        assert part1_info['name'] == exp_partition_name
        assert part1_info['status'] == exp_partition_status

    def test_adapter_part_nic_nomatch_status(self):
        """
        Test network adapter with non-matching 'status' filter, successful.
        """

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc,
            '/api/adapters/3/operations/get-partitions-assigned-to-adapter'
            '?status=active',
            True)

        partition_infos = resp['partitions-assigned-to-adapter']
        assert len(partition_infos) == 0

    def xtest_adapter_part_ficon_nofilter(self):
        # TODO: Enable test again when FakedStorageGroup supports VSRs
        """
        Test FICON adapter without filters, successful.
        """

        exp_partition_uri = '/api/partitions/1'
        exp_partition_name = 'partition_1'
        exp_partition_status = 'stopped'

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc,
            '/api/adapters/2/operations/get-partitions-assigned-to-adapter',
            True)

        partition_infos = resp['partitions-assigned-to-adapter']
        assert len(partition_infos) == 1

        part1_info = partition_infos[0]
        assert part1_info['object-uri'] == exp_partition_uri
        assert part1_info['name'] == exp_partition_name
        assert part1_info['status'] == exp_partition_status

    def test_adapter_part_crypto_nofilter(self):
        """
        Test crypto adapter without filters, successful.
        """

        exp_partition_uri = '/api/partitions/1'
        exp_partition_name = 'partition_1'
        exp_partition_status = 'stopped'

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc,
            '/api/adapters/4/operations/get-partitions-assigned-to-adapter',
            True)

        partition_infos = resp['partitions-assigned-to-adapter']
        assert len(partition_infos) == 1

        part1_info = partition_infos[0]
        assert part1_info['object-uri'] == exp_partition_uri
        assert part1_info['name'] == exp_partition_name
        assert part1_info['status'] == exp_partition_status

    def test_adapter_part_accel_nofilter(self):
        """
        Test accelerator adapter without filters, successful.
        """

        exp_partition_uri = '/api/partitions/1'
        exp_partition_name = 'partition_1'
        exp_partition_status = 'stopped'

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc,
            '/api/adapters/5/operations/get-partitions-assigned-to-adapter',
            True)

        partition_infos = resp['partitions-assigned-to-adapter']
        assert len(partition_infos) == 1

        part1_info = partition_infos[0]
        assert part1_info['object-uri'] == exp_partition_uri
        assert part1_info['name'] == exp_partition_name
        assert part1_info['status'] == exp_partition_status


class TestNetworkPortHandlers:
    """
    All tests for class NetworkPortHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        NetworkPortHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/adapters/([^/]+)/network-ports/([^/]+)',
             NetworkPortHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_netport_get(self):
        """
        Test GET network adapter port.
        """

        # the function to be tested:
        port1 = self.urihandler.get(self.hmc,
                                    '/api/adapters/1/network-ports/1', True)

        exp_port1 = {
            'element-id': '1',
            'element-uri': '/api/adapters/1/network-ports/1',
            'class': 'network-port',
            'parent': '/api/adapters/1',
            'name': 'osa_1_port_1',
            'description': 'Port #1 of OSA #1',
        }
        assert port1 == exp_port1

    def test_netport_update_verify(self):
        """
        Test POST network adapter port (update).
        """

        update_port1 = {
            'description': 'updated port #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/adapters/1/network-ports/1',
                             update_port1, True, True)

        port1 = self.urihandler.get(self.hmc,
                                    '/api/adapters/1/network-ports/1', True)
        assert port1['description'] == 'updated port #1'


class TestStoragePortHandlers:
    """
    All tests for class StoragePortHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        StoragePortHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/adapters/([^/]+)/storage-ports/([^/]+)',
             StoragePortHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_stoport_get(self):
        """
        Test GET storage adapter port.
        """

        # the function to be tested:
        port1 = self.urihandler.get(self.hmc,
                                    '/api/adapters/2/storage-ports/1', True)

        exp_port1 = {
            'element-id': '1',
            'element-uri': '/api/adapters/2/storage-ports/1',
            'class': 'storage-port',
            'parent': '/api/adapters/2',
            'name': 'fcp_2_port_1',
            'description': 'Port #1 of FCP #2',
        }
        assert port1 == exp_port1

    def test_stoport_update_verify(self):
        """
        Test POST storage adapter port (update).
        """

        update_port1 = {
            'description': 'updated port #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/adapters/2/storage-ports/1',
                             update_port1, True, True)

        port1 = self.urihandler.get(self.hmc,
                                    '/api/adapters/2/storage-ports/1', True)
        assert port1['description'] == 'updated port #1'


class TestPartitionHandlers:
    """
    All tests for classes PartitionsHandler and PartitionHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        PartitionsHandler and PartitionHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/partitions(?:\?(.*))?', PartitionsHandler),
            (r'/api/partitions/([^/]+)', PartitionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_part_list(self):
        """
        Test GET partitions (list).
        """

        # the function to be tested:
        partitions = self.urihandler.get(self.hmc, '/api/cpcs/2/partitions',
                                         True)

        exp_partitions = {  # properties reduced to those returned by List
            'partitions': [
                {
                    'object-uri': '/api/partitions/1',
                    'name': 'partition_1',
                    'status': 'stopped',
                    'type': 'linux',
                },
            ]
        }
        assert partitions == exp_partitions

    def test_part_get(self):
        """
        Test GET partition.
        """

        # the function to be tested:
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)

        exp_partition1 = {
            'object-id': '1',
            'object-uri': '/api/partitions/1',
            'class': 'partition',
            'parent': '/api/cpcs/2',
            'name': 'partition_1',
            'description': 'Partition #1 in CPC #2',
            'status': 'stopped',
            'type': 'linux',
            'hba-uris': ['/api/partitions/1/hbas/1'],
            'nic-uris': ['/api/partitions/1/nics/1'],
            'virtual-function-uris': ['/api/partitions/1/virtual-functions/1'],
            'partition-link-uris': [],
            'storage-group-uris': [],
            'tape-link-uris': [],
            'crypto-configuration': {
                'crypto-adapter-uris': [
                    '/api/adapters/4',
                ],
                'crypto-domain-configurations': [
                    {
                        'access-mode': 'control-usage',
                        'domain-index': 0,
                    },
                ],
            },
        }
        assert partition1 == exp_partition1

    def test_part_create_verify(self):
        """
        Test POST partitions (create).
        """

        new_partition2 = {
            'object-id': '2',
            'name': 'partition_2',
            'ifl-processors': 2,
            'initial-memory': 1024,
            'maximum-memory': 2048,
        }

        # the function to be tested:
        resp = self.urihandler.post(self.hmc, '/api/cpcs/2/partitions',
                                    new_partition2, True, True)

        assert len(resp) == 1
        assert 'object-uri' in resp
        new_partition2_uri = resp['object-uri']
        assert new_partition2_uri == '/api/partitions/2'

        exp_partition2 = {
            'object-id': '2',
            'object-uri': '/api/partitions/2',
            'class': 'partition',
            'parent': '/api/cpcs/2',
            'name': 'partition_2',
            'status': 'stopped',
            'hba-uris': [],
            'nic-uris': [],
            'virtual-function-uris': [],
            'initial-memory': 1024,
            'maximum-memory': 2048,
        }

        # the function to be tested:
        partition2 = self.urihandler.get(self.hmc, '/api/partitions/2', True)

        for pname, exp_value in exp_partition2.items():
            assert pname in partition2
            act_value = partition2[pname]
            assert act_value == exp_value, \
                f"property {pname!r}"

    def test_part_update_verify(self):
        """
        Test POST partition (update).
        """

        update_partition1 = {
            'description': 'updated partition #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/partitions/1',
                             update_partition1, True, True)

        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        assert partition1['description'] == 'updated partition #1'

    def test_part_delete_verify(self):
        """
        Test DELETE partition.
        """

        self.urihandler.get(self.hmc, '/api/partitions/1', True)

        # the function to be tested:
        self.urihandler.delete(self.hmc, '/api/partitions/1', True)

        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc, '/api/partitions/1', True)


class TestPartitionStartStopHandler:
    """
    All tests for classes PartitionStartHandler and PartitionStopHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        PartitionStartHandler and PartitionStopHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/start',
             PartitionStartHandler),
            (r'/api/partitions/([^/]+)/operations/stop', PartitionStopHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_part_start_stop(self):
        """
        Test POST partition start and stop.
        """

        # CPC2 is in DPM mode
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        assert partition1['status'] == 'stopped'

        # the start() function to be tested, with a valid initial status:
        self.urihandler.post(self.hmc, '/api/partitions/1/operations/start',
                             None, True, True)
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        assert partition1['status'] == 'active'

        # the start() function to be tested, with an invalid initial status:
        with pytest.raises(HTTPError):
            self.urihandler.post(self.hmc,
                                 '/api/partitions/1/operations/start',
                                 None, True, True)

        # the stop() function to be tested, with a valid initial status:
        assert partition1['status'] == 'active'
        self.urihandler.post(self.hmc, '/api/partitions/1/operations/stop',
                             None, True, True)
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        assert partition1['status'] == 'stopped'

        # the stop() function to be tested, with an invalid initial status:
        with pytest.raises(HTTPError):
            self.urihandler.post(self.hmc,
                                 '/api/partitions/1/operations/stop',
                                 None, True, True)


class TestPartitionScsiDumpHandler:
    """
    All tests for class PartitionScsiDumpHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        PartitionScsiDumpHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/scsi-dump',
             PartitionScsiDumpHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_part_scsidump_err_no_body(self):
        """
        Test POST partition scsi-dump, with missing request body.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/scsi-dump',
                None, True, True)

    def test_part_scsidump_err_missing_fields_1(self):
        """
        Test POST partition scsi-dump, with missing 'dump-load-hba-uri' field
        in request body.
        """

        operation_body = {
            # missing: 'dump-load-hba-uri'
            'dump-world-wide-port-name': 'fake-wwpn',
            'dump-logical-unit-number': 'fake-lun',
        }

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/scsi-dump',
                operation_body, True, True)

    def test_part_scsidump_err_missing_fields_2(self):
        """
        Test POST partition scsi-dump, with missing 'dump-world-wide-port-name'
        field in request body.
        """

        operation_body = {
            'dump-load-hba-uri': 'fake-uri',
            # missing: 'dump-world-wide-port-name'
            'dump-logical-unit-number': 'fake-lun',
        }

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/scsi-dump',
                operation_body, True, True)

    def test_part_scsidump_err_missing_fields_3(self):
        """
        Test POST partition scsi-dump, with missing 'dump-logical-unit-number'
        field in request body.
        """

        operation_body = {
            'dump-load-hba-uri': 'fake-uri',
            'dump-world-wide-port-name': 'fake-wwpn',
            # missing: 'dump-logical-unit-number'
        }

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/scsi-dump',
                operation_body, True, True)

    def test_part_scsidump_err_status(self):
        """
        Test POST partition scsi-dump, with partition in invalid status
        'stopped'.
        """

        operation_body = {
            'dump-load-hba-uri': 'fake-uri',
            'dump-world-wide-port-name': 'fake-wwpn',
            'dump-logical-unit-number': 'fake-lun',
        }

        # Set the partition status to an invalid status for this operation

        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'stopped'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/scsi-dump',
                operation_body, True, True)

    def test_part_scsidump(self):
        """
        Test POST partition scsi-dump, successful.
        """

        operation_body = {
            'dump-load-hba-uri': 'fake-uri',
            'dump-world-wide-port-name': 'fake-wwpn',
            'dump-logical-unit-number': 'fake-lun',
        }

        # Set the partition status to a valid status for this operation
        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'active'

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/partitions/1/operations/scsi-dump',
            operation_body, True, True)

        assert resp == {}


class TestPartitionStartDumpProgramHandler:
    """
    All tests for class PartitionStartDumpProgramHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        PartitionStartDumpProgramHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/start-dump-program',
             PartitionStartDumpProgramHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_part_dumpprog_err_no_body(self):
        """
        Test POST partition start-dump-program, with missing request body.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/start-dump-program',
                None, True, True)

    def test_part_dumpprog_err_missing_fields_1(self):
        """
        Test POST partition start-dump-program, with missing
        'dump-program-info' and 'dump-program-type' fields in request body.
        """

        operation_body = {
            # missing: 'dump-program-info'
            # missing: 'dump-program-type'
        }

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/start-dump-program',
                operation_body, True, True)

    def test_part_dumpprog_err_status(self):
        """
        Test POST partition start-dump-program, with partition in invalid
        status 'stopped'.
        """

        operation_body = {
            'dump-program-type': 'storage',
            'dump-program-info': {
                'storage-volume-uri': 'sv1'  # dummy
            },
        }

        # Set the partition status to an invalid status for this operation
        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'stopped'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/start-dump-program',
                operation_body, True, True)

    def test_part_scsidump(self):
        """
        Test POST partition scsi-dump, successful.
        """

        operation_body = {
            'dump-program-type': 'storage',
            'dump-program-info': {
                'storage-volume-uri': 'sv1'  # dummy
            },
        }

        # Set the partition status to a valid status for this operation
        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'active'

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/partitions/1/operations/start-dump-program',
            operation_body, True, True)

        assert resp == {}


class TestPartitionPswRestartHandler:
    """
    All tests for class PartitionPswRestartHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        PartitionPswRestartHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/psw-restart',
             PartitionPswRestartHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_part_pswrestart_err_status(self):
        """
        Test POST partition psw-restart, with partition in invalid status
        'stopped'.
        """

        # Set the partition status to an invalid status for this operation
        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'stopped'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/psw-restart',
                None, True, True)

    def test_part_pswrestart(self):
        """
        Test POST partition psw-restart, successful.
        """

        # Set the partition status to a valid status for this operation
        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'active'

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/partitions/1/operations/psw-restart',
            None, True, True)

        assert resp == {}


class TestPartitionMountIsoImageHandler:
    """
    All tests for class PartitionMountIsoImageHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        PartitionMountIsoImageHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/mount-iso-image(?:\?(.*))?',
             PartitionMountIsoImageHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_part_mountiso_err_queryparm_1(self):
        """
        Test POST partition mount-iso-image, with invalid query parameter
        'image-namex'.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/mount-iso-image?'
                'image-namex=fake-image&ins-file-name=fake-ins',
                None, True, True)

    def test_part_mountiso_err_queryparm_2(self):
        """
        Test POST partition mount-iso-image, with invalid query parameter
        'ins-file-namex'.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/mount-iso-image?'
                'image-name=fake-image&ins-file-namex=fake-ins',
                None, True, True)

    def test_part_mountiso_err_status(self):
        """
        Test POST partition mount-iso-image, with invalid partition status.
        """

        # Set the partition status to an invalid status for this operation
        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'starting'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/mount-iso-image?'
                'image-name=fake-image&ins-file-name=fake-ins',
                None, True, True)

    def test_part_mountiso(self):
        """
        Test POST partition mount-iso-image, successful.
        """

        # Set the partition status to a valid status for this operation
        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'active'

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/partitions/1/operations/mount-iso-image?'
            'image-name=fake-image&ins-file-name=fake-ins',
            None, True, True)

        assert resp == {}

        boot_iso_image_name = partition1.properties['boot-iso-image-name']
        assert boot_iso_image_name == 'fake-image'

        boot_iso_ins_file = partition1.properties['boot-iso-ins-file']
        assert boot_iso_ins_file == 'fake-ins'


class TestPartitionUnmountIsoImageHandler:
    """
    All tests for class PartitionUnmountIsoImageHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        PartitionUnmountIsoImageHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/unmount-iso-image',
             PartitionUnmountIsoImageHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_part_unmountiso_err_status(self):
        """
        Test POST partition unmount-iso-image, with invalid partition status.
        """

        # Set the partition status to an invalid status for this operation
        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'starting'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/unmount-iso-image',
                None, True, True)

    def test_part_unmountiso(self):
        """
        Test POST partition unmount-iso-image, successful.
        """

        # Set the partition status to a valid status for this operation
        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'active'

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/partitions/1/operations/unmount-iso-image',
            None, True, True)

        assert resp == {}

        boot_iso_image_name = partition1.properties['boot-iso-image-name']
        assert boot_iso_image_name is None

        boot_iso_ins_file = partition1.properties['boot-iso-ins-file']
        assert boot_iso_ins_file is None


class TestPartitionIncreaseCryptoConfigHandler:
    """
    All tests for class PartitionIncreaseCryptoConfigHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        PartitionIncreaseCryptoConfigHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/'
             'increase-crypto-configuration',
             PartitionIncreaseCryptoConfigHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_part_icc_err_missing_body(self):
        """
        Test POST partition increase-crypto-configuration, with missing
        request body.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/increase-crypto-configuration',
                None, True, True)

    def test_part_icc_err_status(self):
        """
        Test POST partition increase-crypto-configuration, with invalid status
        of partition.
        """

        # Set the partition status to an invalid status for this operation
        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'starting'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/increase-crypto-configuration',
                {}, True, True)

    def test_part_icc(self):
        """
        Test POST partition increase-crypto-configuration, successful.
        """

        testcases = [
            # (input_adapter_uris, input_domain_configs)
            # TODO: Change testcases to allow for different initial states
            (None,
             None),
            (None,
             [{'domain-index': 17, 'access-mode': 'control-usage'},
              {'domain-index': 18, 'access-mode': 'control-usage'}]),
            (['fake-uri1', 'fake-uri2'],
             None),
            ([],
             []),
            ([],
             [{'domain-index': 17, 'access-mode': 'control-usage'},
              {'domain-index': 18, 'access-mode': 'control-usage'}]),
            (['fake-uri1', 'fake-uri2'],
             []),
            (['fake-uri1', 'fake-uri2'],
             [{'domain-index': 17, 'access-mode': 'control-usage'},
              {'domain-index': 18, 'access-mode': 'control-usage'}]),
        ]

        for tc in testcases:

            input_adapter_uris = tc[0]
            input_domain_configs = tc[1]

            operation_body = {}
            if input_adapter_uris is not None:
                operation_body['crypto-adapter-uris'] = input_adapter_uris
            if input_domain_configs is not None:
                operation_body['crypto-domain-configurations'] = \
                    input_domain_configs

            # Set the partition status to a valid status for this operation
            partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
            partition1.properties['status'] = 'active'

            # Set up the initial partition config
            partition1.properties['crypto-configuration'] = None

            # the function to be tested:
            resp = self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/increase-crypto-configuration',
                operation_body, True, True)

            assert resp is None

            crypto_config = partition1.properties['crypto-configuration']
            assert isinstance(crypto_config, dict)

            adapter_uris = crypto_config['crypto-adapter-uris']
            assert isinstance(adapter_uris, list)
            exp_adapter_uris = input_adapter_uris \
                if input_adapter_uris is not None else []
            assert adapter_uris == exp_adapter_uris

            domain_configs = crypto_config['crypto-domain-configurations']
            assert isinstance(domain_configs, list)
            exp_domain_configs = input_domain_configs \
                if input_domain_configs is not None else []
            assert domain_configs == exp_domain_configs


class TestPartitionDecreaseCryptoConfigHandler:
    """
    All tests for class PartitionDecreaseCryptoConfigHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        PartitionDecreaseCryptoConfigHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/'
             'decrease-crypto-configuration',
             PartitionDecreaseCryptoConfigHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_part_dcc_err_missing_body(self):
        """
        Test POST partition decrease-crypto-configuration, with missing
        request body.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/decrease-crypto-configuration',
                None, True, True)

    def test_part_dcc_err_status(self):
        """
        Test POST partition decrease-crypto-configuration, with invalid
        status of partition.
        """

        # Set the partition status to an invalid status for this operation
        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'starting'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/decrease-crypto-configuration',
                {}, True, True)

    def test_part_dcc(self):
        """
        Test POST partition decrease-crypto-configuration, successful.
        """

        testcases = [
            # (input_adapter_uris, input_domain_indexes)
            # TODO: Change testcases to allow for different initial states
            # TODO: Change testcases to allow for expected results
            (None,
             None),
            (None,
             [17, 18]),
            (['fake-uri1', 'fake-uri2'],
             None),
            ([],
             []),
            ([],
             [17, 18]),
            (['fake-uri1', 'fake-uri2'],
             []),
            (['fake-uri1', 'fake-uri2'],
             [17, 18]),
        ]

        for tc in testcases:

            input_adapter_uris = tc[0]
            input_domain_indexes = tc[1]

            operation_body = {}
            if input_adapter_uris is not None:
                operation_body['crypto-adapter-uris'] = input_adapter_uris
            if input_domain_indexes is not None:
                operation_body['crypto-domain-indexes'] = \
                    input_domain_indexes

            # Set the partition status to a valid status for this operation
            partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
            partition1.properties['status'] = 'active'

            # Set up the initial partition config
            partition1.properties['crypto-configuration'] = {
                'crypto-adapter-uris': ['fake-uri1', 'fake-uri2'],
                'crypto-domain-configurations': [
                    {'domain-index': 17,
                     'access-mode': 'control-usage'},
                    {'domain-index': 18,
                     'access-mode': 'control-usage'},
                ]
            }

            # the function to be tested:
            resp = self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/decrease-crypto-configuration',
                operation_body, True, True)

            assert resp is None

            crypto_config = partition1.properties['crypto-configuration']
            assert isinstance(crypto_config, dict)

            adapter_uris = crypto_config['crypto-adapter-uris']
            assert isinstance(adapter_uris, list)

            domain_configs = crypto_config['crypto-domain-configurations']
            assert isinstance(domain_configs, list)


class TestPartitionChangeCryptoConfigHandler:
    """
    All tests for class PartitionChangeCryptoConfigHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        PartitionChangeCryptoConfigHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/'
             'change-crypto-domain-configuration',
             PartitionChangeCryptoConfigHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_part_ccc_err_missing_body(self):
        """
        Test POST partition change-crypto-domain-configuration, with missing
        request body.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/'
                'change-crypto-domain-configuration',
                None, True, True)

    def test_part_ccc_err_missing_field_1(self):
        """
        Test POST partition change-crypto-domain-configuration, with missing
        'domain-index' field in request body.
        """

        operation_body = {
            # missing 'domain-index'
            'access-mode': 'control-usage',
        }

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/'
                'change-crypto-domain-configuration',
                operation_body, True, True)

    def test_part_ccc_err_missing_field_2(self):
        """
        Test POST partition change-crypto-domain-configuration, with missing
        'access-mode' field in request body.
        """

        operation_body = {
            'domain-index': 17,
            # missing 'access-mode'
        }

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/'
                'change-crypto-domain-configuration',
                operation_body, True, True)

    def test_part_ccc_err_status(self):
        """
        Test POST partition change-crypto-domain-configuration, with invalid
        status of partition.
        """

        # Set the partition status to an invalid status for this operation
        partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
        partition1.properties['status'] = 'starting'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/'
                'change-crypto-domain-configuration',
                {}, True, True)

    def test_part_ccc(self):
        """
        Test POST partition change-crypto-domain-configuration, successful.
        """

        testcases = [
            # (input_domain_index, input_access_mode)
            # TODO: Change testcases to allow for different initial states
            # TODO: Change testcases to allow for expected results
            (17, 'control'),
        ]

        for tc in testcases:

            input_domain_index = tc[0]
            input_access_mode = tc[1]

            operation_body = {}
            if input_domain_index is not None:
                operation_body['domain-index'] = input_domain_index
            if input_access_mode is not None:
                operation_body['access-mode'] = input_access_mode

            # Set the partition status to a valid status for this operation
            partition1 = self.hmc.lookup_by_uri('/api/partitions/1')
            partition1.properties['status'] = 'active'

            # Set up the initial partition config
            partition1.properties['crypto-configuration'] = {
                'crypto-adapter-uris': ['fake-uri1', 'fake-uri2'],
                'crypto-domain-configurations': [
                    {'domain-index': 17,
                     'access-mode': 'control-usage'},
                    {'domain-index': 18,
                     'access-mode': 'control-usage'},
                ]
            }

            # the function to be tested:
            resp = self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/'
                'change-crypto-domain-configuration',
                operation_body, True, True)

            assert resp is None

            crypto_config = partition1.properties['crypto-configuration']
            assert isinstance(crypto_config, dict)

            adapter_uris = crypto_config['crypto-adapter-uris']
            assert isinstance(adapter_uris, list)

            domain_configs = crypto_config['crypto-domain-configurations']
            assert isinstance(domain_configs, list)


class TestHbaHandler:
    """
    All tests for classes HbasHandler and HbaHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        HbasHandler and HbaHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/hbas(?:\?(.*))?', HbasHandler),
            (r'/api/partitions/([^/]+)/hbas/([^/]+)', HbaHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_hba_list(self):
        """
        Test GET HBAs (list).
        """

        # the function to be tested:
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)

        hba_uris = partition1.get('hba-uris', [])

        exp_hba_uris = [
            '/api/partitions/1/hbas/1',
        ]
        assert hba_uris == exp_hba_uris

    def test_hba_get(self):
        """
        Test GET HBA.
        """

        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        hba1_uri = partition1.get('hba-uris', [])[0]

        # the function to be tested:
        hba1 = self.urihandler.get(self.hmc, hba1_uri, True)

        exp_hba1 = {
            'element-id': '1',
            'element-uri': '/api/partitions/1/hbas/1',
            'class': 'hba',
            'parent': '/api/partitions/1',
            'name': 'hba_1',
            'description': 'HBA #1 in Partition #1',
            'adapter-port-uri': '/api/adapters/2/storage-ports/1',
            'wwpn': 'CFFEAFFE00008001',
            'device-number': '1001',
        }
        assert hba1 == exp_hba1

    def test_hba_create_verify(self):
        """
        Test POST HBAs (create).
        """

        new_hba2 = {
            'element-id': '2',
            'name': 'hba_2',
            'adapter-port-uri': '/api/adapters/2/storage-ports/1',
        }

        # the function to be tested:
        resp = self.urihandler.post(self.hmc, '/api/partitions/1/hbas',
                                    new_hba2, True, True)

        assert len(resp) == 1
        assert 'element-uri' in resp
        new_hba2_uri = resp['element-uri']
        assert new_hba2_uri == '/api/partitions/1/hbas/2'

        # the function to be tested:
        hba2 = self.urihandler.get(self.hmc, '/api/partitions/1/hbas/2', True)

        exp_hba2 = {
            'element-id': '2',
            'element-uri': '/api/partitions/1/hbas/2',
            'class': 'hba',
            'parent': '/api/partitions/1',
            'name': 'hba_2',
            'adapter-port-uri': '/api/adapters/2/storage-ports/1',
            'device-number': hba2['device-number'],  # auto-generated
            'wwpn': hba2['wwpn'],  # auto-generated
        }

        assert hba2 == exp_hba2

    def test_hba_update_verify(self):
        """
        Test POST HBA (update).
        """

        update_hba1 = {
            'description': 'updated hba #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/partitions/1/hbas/1',
                             update_hba1, True, True)

        hba1 = self.urihandler.get(self.hmc, '/api/partitions/1/hbas/1', True)
        assert hba1['description'] == 'updated hba #1'

    def test_hba_delete_verify(self):
        """
        Test DELETE HBA.
        """

        self.urihandler.get(self.hmc, '/api/partitions/1/hbas/1', True)

        # the function to be tested:
        self.urihandler.delete(self.hmc, '/api/partitions/1/hbas/1', True)

        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc, '/api/partitions/1/hbas/1', True)


class TestHbaReassignPortHandler:
    """
    All tests for class HbaReassignPortHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        HbaReassignPortHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/hbas/([^/]+)', HbaHandler),
            (r'/api/partitions/([^/]+)/hbas/([^/]+)'
             '/operations/reassign-storage-adapter-port',
             HbaReassignPortHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_hba_rap_err_missing_body(self):
        """
        Test POST HBA reassign-storage-adapter-port, with missing request body.
        """

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/hbas/1/operations/'
                'reassign-storage-adapter-port',
                None, True, True)

    def test_hba_rap_err_missing_field_1(self):
        """
        Test POST HBA reassign-storage-adapter-port, with missing
        'adapter-port-uri' field in request body.
        """

        operation_body = {
            # missing 'adapter-port-uri'
        }

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/hbas/1/operations/'
                'reassign-storage-adapter-port',
                operation_body, True, True)

    def test_hba_rap(self):
        """
        Test POST HBA reassign-storage-adapter-port, successful.
        """

        new_adapter_port_uri = '/api/adapters/2a/port/1'
        operation_body = {
            'adapter-port-uri': new_adapter_port_uri,
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc,
            '/api/partitions/1/hbas/1/operations/'
            'reassign-storage-adapter-port',
            operation_body, True, True)

        assert resp is None

        hba = self.urihandler.get(self.hmc, '/api/partitions/1/hbas/1', True)
        adapter_port_uri = hba['adapter-port-uri']
        assert adapter_port_uri == new_adapter_port_uri


class TestNicHandler:
    """
    All tests for classes NicsHandler and NicHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        NicsHandler and NicHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/nics(?:\?(.*))?', NicsHandler),
            (r'/api/partitions/([^/]+)/nics/([^/]+)', NicHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_nic_list(self):
        """
        Test GET NICs (list).
        """

        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)

        # the function to be tested:
        nic_uris = partition1.get('nic-uris', [])

        exp_nic_uris = [
            '/api/partitions/1/nics/1',
        ]
        assert nic_uris == exp_nic_uris

    def test_nic_get(self):
        """
        Test GET NIC.
        """

        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        nic1_uri = partition1.get('nic-uris', [])[0]

        # the function to be tested:
        nic1 = self.urihandler.get(self.hmc, nic1_uri, True)

        exp_nic1 = {
            'element-id': '1',
            'element-uri': '/api/partitions/1/nics/1',
            'class': 'nic',
            'parent': '/api/partitions/1',
            'name': 'nic_1',
            'description': 'NIC #1 in Partition #1',
            'network-adapter-port-uri': '/api/adapters/3/network-ports/1',
            'device-number': '2001',
            'ssc-management-nic': False,
            'type': 'roce',
        }
        assert nic1 == exp_nic1

    def test_nic_create_verify(self):
        """
        Test POST NICs (create).
        """

        new_nic2 = {
            'element-id': '2',
            'name': 'nic_2',
            'network-adapter-port-uri': '/api/adapters/3/network-ports/1',
        }

        # the function to be tested:
        resp = self.urihandler.post(self.hmc, '/api/partitions/1/nics',
                                    new_nic2, True, True)

        assert len(resp) == 1
        assert 'element-uri' in resp
        new_nic2_uri = resp['element-uri']
        assert new_nic2_uri == '/api/partitions/1/nics/2'

        # the function to be tested:
        nic2 = self.urihandler.get(self.hmc, '/api/partitions/1/nics/2', True)

        exp_nic2 = {
            'element-id': '2',
            'element-uri': '/api/partitions/1/nics/2',
            'class': 'nic',
            'parent': '/api/partitions/1',
            'name': 'nic_2',
            'network-adapter-port-uri': '/api/adapters/3/network-ports/1',
            'device-number': nic2['device-number'],  # auto-generated
            'ssc-management-nic': False,
            'type': 'iqd',
        }

        assert nic2 == exp_nic2

    def test_nic_update_verify(self):
        """
        Test POST NIC (update).
        """

        update_nic1 = {
            'description': 'updated nic #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/partitions/1/nics/1',
                             update_nic1, True, True)

        nic1 = self.urihandler.get(self.hmc, '/api/partitions/1/nics/1', True)
        assert nic1['description'] == 'updated nic #1'

    def test_nic_delete_verify(self):
        """
        Test DELETE NIC.
        """

        self.urihandler.get(self.hmc, '/api/partitions/1/nics/1', True)

        # the function to be tested:
        self.urihandler.delete(self.hmc, '/api/partitions/1/nics/1', True)

        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc, '/api/partitions/1/nics/1', True)


class TestVirtualFunctionHandler:
    """
    All tests for classes VirtualFunctionsHandler and VirtualFunctionHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        VirtualFunctionsHandler and VirtualFunctionHandler and other needed
        handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/virtual-functions(?:\?(.*))?',
             VirtualFunctionsHandler),
            (r'/api/partitions/([^/]+)/virtual-functions/([^/]+)',
             VirtualFunctionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_vf_list(self):
        """
        Test GET virtual functions (list).
        """

        # the function to be tested:
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)

        vf_uris = partition1.get('virtual-function-uris', [])

        exp_vf_uris = [
            '/api/partitions/1/virtual-functions/1',
        ]
        assert vf_uris == exp_vf_uris

    def test_vf_get(self):
        """
        Test GET virtual function.
        """

        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        vf1_uri = partition1.get('virtual-function-uris', [])[0]

        # the function to be tested:
        vf1 = self.urihandler.get(self.hmc, vf1_uri, True)

        exp_vf1 = {
            'element-id': '1',
            'element-uri': '/api/partitions/1/virtual-functions/1',
            'class': 'virtual-function',
            'parent': '/api/partitions/1',
            'name': 'vf_1',
            'description': 'VF #1 in Partition #1',
            'device-number': '3001',
            'adapter-uri': '/api/adapters/5',
        }
        assert vf1 == exp_vf1

    def test_vf_create_verify(self):
        """
        Test POST virtual functions (create).
        """

        new_vf2 = {
            'element-id': '2',
            'name': 'vf_2',
        }

        # the function to be tested:
        resp = self.urihandler.post(self.hmc,
                                    '/api/partitions/1/virtual-functions',
                                    new_vf2, True, True)

        assert len(resp) == 1
        assert 'element-uri' in resp
        new_vf2_uri = resp['element-uri']
        assert new_vf2_uri == '/api/partitions/1/virtual-functions/2'

        # the function to be tested:
        vf2 = self.urihandler.get(self.hmc,
                                  '/api/partitions/1/virtual-functions/2',
                                  True)

        exp_vf2 = {
            'element-id': '2',
            'element-uri': '/api/partitions/1/virtual-functions/2',
            'class': 'virtual-function',
            'parent': '/api/partitions/1',
            'name': 'vf_2',
            'device-number': vf2['device-number'],  # auto-generated
        }

        assert vf2 == exp_vf2

    def test_vf_update_verify(self):
        """
        Test POST virtual function (update).
        """

        update_vf1 = {
            'description': 'updated vf #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/partitions/1/virtual-functions/1',
                             update_vf1, True, True)

        vf1 = self.urihandler.get(self.hmc,
                                  '/api/partitions/1/virtual-functions/1',
                                  True)
        assert vf1['description'] == 'updated vf #1'

    def test_vf_delete_verify(self):
        """
        Test DELETE virtual function.
        """

        self.urihandler.get(self.hmc, '/api/partitions/1/virtual-functions/1',
                            True)

        # the function to be tested:
        self.urihandler.delete(self.hmc,
                               '/api/partitions/1/virtual-functions/1', True)

        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc,
                                '/api/partitions/1/virtual-functions/1', True)


class TestVirtualSwitchHandlers:
    """
    All tests for classes VirtualSwitchesHandler and VirtualSwitchHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        VirtualSwitchesHandler and VirtualSwitchHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/virtual-switches(?:\?(.*))?',
             VirtualSwitchesHandler),
            (r'/api/virtual-switches/([^/]+)', VirtualSwitchHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_vs_list(self):
        """
        Test GET virtual switches (list).
        """

        # the function to be tested:
        vswitches = self.urihandler.get(self.hmc,
                                        '/api/cpcs/2/virtual-switches', True)

        exp_vswitches = {  # properties reduced to those returned by List
            'virtual-switches': [
                {
                    'object-uri': '/api/virtual-switches/1',
                    'name': 'vswitch_osa_1',
                    'type': 'osd',
                    # status not set in resource -> not in response
                },
            ]
        }
        assert vswitches == exp_vswitches

    def test_vs_get(self):
        """
        Test GET virtual switch.
        """

        # the function to be tested:
        vswitch1 = self.urihandler.get(self.hmc, '/api/virtual-switches/1',
                                       True)

        exp_vswitch1 = {
            'object-id': '1',
            'object-uri': '/api/virtual-switches/1',
            'class': 'virtual-switch',
            'parent': '/api/cpcs/2',
            'name': 'vswitch_osa_1',
            'description': 'Vswitch for OSA #1 in CPC #2',
            'type': 'osd',
            'connected-vnic-uris': [],  # auto-generated
        }
        assert vswitch1 == exp_vswitch1


class TestVirtualSwitchGetVnicsHandler:
    """
    All tests for class VirtualSwitchGetVnicsHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        VirtualSwitchGetVnicsHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/virtual-switches/([^/]+)', VirtualSwitchHandler),
            (r'/api/virtual-switches/([^/]+)/operations/get-connected-vnics',
             VirtualSwitchGetVnicsHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_vs_getvnics(self):
        """
        Test GET virtual switch get-connected-vnics.
        """

        connected_nic_uris = ['/api/adapters/1/ports/1']

        # Set up the connected vNICs in the vswitch
        vswitch1 = self.hmc.lookup_by_uri('/api/virtual-switches/1')
        vswitch1.properties['connected-vnic-uris'] = connected_nic_uris

        # the function to be tested:
        # XXX: Fix this to be get instead of post, also in handler itself.
        resp = self.urihandler.post(
            self.hmc,
            '/api/virtual-switches/1/operations/get-connected-vnics',
            None, True, True)

        exp_resp = {
            'connected-vnic-uris': connected_nic_uris,
        }
        assert resp == exp_resp


class TestStorageGroupHandlers:
    """
    All tests for classes StorageGroupsHandler and StorageGroupHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        StorageGroupsHandler and StorageGroupHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/storage-groups(?:\?(.*))?', StorageGroupsHandler),
            (r'/api/storage-groups/([^/]+)', StorageGroupHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_stogrp_list(self):
        """
        Test GET Storage Groups (list).
        """

        # the function to be tested:
        stogrps = self.urihandler.get(self.hmc, '/api/storage-groups', True)

        exp_stogrps = {  # properties reduced to those returned by List
            'storage-groups': [
                {
                    'object-uri': '/api/storage-groups/fake-stogrp-oid-1',
                    'cpc-uri': '/api/cpcs/2',
                    'name': 'fake_stogrp_name_1',
                    'fulfillment-state': 'complete',
                    'type': 'fcp',
                },
            ]
        }
        assert stogrps == exp_stogrps

    def test_stogrp_get(self):
        """
        Test GET Storage Group.
        """

        # the function to be tested:
        stogrp1 = self.urihandler.get(
            self.hmc, '/api/storage-groups/fake-stogrp-oid-1', True)

        exp_stogrp1 = {
            'object-id': 'fake-stogrp-oid-1',
            'object-uri': '/api/storage-groups/fake-stogrp-oid-1',
            'class': 'storage-group',
            'parent': '/api/console',
            'cpc-uri': '/api/cpcs/2',
            'name': 'fake_stogrp_name_1',
            'description': 'Storage Group #1',
            'fulfillment-state': 'complete',
            'type': 'fcp',
            'shared': False,
            'storage-volume-uris': [
                '/api/storage-groups/fake-stogrp-oid-1/storage-volumes/'
                'fake-stovol-oid-1',
            ],
            'virtual-storage-resource-uris': [
                '/api/storage-groups/fake-stogrp-oid-1/'
                'virtual-storage-resources/fake-vsr-oid-1',
            ],
            'candidate-adapter-port-uris': ['/api/cpcs/2/adapters/2'],
        }
        assert stogrp1 == exp_stogrp1


# TODO: Test StorageGroupModifyHandler
# TODO: Test StorageGroupDeleteHandler
# TODO: Test StorageGroupRequestFulfillmentHandler
# TODO: Test StorageGroupAddCandidatePortsHandler
# TODO: Test StorageGroupRemoveCandidatePortsHandler


class TestStorageVolumeHandlers:
    """
    All tests for classes StorageVolumesHandler and StorageVolumeHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        StorageVolumesHandler and StorageVolumeHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/storage-groups/([^/]+)/storage-volumes(?:\?(.*))?',
             StorageVolumesHandler),
            (r'/api/storage-groups/([^/]+)/storage-volumes/([^/]+)',
             StorageVolumeHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_stovol_list(self):
        """
        Test GET Storage Volumes of Storage Group (list).
        """

        # the function to be tested:
        stovols = self.urihandler.get(
            self.hmc, '/api/storage-groups/fake-stogrp-oid-1/storage-volumes',
            True)

        exp_stovols = {  # properties reduced to those returned by List
            'storage-volumes': [
                {
                    'element-uri': '/api/storage-groups/fake-stogrp-oid-1/'
                                   'storage-volumes/fake-stovol-oid-1',
                    'name': 'fake_stovol_name_1',
                    'fulfillment-state': 'complete',
                    'size': 10.0,
                    'usage': 'boot',
                },
            ]
        }
        assert stovols == exp_stovols

    def test_stovol_get(self):
        """
        Test GET Storage Volume.
        """

        # the function to be tested:
        stovol1 = self.urihandler.get(
            self.hmc, '/api/storage-groups/fake-stogrp-oid-1/'
            'storage-volumes/fake-stovol-oid-1', True)

        exp_stovol1 = {
            'element-id': 'fake-stovol-oid-1',
            'element-uri': '/api/storage-groups/fake-stogrp-oid-1/'
                           'storage-volumes/fake-stovol-oid-1',
            'class': 'storage-volume',
            'parent': '/api/storage-groups/fake-stogrp-oid-1',
            'name': 'fake_stovol_name_1',
            'description': 'Storage Volume #1',
            'fulfillment-state': 'complete',
            'size': 10.0,
            'usage': 'boot',
        }
        assert stovol1 == exp_stovol1


class TestVirtualStorageResourceHandlers:
    """
    All tests for classes VirtualStorageResourcesHandler and
    VirtualStorageResourceHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        VirtualStorageResourcesHandler and VirtualStorageResourceHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/storage-groups/([^/]+)/virtual-storage-resources'
             r'(?:\?(.*))?', VirtualStorageResourcesHandler),
            (r'/api/storage-groups/([^/]+)/virtual-storage-resources/([^/]+)',
             VirtualStorageResourceHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_vsr_list(self):
        """
        Test GET Virtual Storage Resources of Storage Group (list).
        """

        # the function to be tested:
        vsrs = self.urihandler.get(
            self.hmc,
            '/api/storage-groups/fake-stogrp-oid-1/virtual-storage-resources',
            True)

        exp_vsrs = {  # properties reduced to those returned by List
            'virtual-storage-resources': [
                {
                    'element-uri': '/api/storage-groups/fake-stogrp-oid-1/'
                                   'virtual-storage-resources/fake-vsr-oid-1',
                    'name': 'fake_vsr_name_1',
                    'device-number': '1300',
                    'partition-uri': None,
                    'adapter-port-uri': None,
                },
            ]
        }
        assert vsrs == exp_vsrs

    def test_vsr_get(self):
        """
        Test GET Virtual Storage Resource.
        """

        # the function to be tested:
        vsr1 = self.urihandler.get(
            self.hmc, '/api/storage-groups/fake-stogrp-oid-1/'
            'virtual-storage-resources/fake-vsr-oid-1', True)

        exp_vsr1 = {
            'element-id': 'fake-vsr-oid-1',
            'element-uri': '/api/storage-groups/fake-stogrp-oid-1/'
                           'virtual-storage-resources/fake-vsr-oid-1',
            'class': 'virtual-storage-resource',
            'parent': '/api/storage-groups/fake-stogrp-oid-1',
            'name': 'fake_vsr_name_1',
            'description': 'Virtual Storage Resource #1',
            'device-number': '1300',
            'partition-uri': None,
            'adapter-port-uri': None,
        }
        assert vsr1 == exp_vsr1


class TestStorageTemplateHandlers:
    """
    All tests for classes StorageTemplatesHandler and StorageTemplateHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        StorageTemplatesHandler and StorageTemplateHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/storage-templates(?:\?(.*))?', StorageTemplatesHandler),
            (r'/api/storage-templates/([^/]+)', StorageTemplateHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_stotpl_list(self):
        """
        Test GET Storage Templates (list).
        """

        # the function to be tested:
        stotpls = self.urihandler.get(self.hmc, '/api/storage-templates', True)

        exp_stotpls = {  # properties reduced to those returned by List
            'storage-templates': [
                {
                    'object-uri': '/api/storage-templates/fake-stotpl-oid-1',
                    'cpc-uri': '/api/cpcs/2',
                    'name': 'fake_stotpl_name_1',
                    'type': 'fcp',
                },
            ]
        }
        assert stotpls == exp_stotpls

    def test_stotpl_get(self):
        """
        Test GET Storage Group Template.
        """

        # the function to be tested:
        stotpl1 = self.urihandler.get(
            self.hmc, '/api/storage-templates/fake-stotpl-oid-1', True)

        exp_stotpl1 = {
            'object-id': 'fake-stotpl-oid-1',
            'object-uri': '/api/storage-templates/fake-stotpl-oid-1',
            'class': 'storage-template',
            'parent': '/api/console',
            'cpc-uri': '/api/cpcs/2',
            'name': 'fake_stotpl_name_1',
            'description': 'Storage Group Template #1',
            'type': 'fcp',
            'shared': False,
            'storage-template-volume-uris': [
                '/api/storage-templates/fake-stotpl-oid-1/'
                'storage-template-volumes/fake-stotvl-oid-1',
            ],
        }
        assert stotpl1 == exp_stotpl1


# TODO: Test StorageTemplateModifyHandler


class TestStorageTemplateVolumeHandlers:
    """
    All tests for classes StorageTemplateVolumesHandler and
    StorageTemplateVolumeHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        StorageTemplateVolumesHandler and StorageTemplateVolumeHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/storage-templates/([^/]+)/'
             r'storage-template-volumes(?:\?(.*))?',
             StorageTemplateVolumesHandler),
            (r'/api/storage-templates/([^/]+)/'
             r'storage-template-volumes/([^/]+)',
             StorageTemplateVolumeHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_stotvl_list(self):
        """
        Test GET Storage Volumes of Storage Template (list).
        """

        # the function to be tested:
        stotvls = self.urihandler.get(
            self.hmc,
            '/api/storage-templates/fake-stotpl-oid-1/'
            'storage-template-volumes',
            True)

        exp_stotvls = {  # properties reduced to those returned by List
            'storage-template-volumes': [
                {
                    'element-uri': '/api/storage-templates/fake-stotpl-oid-1/'
                                   'storage-template-volumes/fake-stotvl-oid-1',
                    'name': 'fake_stotvl_name_1',
                    'size': 10.0,
                    'usage': 'boot',
                },
            ]
        }
        assert stotvls == exp_stotvls

    def test_stotvl_get(self):
        """
        Test GET Storage Template Volume.
        """

        # the function to be tested:
        stotvl1 = self.urihandler.get(
            self.hmc, '/api/storage-templates/fake-stotpl-oid-1/'
            'storage-template-volumes/fake-stotvl-oid-1', True)

        exp_stotvl1 = {
            'element-id': 'fake-stotvl-oid-1',
            'element-uri': '/api/storage-templates/fake-stotpl-oid-1/'
                           'storage-template-volumes/fake-stotvl-oid-1',
            'class': 'storage-template-volume',
            'parent': '/api/storage-templates/fake-stotpl-oid-1',
            'name': 'fake_stotvl_name_1',
            'description': 'Storage Volume Template #1',
            'size': 10.0,
            'usage': 'boot',
        }
        assert stotvl1 == exp_stotvl1


class TestCapacityGroupHandlers:
    """
    All tests for classes CapacityGroupsHandler and CapacityGroupHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CapacityGroupsHandler and CapacityGroupHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/capacity-groups(?:\?(.*))?',
             CapacityGroupsHandler),
            (r'/api/cpcs/([^/]+)/capacity-groups/([^/]+)',
             CapacityGroupHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cgm_list(self):
        """
        Test GET capacity groups (list).
        """

        # the function to be tested:
        cgs = self.urihandler.get(self.hmc, '/api/cpcs/2/capacity-groups',
                                  True)

        exp_cgs = {  # properties reduced to those returned by List
            'capacity-groups': [
                {
                    'element-uri': '/api/cpcs/2/capacity-groups/1',
                    'name': 'capacity_group1',
                    # status not set in resource -> not in response
                },
            ]
        }
        assert cgs == exp_cgs

    def test_cg_get(self):
        """
        Test GET capacity group.
        """

        # the function to be tested:
        cg1 = self.urihandler.get(self.hmc, '/api/cpcs/2/capacity-groups/1',
                                  True)

        exp_cg1 = {
            'element-id': '1',
            'element-uri': '/api/cpcs/2/capacity-groups/1',
            'class': 'capacity-group',
            'parent': '/api/cpcs/2',
            'name': 'capacity_group1',
            'description': 'Capacity Group #1',
            'capping-enabled': True,
            'partition-uris': [],  # auto-generated
        }
        assert cg1 == exp_cg1


class TestCapacityGroupAddPartitionHandler:
    """
    All tests for class CapacityGroupAddPartitionHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CapacityGroupAddPartitionHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/cpcs/([^/]+)/capacity-groups(?:\?(.*))?',
             CapacityGroupsHandler),
            (r'/api/cpcs/([^/]+)/capacity-groups/([^/]+)/operations/'
             'add-partition',
             CapacityGroupAddPartitionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cg_add_partition(self):
        """
        Test POST capacity group add-partitions (to empty capacity group).
        """

        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1_uri = partition1['object-uri']

        # The function to be tested:
        self.urihandler.post(
            self.hmc,
            '/api/cpcs/2/capacity-groups/1/operations/add-partition',
            {'partition-uri': partition1_uri},
            True, True)


class TestCapacityGroupRemovePartitionHandler:
    """
    All tests for class CapacityGroupRemovePartitionHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        CapacityGroupRemovePartitionHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/cpcs/([^/]+)/capacity-groups(?:\?(.*))?',
             CapacityGroupsHandler),
            (r'/api/cpcs/([^/]+)/capacity-groups/([^/]+)/operations/'
             'remove-partition',
             CapacityGroupRemovePartitionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_cg_remove_partition(self):
        """
        Test POST capacity group remove-partitions (from empty capacity group).
        """

        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1_uri = partition1['object-uri']

        with pytest.raises(ConflictError) as exc_info:

            # The function to be tested:
            self.urihandler.post(
                self.hmc,
                '/api/cpcs/2/capacity-groups/1/operations/remove-partition',
                {'partition-uri': partition1_uri},
                True, True)

        exc = exc_info.value
        assert exc.reason == 140


class TestLparHandlers:
    """
    All tests for classes LparsHandler and LparHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        LparsHandler and LparHandler.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/logical-partitions(?:\?(.*))?', LparsHandler),
            (r'/api/logical-partitions/([^/]+)', LparHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_lpar_list(self):
        """
        Test GET LPARs (list).
        """

        # the function to be tested:
        lpars = self.urihandler.get(self.hmc,
                                    '/api/cpcs/1/logical-partitions', True)

        exp_lpars = {  # properties reduced to those returned by List
            'logical-partitions': [
                {
                    'object-uri': '/api/logical-partitions/1',
                    'name': 'lpar_1',
                    'status': 'not-activated',
                },
            ]
        }
        assert lpars == exp_lpars

    def test_lpar_get(self):
        """
        Test GET LPAR.
        """

        # the function to be tested:
        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)

        exp_lpar1 = {
            'object-id': '1',
            'object-uri': '/api/logical-partitions/1',
            'class': 'logical-partition',
            'parent': '/api/cpcs/1',
            'name': 'lpar_1',
            'status': 'not-activated',
            'description': 'LPAR #1 in CPC #1',
        }
        assert lpar1 == exp_lpar1


class TestLparActLoadDeactHandler:
    """
    All tests for classes LparActivateHandler, LparLoadHandler, and
    LparDeactivateHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        LparActivateHandler, LparLoadHandler, and
        LparDeactivateHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/logical-partitions/([^/]+)',
             LparHandler),
            (r'/api/logical-partitions/([^/]+)/operations/activate',
             LparActivateHandler),
            (r'/api/logical-partitions/([^/]+)/operations/deactivate',
             LparDeactivateHandler),
            (r'/api/logical-partitions/([^/]+)/operations/load',
             LparLoadHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_lpar_start_stop(self):
        """
        Test POST LPAR activate, load, deactivate.
        """

        # CPC1 is in classic mode
        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-activated'
        lpar1_name = lpar1['name']

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/activate',
                             {'activation-profile-name': lpar1_name},
                             True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-operating'

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/load',
                             {'load-address': '5176'}, True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'operating'

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/deactivate',
                             {'force': True}, True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-activated'


class TestLparScsiLoadHandler:
    """
    All tests for class LparScsiLoadHandler and other needed classes.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        the needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/logical-partitions/([^/]+)',
             LparHandler),
            (r'/api/logical-partitions/([^/]+)/operations/activate',
             LparActivateHandler),
            (r'/api/logical-partitions/([^/]+)/operations/deactivate',
             LparDeactivateHandler),
            (r'/api/logical-partitions/([^/]+)/operations/scsi-load',
             LparScsiLoadHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_lpar_start_stop(self):
        """
        Test POST LPAR activate, SCSI load, deactivate.
        """

        # CPC1 is in classic mode
        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-activated'
        lpar1_name = lpar1['name']

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/activate',
                             {'activation-profile-name': lpar1_name},
                             True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-operating'

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/scsi-load',
                             {'load-address': '5176',
                              'world-wide-port-name': '1234',
                              'logical-unit-number': '5678'},
                             True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'operating'

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/deactivate',
                             {'force': True}, True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-activated'


class TestLparScsiDumpHandler:
    """
    All tests for class LparScsiDumpHandler and other needed classes.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        the needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/logical-partitions/([^/]+)',
             LparHandler),
            (r'/api/logical-partitions/([^/]+)/operations/activate',
             LparActivateHandler),
            (r'/api/logical-partitions/([^/]+)/operations/deactivate',
             LparDeactivateHandler),
            (r'/api/logical-partitions/([^/]+)/operations/scsi-dump',
             LparScsiDumpHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_lpar_start_stop(self):
        """
        Test POST LPAR activate, SCSI load, deactivate.
        """

        # CPC1 is in classic mode
        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-activated'
        lpar1_name = lpar1['name']

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/activate',
                             {'activation-profile-name': lpar1_name},
                             True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-operating'

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/scsi-dump',
                             {'load-address': '5176',
                              'world-wide-port-name': '1234',
                              'logical-unit-number': '5678'},
                             True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'operating'

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/deactivate',
                             {'force': True}, True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-activated'


class TestLparNvmeLoadHandler:
    """
    All tests for class LparNvmeLoadHandler and other needed classes.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        the needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/logical-partitions/([^/]+)',
             LparHandler),
            (r'/api/logical-partitions/([^/]+)/operations/activate',
             LparActivateHandler),
            (r'/api/logical-partitions/([^/]+)/operations/deactivate',
             LparDeactivateHandler),
            (r'/api/logical-partitions/([^/]+)/operations/nvme-load',
             LparNvmeLoadHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_lpar_start_stop(self):
        """
        Test POST LPAR activate, NVME load, deactivate.
        """

        # CPC1 is in classic mode
        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-activated'
        lpar1_name = lpar1['name']

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/activate',
                             {'activation-profile-name': lpar1_name},
                             True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-operating'

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/nvme-load',
                             {'load-address': '5176'},
                             True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'operating'

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/deactivate',
                             {'force': True}, True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-activated'


class TestLparNvmeDumpHandler:
    """
    All tests for class LparNvmeDumpHandler and other needed classes.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        the needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/logical-partitions/([^/]+)',
             LparHandler),
            (r'/api/logical-partitions/([^/]+)/operations/activate',
             LparActivateHandler),
            (r'/api/logical-partitions/([^/]+)/operations/deactivate',
             LparDeactivateHandler),
            (r'/api/logical-partitions/([^/]+)/operations/nvme-dump',
             LparNvmeDumpHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_lpar_start_stop(self):
        """
        Test POST LPAR activate, NVME load, deactivate.
        """

        # CPC1 is in classic mode
        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-activated'
        lpar1_name = lpar1['name']

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/activate',
                             {'activation-profile-name': lpar1_name},
                             True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-operating'

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/nvme-dump',
                             {'load-address': '5176'},
                             True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'operating'

        # the function to be tested:
        self.urihandler.post(self.hmc,
                             '/api/logical-partitions/1/operations/deactivate',
                             {'force': True}, True, True)

        lpar1 = self.urihandler.get(self.hmc, '/api/logical-partitions/1',
                                    True)
        assert lpar1['status'] == 'not-activated'


# TODO: Add test for handler for start
# TODO: Add test for handler for stop
# TODO: Add test for handler for psw-restart
# TODO: Add test for handler for reset-clear
# TODO: Add test for handler for reset-normal


class TestResetActProfileHandlers:
    """
    All tests for classes ResetActProfilesHandler and ResetActProfileHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        ResetActProfilesHandler and ResetActProfileHandler and other needed
        handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/reset-activation-profiles(?:\?(.*))?',
             ResetActProfilesHandler),
            (r'/api/cpcs/([^/]+)/reset-activation-profiles/([^/]+)',
             ResetActProfileHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_rap_list(self):
        """
        Test GET reset activation profiles (list).
        """

        # the function to be tested:
        raps = self.urihandler.get(self.hmc,
                                   '/api/cpcs/1/reset-activation-profiles',
                                   True)

        exp_raps = {  # properties reduced to those returned by List
            'reset-activation-profiles': [
                {
                    'name': 'r1',
                    'element-uri': '/api/cpcs/1/reset-activation-profiles/r1',
                },
            ]
        }
        assert raps == exp_raps

    def test_rap_get(self):
        """
        Test GET reset activation profile.
        """

        # the function to be tested:
        rap1 = self.urihandler.get(self.hmc,
                                   '/api/cpcs/1/reset-activation-profiles/r1',
                                   True)

        exp_rap1 = {
            'name': 'r1',
            'class': 'reset-activation-profile',
            'parent': '/api/cpcs/1',
            'element-uri': '/api/cpcs/1/reset-activation-profiles/r1',
            'description': 'Reset profile #1 in CPC #1',
        }
        assert rap1 == exp_rap1


class TestImageActProfileHandlers:
    """
    All tests for classes ImageActProfilesHandler and ImageActProfileHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        ImageActProfilesHandler and ImageActProfileHandler and other needed
        handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/image-activation-profiles/([^/]+)',
             ImageActProfileHandler),
            (r'/api/cpcs/([^/]+)/image-activation-profiles(?:\?(.*))?',
             ImageActProfilesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_iap_list(self):
        """
        Test GET image activation profiles (list).
        """

        # the function to be tested:
        iaps = self.urihandler.get(self.hmc,
                                   '/api/cpcs/1/image-activation-profiles',
                                   True)

        exp_iaps = {  # properties reduced to those returned by List
            'image-activation-profiles': [
                {
                    'name': 'i1',
                    'element-uri': '/api/cpcs/1/image-activation-profiles/i1',
                },
            ]
        }
        assert iaps == exp_iaps

    def test_iap_get(self):
        """
        Test GET image activation profile.
        """

        # the function to be tested:
        iap1 = self.urihandler.get(self.hmc,
                                   '/api/cpcs/1/image-activation-profiles/i1',
                                   True)

        exp_iap1 = {
            'name': 'i1',
            'element-uri': '/api/cpcs/1/image-activation-profiles/i1',
            'class': 'image-activation-profile',
            'parent': '/api/cpcs/1',
            'description': 'Image profile #1 in CPC #1',
        }
        assert iap1 == exp_iap1


class TestLoadActProfileHandlers:
    """
    All tests for classes LoadActProfilesHandler and LoadActProfileHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        LoadActProfilesHandler and LoadActProfileHandler and other needed
        handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/load-activation-profiles/([^/]+)',
             LoadActProfileHandler),
            (r'/api/cpcs/([^/]+)/load-activation-profiles(?:\?(.*))?',
             LoadActProfilesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_lap_list(self):
        """
        Test GET load activation profiles (list).
        """

        # the function to be tested:
        laps = self.urihandler.get(self.hmc,
                                   '/api/cpcs/1/load-activation-profiles',
                                   True)

        exp_laps = {  # properties reduced to those returned by List
            'load-activation-profiles': [
                {
                    'name': 'L1',
                    'element-uri': '/api/cpcs/1/load-activation-profiles/L1',
                },
            ]
        }
        assert laps == exp_laps

    def test_lap_get(self):
        """
        Test GET load activation profile.
        """

        # the function to be tested:
        lap1 = self.urihandler.get(self.hmc,
                                   '/api/cpcs/1/load-activation-profiles/L1',
                                   True)

        exp_lap1 = {
            'name': 'L1',
            'element-uri': '/api/cpcs/1/load-activation-profiles/L1',
            'class': 'load-activation-profile',
            'parent': '/api/cpcs/1',
            'description': 'Load profile #1 in CPC #1',
        }
        assert lap1 == exp_lap1


class TestSubmitRequestsHandler:
    """
    All tests for class SubmitRequestsHandler.
    """

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a Faked HMC with standard resources, and with
        SubmitRequestsHandler and other needed handlers.
        """
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/services/aggregation/submit', SubmitRequestsHandler),
            (r'/api/console/users(?:\?(.*))?', UsersHandler),
            (r'/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_bulk_two_get_success(self):
        """
        Test two successful GET in the bulk operation.
        """

        body = {
            'requests': [
                {
                    'method': 'GET',
                    'uri': '/api/console/users',
                    'id': '1',
                },
                {
                    'method': 'GET',
                    'uri': '/api/console/user-roles',
                    'id': '2',
                },
            ],
        }

        # the function to be tested:
        result = self.urihandler.post(
            self.hmc, '/api/services/aggregation/submit', body, True, True)

        exp_result = [
            {
                'body': {
                    'users': [
                        {
                            'name': 'fake_user_name_1',
                            'object-uri': '/api/users/fake-user-oid-1',
                            'type': 'system-defined',
                        },
                    ],
                },
                'status': 200,
                'headers': [],
                'id': '1',
            },
            {
                'body': {
                    'user-roles': [
                        {
                            'name': 'fake_user_role_name_1',
                            'object-uri':
                                '/api/user-roles/fake-user-role-oid-1',
                            'type': 'system-defined',
                        },
                        {
                            'name': 'hmc-operator-tasks',
                            'object-uri':
                                '/api/user-roles/fake-hmc-operator-tasks',
                            'type': 'system-defined',
                        },
                    ],
                },
                'status': 200,
                'headers': [],
                'id': '2',
            },
        ]
        assert result == exp_result

    def test_bulk_one_post_success(self):
        """
        Test one successful POST in the bulk operation.
        """

        body = {
            'requests': [
                {
                    'method': 'POST',
                    'uri': '/api/console/users',
                    'body': {
                        'name': 'bulk-user',
                        'type': 'standard',
                        'authentication-type': 'local',
                        'password-rule-uri':
                            '/api/password-rules/fake-password-rule-oid-1',
                        'password': 'abcde1234',
                    },
                    'id': '1',
                },
            ],
        }

        # the function to be tested:
        result = self.urihandler.post(
            self.hmc, '/api/services/aggregation/submit', body, True, True)

        exp_result = [
            {
                'body': {
                    'object-uri': '/api/users/1',
                },
                'status': 200,
                'headers': [],
                'id': '1',
            },
        ]
        assert result == exp_result

    def test_bulk_one_delete_success(self):
        """
        Test one successful DELETE in the bulk operation.
        """

        body = {
            'requests': [
                {
                    'method': 'DELETE',
                    'uri': '/api/users/fake-user-oid-1',
                    'id': '1',
                },
            ],
        }

        # the function to be tested:
        result = self.urihandler.post(
            self.hmc, '/api/services/aggregation/submit', body, True, True)

        exp_result = [
            {
                'body': None,
                'status': 200,
                'headers': [],
                'id': '1',
            },
        ]
        assert result == exp_result

    def test_bulk_one_get_fail(self):
        """
        Test one failed GET in the bulk operation.
        """

        body = {
            'requests': [
                {
                    'method': 'GET',
                    'uri': '/api/console/usersxx',
                    'id': '1',
                },
            ],
        }

        # the function to be tested:
        result = self.urihandler.post(
            self.hmc, '/api/services/aggregation/submit', body, True, True)

        exp_result = [
            {
                'body': {
                    'http-status': 404,
                    'message':
                        'Unknown resource with URI: /api/console/usersxx',
                    'reason': 1,
                    'request-authenticated-as': None,
                    'request-headers': [],
                    'request-method': 'GET',
                    'request-uri': '/api/console/usersxx',
                },
                'status': 404,
                'headers': [],
                'id': '1',
            },
        ]
        assert result == exp_result
