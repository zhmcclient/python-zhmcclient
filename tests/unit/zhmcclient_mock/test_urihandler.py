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
Unit tests for _urihandler module of the zhmcclient_mock package.
"""

from __future__ import absolute_import, print_function

import requests.packages.urllib3
from datetime import datetime
# FIXME: Migrate mock to zhmcclient_mock
from mock import MagicMock
import pytest

from zhmcclient_mock._hmc import FakedHmc, FakedMetricGroupDefinition, \
    FakedMetricObjectValues

from zhmcclient_mock._urihandler import HTTPError, InvalidResourceError, \
    InvalidMethodError, CpcNotInDpmError, CpcInDpmError, BadRequestError, \
    ConflictError, ConnectionError, \
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
    CpcsHandler, CpcHandler, CpcSetPowerSaveHandler, \
    CpcSetPowerCappingHandler, CpcGetEnergyManagementDataHandler, \
    CpcStartHandler, CpcStopHandler, \
    CpcImportProfilesHandler, CpcExportProfilesHandler, \
    CpcExportPortNamesListHandler, \
    MetricsContextsHandler, MetricsContextHandler, \
    PartitionsHandler, PartitionHandler, PartitionStartHandler, \
    PartitionStopHandler, PartitionScsiDumpHandler, \
    PartitionPswRestartHandler, PartitionMountIsoImageHandler, \
    PartitionUnmountIsoImageHandler, PartitionIncreaseCryptoConfigHandler, \
    PartitionDecreaseCryptoConfigHandler, PartitionChangeCryptoConfigHandler, \
    HbasHandler, HbaHandler, HbaReassignPortHandler, \
    NicsHandler, NicHandler, \
    VirtualFunctionsHandler, VirtualFunctionHandler, \
    AdaptersHandler, AdapterHandler, AdapterChangeCryptoTypeHandler, \
    AdapterChangeAdapterTypeHandler, \
    NetworkPortHandler, \
    StoragePortHandler, \
    VirtualSwitchesHandler, VirtualSwitchHandler, \
    VirtualSwitchGetVnicsHandler, \
    LparsHandler, LparHandler, LparActivateHandler, LparDeactivateHandler, \
    LparLoadHandler, \
    ResetActProfilesHandler, ResetActProfileHandler, \
    ImageActProfilesHandler, ImageActProfileHandler, \
    LoadActProfilesHandler, LoadActProfileHandler

requests.packages.urllib3.disable_warnings()


class TestHTTPError(object):
    """All tests for class HTTPError."""

    def test_attributes(self):
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

    def test_response(self):
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


class TestConnectionError(object):
    """All tests for class ConnectionError."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
        self.cpc1 = self.hmc.cpcs.add({'name': 'cpc1'})

    def test_attributes(self):
        msg = "fake error message"

        exc = ConnectionError(msg)

        assert exc.message == msg


class DummyHandler1(object):
    pass


class DummyHandler2(object):
    pass


class DummyHandler3(object):
    pass


class TestInvalidResourceError(object):
    """All tests for class InvalidResourceError."""

    def test_attributes_with_handler(self):
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

    def test_attributes_no_handler(self):
        method = 'GET'
        uri = '/api/cpcs'
        exp_http_status = 404
        exp_reason = 1

        exc = InvalidResourceError(method, uri, None)

        assert exc.method == method
        assert exc.uri == uri
        assert exc.http_status == exp_http_status
        assert exc.reason == exp_reason


class TestInvalidMethodError(object):
    """All tests for class InvalidMethodError."""

    def test_attributes_with_handler(self):
        method = 'DELETE'
        uri = '/api/cpcs'
        exp_http_status = 404
        exp_reason = 1

        exc = InvalidMethodError(method, uri, DummyHandler1)

        assert exc.method == method
        assert exc.uri == uri
        assert exc.http_status == exp_http_status
        assert exc.reason == exp_reason

    def test_attributes_no_handler(self):
        method = 'DELETE'
        uri = '/api/cpcs'
        exp_http_status = 404
        exp_reason = 1

        exc = InvalidMethodError(method, uri, None)

        assert exc.method == method
        assert exc.uri == uri
        assert exc.http_status == exp_http_status
        assert exc.reason == exp_reason


class TestCpcNotInDpmError(object):
    """All tests for class CpcNotInDpmError."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
        self.cpc1 = self.hmc.cpcs.add({'name': 'cpc1'})

    def test_attributes(self):
        method = 'GET'
        uri = '/api/cpcs/1/partitions'
        exp_http_status = 409
        exp_reason = 5

        exc = CpcNotInDpmError(method, uri, self.cpc1)

        assert exc.method == method
        assert exc.uri == uri
        assert exc.http_status == exp_http_status
        assert exc.reason == exp_reason


class TestCpcInDpmError(object):
    """All tests for class CpcInDpmError."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
        self.cpc1 = self.hmc.cpcs.add({'name': 'cpc1'})

    def test_attributes(self):
        method = 'GET'
        uri = '/api/cpcs/1/logical-partitions'
        exp_http_status = 409
        exp_reason = 4

        exc = CpcInDpmError(method, uri, self.cpc1)

        assert exc.method == method
        assert exc.uri == uri
        assert exc.http_status == exp_http_status
        assert exc.reason == exp_reason


class TestParseQueryParms(object):
    """All tests for parse_query_parms()."""

    def test_none(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', None)
        assert filter_args is None

    def test_empty(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', '')
        assert filter_args is None

    def test_one_normal(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', 'a=b')
        assert filter_args == {'a': 'b'}

    def test_two_normal(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', 'a=b&c=d')
        assert filter_args == {'a': 'b', 'c': 'd'}

    def test_one_trailing_amp(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', 'a=b&')
        assert filter_args == {'a': 'b'}

    def test_one_leading_amp(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', '&a=b')
        assert filter_args == {'a': 'b'}

    def test_one_missing_value(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', 'a=')
        assert filter_args == {'a': ''}

    def test_one_missing_name(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', '=b')
        assert filter_args == {'': 'b'}

    def test_two_same_normal(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', 'a=b&a=c')
        assert filter_args == {'a': ['b', 'c']}

    def test_two_same_one_normal(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', 'a=b&d=e&a=c')
        assert filter_args == {'a': ['b', 'c'], 'd': 'e'}

    def test_space_value_1(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', 'a=b%20c')
        assert filter_args == {'a': 'b c'}

    def test_space_value_2(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', 'a=%20c')
        assert filter_args == {'a': ' c'}

    def test_space_value_3(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', 'a=b%20')
        assert filter_args == {'a': 'b '}

    def test_space_value_4(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', 'a=%20')
        assert filter_args == {'a': ' '}

    def test_space_name_1(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', 'a%20b=c')
        assert filter_args == {'a b': 'c'}

    def test_space_name_2(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', '%20b=c')
        assert filter_args == {' b': 'c'}

    def test_space_name_3(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', 'a%20=c')
        assert filter_args == {'a ': 'c'}

    def test_space_name_4(self):
        filter_args = parse_query_parms('fake-meth', 'fake-uri', '%20=c')
        assert filter_args == {' ': 'c'}

    def test_invalid_format_1(self):
        with pytest.raises(HTTPError) as exc_info:
            parse_query_parms('fake-meth', 'fake-uri', 'a==b')
        exc = exc_info.value
        assert exc.http_status == 400
        assert exc.reason == 1

    def test_invalid_format_2(self):
        with pytest.raises(HTTPError) as exc_info:
            parse_query_parms('fake-meth', 'fake-uri', 'a=b=c')
        exc = exc_info.value
        assert exc.http_status == 400
        assert exc.reason == 1

    def test_invalid_format_3(self):
        with pytest.raises(HTTPError) as exc_info:
            parse_query_parms('fake-meth', 'fake-uri', 'a')
        exc = exc_info.value
        assert exc.http_status == 400
        assert exc.reason == 1


class TestUriHandlerHandlerEmpty(object):
    """All tests for UriHandler.handler() with empty URIs."""

    def setup_method(self):
        self.uris = ()
        self.urihandler = UriHandler(self.uris)

    def test_uris_empty_1(self):
        with pytest.raises(InvalidResourceError):
            self.urihandler.handler('/api/cpcs', 'GET')

    def test_uris_empty_2(self):
        with pytest.raises(InvalidResourceError):
            self.urihandler.handler('', 'GET')


class TestUriHandlerHandlerSimple(object):
    """All tests for UriHandler.handler() with a simple set of URIs."""

    def setup_method(self):
        self.uris = (
            (r'/api/cpcs', DummyHandler1),
            (r'/api/cpcs/([^/]+)', DummyHandler2),
            (r'/api/cpcs/([^/]+)/child', DummyHandler3),
        )
        self.urihandler = UriHandler(self.uris)

    def test_ok1(self):
        handler_class, uri_parms = self.urihandler.handler(
            '/api/cpcs', 'GET')
        assert handler_class == DummyHandler1
        assert len(uri_parms) == 0

    def test_ok2(self):
        handler_class, uri_parms = self.urihandler.handler(
            '/api/cpcs/fake-id1', 'GET')
        assert handler_class == DummyHandler2
        assert len(uri_parms) == 1
        assert uri_parms[0] == 'fake-id1'

    def test_ok3(self):
        handler_class, uri_parms = self.urihandler.handler(
            '/api/cpcs/fake-id1/child', 'GET')
        assert handler_class == DummyHandler3
        assert len(uri_parms) == 1
        assert uri_parms[0] == 'fake-id1'

    def test_err_begin_missing(self):
        with pytest.raises(InvalidResourceError):
            self.urihandler.handler('api/cpcs', 'GET')

    def test_err_begin_extra(self):
        with pytest.raises(InvalidResourceError):
            self.urihandler.handler('x/api/cpcs', 'GET')

    def test_err_end_missing(self):
        with pytest.raises(InvalidResourceError):
            self.urihandler.handler('/api/cpc', 'GET')

    def test_err_end_extra(self):
        with pytest.raises(InvalidResourceError):
            self.urihandler.handler('/api/cpcs_x', 'GET')

    def test_err_end_slash(self):
        with pytest.raises(InvalidResourceError):
            self.urihandler.handler('/api/cpcs/', 'GET')

    def test_err_end2_slash(self):
        with pytest.raises(InvalidResourceError):
            self.urihandler.handler('/api/cpcs/fake-id1/', 'GET')

    def test_err_end2_missing(self):
        with pytest.raises(InvalidResourceError):
            self.urihandler.handler('/api/cpcs/fake-id1/chil', 'GET')

    def test_err_end2_extra(self):
        with pytest.raises(InvalidResourceError):
            self.urihandler.handler('/api/cpcs/fake-id1/child_x', 'GET')


class TestUriHandlerMethod(object):
    """All tests for get(), post(), delete() methods of class UriHandler."""

    def setup_method(self):
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
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')

    def teardown_method(self):
        delattr(DummyHandler1, 'get')
        delattr(DummyHandler1, 'post')
        delattr(DummyHandler2, 'get')
        delattr(DummyHandler2, 'delete')

    def test_get_cpcs(self):

        # the function to be tested
        result = self.urihandler.get(self.hmc, '/api/cpcs', True)

        assert result == self.cpcs

        DummyHandler1.get.assert_called_with(
            'GET', self.hmc, '/api/cpcs', tuple(), True)
        assert DummyHandler1.post.called == 0
        assert DummyHandler2.get.called == 0
        assert DummyHandler2.delete.called == 0

    def test_get_cpc1(self):

        # the function to be tested
        result = self.urihandler.get(self.hmc, '/api/cpcs/1', True)

        assert result == self.cpc1

        assert DummyHandler1.get.called == 0
        assert DummyHandler1.post.called == 0
        DummyHandler2.get.assert_called_with(
            'GET', self.hmc, '/api/cpcs/1', tuple('1'), True)
        assert DummyHandler2.delete.called == 0

    def test_post_cpcs(self):

        # the function to be tested
        result = self.urihandler.post(self.hmc, '/api/cpcs', {}, True, True)

        assert result == self.new_cpc

        assert DummyHandler1.get.called == 0
        DummyHandler1.post.assert_called_with(
            'POST', self.hmc, '/api/cpcs', tuple(), {}, True, True)
        assert DummyHandler2.get.called == 0
        assert DummyHandler2.delete.called == 0

    def test_delete_cpc2(self):

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
                            'user-template-uri': '/api/users/fake-user-oid-1',
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
                },
                'partitions': [
                    {
                        'properties': {
                            'object-id': '1',
                            'name': 'partition_1',
                            'description': 'Partition #1 in CPC #2',
                            'status': 'stopped',
                            'hba-uris': [],   # updated automatically
                            'nic-uris': [],   # updated automatically
                            'virtual-function-uris': [],   # updated autom.
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
                            'detected-card-type': 'crypto-express-5s',
                            'crypto-number': 7,
                            'crypto-type': 'accelerator',
                        },
                    },
                ],
                'virtual_switches': [
                    {
                        'properties': {
                            'object-id': '1',
                            'name': 'vswitch_osa_1',
                            'description': 'Vswitch for OSA #1 in CPC #2',
                        },
                    },
                ],
            },
        ],
    }
    hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
    hmc.add_resources(hmc_resources)
    return hmc, hmc_resources


class TestGenericGetPropertiesHandler(object):
    """All tests for class GenericGetPropertiesHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)', GenericGetPropertiesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_get(self):

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
        }
        assert cpc1 == exp_cpc1

    def test_get_error_offline(self):

        self.hmc.disable()

        with pytest.raises(ConnectionError):
            # the function to be tested:
            self.urihandler.get(self.hmc, '/api/cpcs/1', True)


class _GenericGetUpdatePropertiesHandler(GenericGetPropertiesHandler,
                                         GenericUpdatePropertiesHandler):
    pass


class TestGenericUpdatePropertiesHandler(object):
    """All tests for class GenericUpdatePropertiesHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)', _GenericGetUpdatePropertiesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_update_verify(self):
        update_cpc1 = {
            'description': 'CPC #1 (updated)',
        }

        # the function to be tested:
        resp = self.urihandler.post(self.hmc, '/api/cpcs/1', update_cpc1, True,
                                    True)

        assert resp is None
        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['description'] == 'CPC #1 (updated)'

    def test_post_error_offline(self):

        self.hmc.disable()

        update_cpc1 = {
            'description': 'CPC #1 (updated)',
        }

        with pytest.raises(ConnectionError):
            # the function to be tested:
            self.urihandler.post(self.hmc, '/api/cpcs/1', update_cpc1, True,
                                 True)


class TestGenericDeleteHandler(object):
    """All tests for class GenericDeleteHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            ('/api/console/ldap-server-definitions/([^/]+)',
             GenericDeleteHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_delete(self):

        uri = '/api/console/ldap-server-definitions/fake-ldap-srv-def-oid-1'

        # the function to be tested:
        ret = self.urihandler.delete(self.hmc, uri, True)

        assert ret is None

        # Verify it no longer exists:
        with pytest.raises(KeyError):
            self.hmc.lookup_by_uri(uri)

    def test_delete_error_offline(self):

        self.hmc.disable()

        uri = '/api/console/ldap-server-definitions/fake-ldap-srv-def-oid-1'

        with pytest.raises(ConnectionError):
            # the function to be tested:
            self.urihandler.delete(self.hmc, uri, True)


class TestVersionHandler(object):
    """All tests for class VersionHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/version', VersionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_get_version(self):

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


class TestConsoleHandler(object):
    """All tests for class ConsoleHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console', ConsoleHandler),
        )
        self.urihandler = UriHandler(self.uris)

    # Note: There is no test_list() function because there is no List
    # operation for Console resources.

    def test_get(self):

        # the function to be tested:
        console = self.urihandler.get(self.hmc, '/api/console', True)

        exp_console = {
            'object-uri': '/api/console',
            'name': 'fake_console_name',
            'class': 'console',
            'parent': None,
        }
        assert console == exp_console


class TestConsoleRestartHandler(object):
    """All tests for class ConsoleRestartHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console', ConsoleHandler),
            ('/api/console/operations/restart', ConsoleRestartHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_restart_success(self):
        body = {
            'force': False,
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/operations/restart', body, True, True)

        assert self.hmc.enabled
        assert resp is None

    def test_restart_error_not_found(self):

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


class TestConsoleShutdownHandler(object):
    """All tests for class ConsoleShutdownHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console', ConsoleHandler),
            ('/api/console/operations/shutdown', ConsoleShutdownHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_shutdown_success(self):
        body = {
            'force': False,
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/operations/shutdown', body, True, True)

        assert not self.hmc.enabled
        assert resp is None

    def test_shutdown_error_not_found(self):

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


class TestConsoleMakePrimaryHandler(object):
    """All tests for class ConsoleMakePrimaryHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console', ConsoleHandler),
            ('/api/console/operations/make-primary',
             ConsoleMakePrimaryHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_make_primary_success(self):

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/operations/make-primary', None, True, True)

        assert self.hmc.enabled
        assert resp is None

    def test_make_primary_error_not_found(self):

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


class TestConsoleReorderUserPatternsHandler(object):
    """All tests for class ConsoleReorderUserPatternsHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        # Remove the standard User Pattern objects for this test
        console = self.hmc.lookup_by_uri('/api/console')
        user_pattern_objs = console.user_patterns.list()
        for obj in user_pattern_objs:
            console.user_patterns.remove(obj.oid)

        self.uris = (
            ('/api/console', ConsoleHandler),
            ('/api/console/user-patterns(?:\?(.*))?', UserPatternsHandler),
            ('/api/console/user-patterns/([^/]+)', UserPatternHandler),
            ('/api/console/operations/reorder-user-patterns',
             ConsoleReorderUserPatternsHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_reorder_all(self):
        testcases = [
            # (initial_order, new_order)
            (['a', 'b'], ['a', 'b']),
            (['a', 'b'], ['b', 'a']),
            (['a', 'b', 'c'], ['a', 'c', 'b']),
            (['a', 'b', 'c'], ['c', 'b', 'a']),
        ]
        for initial_order, new_order in testcases:
            self._test_reorder_one(initial_order, new_order)

    def _test_reorder_one(self, initial_order, new_order):

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
                'user-template-uri': 'fake-uri',
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

    def test_reorder_error_not_found(self):

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


class TestConsoleGetAuditLogHandler(object):
    """All tests for class ConsoleGetAuditLogHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console', ConsoleHandler),
            ('/api/console/operations/get-audit-log',
             ConsoleGetAuditLogHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_get_audit_log_success(self):

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/operations/get-audit-log', None, True,
            True)

        assert resp == []

    # TODO: Add testcases with non-empty audit log (once supported in mock)

    def test_get_audit_log_error_not_found(self):

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(
                self.hmc, '/api/console/operations/get-audit-log', None, True,
                True)

        exc = exc_info.value
        assert exc.reason == 1


class TestConsoleGetSecurityLogHandler(object):
    """All tests for class ConsoleGetSecurityLogHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console', ConsoleHandler),
            ('/api/console/operations/get-security-log',
             ConsoleGetSecurityLogHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_get_security_log_success_empty(self):

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/console/operations/get-security-log', None, True,
            True)

        assert resp == []

    # TODO: Add testcases with non-empty security log (once supported in mock)

    def test_get_security_log_error_not_found(self):

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.post(
                self.hmc, '/api/console/operations/get-security-log', None,
                True, True)

        exc = exc_info.value
        assert exc.reason == 1


class TestConsoleListUnmanagedCpcsHandler(object):
    """All tests for class ConsoleListUnmanagedCpcsHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console', ConsoleHandler),
            ('/api/console/operations/list-unmanaged-cpcs(?:\?(.*))?',
             ConsoleListUnmanagedCpcsHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list_success_empty(self):

        # the function to be tested:
        resp = self.urihandler.get(
            self.hmc, '/api/console/operations/list-unmanaged-cpcs', True)

        cpcs = resp['cpcs']
        assert cpcs == []

    # TODO: Add testcases for non-empty list of unmanaged CPCs

    def test_list_error_not_found(self):

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(
                self.hmc, '/api/console/operations/list-unmanaged-cpcs', True)

        exc = exc_info.value
        assert exc.reason == 1


class TestUserHandlers(object):
    """All tests for classes UsersHandler and UserHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console/users(?:\?(.*))?', UsersHandler),
            ('/api/users/([^/]+)', UserHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

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

    def test_list_error_console_not_found(self):

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(self.hmc, '/api/console/users', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_get(self):

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
        }
        assert user1 == exp_user1

    def test_create_verify(self):
        new_user2 = {
            'object-id': '2',
            'name': 'user_2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
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
        }

        # the function to be tested:
        user2 = self.urihandler.get(self.hmc, '/api/users/2', True)

        assert user2 == exp_user2

    def test_create_error_console_not_found(self):

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

    def test_update_verify(self):
        update_user1 = {
            'description': 'updated user #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/users/fake-user-oid-1',
                             update_user1, True, True)

        user1 = self.urihandler.get(self.hmc, '/api/users/fake-user-oid-1',
                                    True)
        assert user1['description'] == 'updated user #1'

    def test_delete_verify_all(self):
        testcases = [
            # (user_props, exp_exc_tuple)
            ({
                'object-id': '2',
                'name': 'user_2',
                'description': 'User #2',
                'type': 'standard',
                'authentication-type': 'local'},
             None),
            ({
                'object-id': '3',
                'name': 'user_3',
                'description': 'User #3',
                'type': 'template',
                'authentication-type': 'local'},
             None),
            ({
                'object-id': '4',
                'name': 'user_4',
                'description': 'User #4',
                'type': 'pattern-based',
                'authentication-type': 'local'},
             (400, 312)),
        ]
        for user_props, exp_exc_tuple in testcases:
            self._test_delete_verify_one(user_props, exp_exc_tuple)

    def _test_delete_verify_one(self, user_props, exp_exc_tuple):

        user_oid = user_props['object-id']
        user_uri = '/api/users/{}'.format(user_oid)

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


class TestUserAddUserRoleHandler(object):
    """All tests for class UserAddUserRoleHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        # Has a system-defined User (oid=fake-user-oid-1)
        # Has a system-defined User Role (oid=fake-user-role-oid-1)

        self.uris = (
            ('/api/console/users(?:\?(.*))?', UsersHandler),
            ('/api/users/([^/]+)', UserHandler),
            ('/api/users/([^/]+)/operations/add-user-role',
             UserAddUserRoleHandler),
            ('/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
            ('/api/user-roles/([^/]+)', UserRoleHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_add_success(self):
        """Test successful addition of a user role to a user."""

        # Add a user-defined User for our tests
        user2 = {
            'name': 'user2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
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

    def test_add_error_bad_user(self):
        """Test failed addition of a user role to a bad user."""

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

    def test_add_error_bad_user_role(self):
        """Test failed addition of a bad user role to a user."""

        # Add a user-defined User for our tests
        user2 = {
            'name': 'user2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
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


class TestUserRemoveUserRoleHandler(object):
    """All tests for class UserRemoveUserRoleHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        # Has a system-defined User (oid=fake-user-oid-1)
        # Has a system-defined User Role (oid=fake-user-role-oid-1)

        self.uris = (
            ('/api/console/users(?:\?(.*))?', UsersHandler),
            ('/api/users/([^/]+)', UserHandler),
            ('/api/users/([^/]+)/operations/add-user-role',
             UserAddUserRoleHandler),
            ('/api/users/([^/]+)/operations/remove-user-role',
             UserRemoveUserRoleHandler),
            ('/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
            ('/api/user-roles/([^/]+)', UserRoleHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_remove_success(self):
        """Test successful removal of a user role from a user."""

        # Add a user-defined User for our tests
        user2 = {
            'name': 'user2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
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

    def test_remove_error_bad_user(self):
        """Test failed removal of a user role from a bad user."""

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

    def test_remove_error_bad_user_role(self):
        """Test failed removal of a bad user role from a user."""

        # Add a user-defined User for our tests
        user2 = {
            'name': 'user2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
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

    def test_remove_error_no_user_role(self):
        """Test failed removal of a user role that a user does not have."""

        # Add a user-defined User for our tests
        user2 = {
            'name': 'user2',
            'description': 'User #2',
            'type': 'standard',
            'authentication-type': 'local',
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


class TestUserRoleHandlers(object):
    """All tests for classes UserRolesHandler and UserRoleHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
            ('/api/user-roles/([^/]+)', UserRoleHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

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
            ]
        }
        assert user_roles == exp_user_roles

    def test_list_error_console_not_found(self):

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(self.hmc, '/api/console/user-roles', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_get(self):

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
        }
        assert user_role1 == exp_user_role1

    def test_create_verify(self):
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

    def test_create_error_console_not_found(self):

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

    def test_create_error_type(self):

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

    def test_update_verify(self):
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

    def test_delete_verify(self):

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


class TestUserRoleAddPermissionHandler(object):
    """All tests for class UserRoleAddPermissionHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        # Has a system-defined User Role (oid=fake-user-role-oid-1)

        self.uris = (
            ('/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
            ('/api/user-roles/([^/]+)', UserRoleHandler),
            ('/api/user-roles/([^/]+)/operations/add-permission',
             UserRoleAddPermissionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_add_all(self):
        """All tests for adding permissions to a User Role."""
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
            self._test_add_one(input_permission, exp_permission)

    def _test_add_one(self, input_permission, exp_permission):

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

    def test_add_error_bad_user_role(self):
        """Test failed addition of a permission to a bad User Role."""

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

    def test_add_error_system_user_role(self):
        """Test failed addition of a permission to a system-defined User
        Role."""

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


class TestUserRoleRemovePermissionHandler(object):
    """All tests for class UserRoleRemovePermissionHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        # Has a system-defined User Role (oid=fake-user-role-oid-1)

        self.uris = (
            ('/api/console/user-roles(?:\?(.*))?', UserRolesHandler),
            ('/api/user-roles/([^/]+)', UserRoleHandler),
            ('/api/user-roles/([^/]+)/operations/add-permission',
             UserRoleAddPermissionHandler),
            ('/api/user-roles/([^/]+)/operations/remove-permission',
             UserRoleRemovePermissionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_remove_all(self):
        """All tests for removing permissions from a User Role."""
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
            self._test_remove_one(input_permission, removed_permission)

    def _test_remove_one(self, input_permission, removed_permission):

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

    def test_remove_error_bad_user_role(self):
        """Test failed removal of a permission from a bad User Role."""

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

    def test_remove_error_system_user_role(self):
        """Test failed removal of a permission from a system-defined User
        Role."""

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


class TestTaskHandlers(object):
    """All tests for classes TasksHandler and TaskHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console/tasks(?:\?(.*))?', TasksHandler),
            ('/api/console/tasks/([^/]+)', TaskHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

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

    def test_list_error_console_not_found(self):

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(self.hmc, '/api/console/tasks', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_get(self):

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


class TestUserPatternHandlers(object):
    """All tests for classes UserPatternsHandler and UserPatternHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console/user-patterns(?:\?(.*))?', UserPatternsHandler),
            ('/api/console/user-patterns/([^/]+)', UserPatternHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

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

    def test_list_error_console_not_found(self):

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(self.hmc, '/api/console/user-patterns', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_get(self):

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
            'user-template-uri': '/api/users/fake-user-oid-1',
        }
        assert user_pattern1 == exp_user_pattern1

    def test_create_verify(self):
        new_user_pattern_input = {
            'name': 'user_pattern_X',
            'description': 'User Pattern #X',
            'pattern': 'user*',
            'type': 'glob-like',
            'retention-time': 0,
            'user-template-uri': '/api/users/fake-user-oid-1',
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

    def test_create_error_console_not_found(self):

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

    def test_update_verify(self):
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

    def test_delete_verify(self):

        new_user_pattern_input = {
            'name': 'user_pattern_x',
            'description': 'User Pattern #X',
            'pattern': 'user*',
            'type': 'glob-like',
            'retention-time': 0,
            'user-template-uri': '/api/users/fake-user-oid-1',
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


class TestPasswordRuleHandlers(object):
    """All tests for classes PasswordRulesHandler and PasswordRuleHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console/password-rules(?:\?(.*))?', PasswordRulesHandler),
            ('/api/console/password-rules/([^/]+)', PasswordRuleHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

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

    def test_list_error_console_not_found(self):

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(self.hmc, '/api/console/password-rules', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_get(self):

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
        }
        assert password_rule1 == exp_password_rule1

    def test_create_verify(self):
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

    def test_create_error_console_not_found(self):

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

    def test_update_verify(self):
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

    def test_delete_verify(self):

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


class TestLdapServerDefinitionHandlers(object):
    """All tests for classes LdapServerDefinitionsHandler and
    LdapServerDefinitionHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()

        self.uris = (
            ('/api/console/ldap-server-definitions(?:\?(.*))?',
             LdapServerDefinitionsHandler),
            ('/api/console/ldap-server-definitions/([^/]+)',
             LdapServerDefinitionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

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

    def test_list_error_console_not_found(self):

        # Remove the faked Console object
        self.hmc.consoles.remove(None)

        with pytest.raises(InvalidResourceError) as exc_info:

            # the function to be tested:
            self.urihandler.get(
                self.hmc, '/api/console/ldap-server-definitions', True)

        exc = exc_info.value
        assert exc.reason == 1

    def test_get(self):

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
        }
        assert ldap_srv_def1 == exp_ldap_srv_def1

    def test_create_verify(self):
        new_ldap_srv_def_input = {
            'name': 'ldap_srv_def_X',
            'description': 'LDAP Srv Def #X',
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

    def test_create_error_console_not_found(self):

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

    def test_update_verify(self):
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

    def test_delete_verify(self):

        new_ldap_srv_def_input = {
            'name': 'ldap_srv_def_X',
            'description': 'LDAP Srv Def #X',
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


class TestCpcHandlers(object):
    """All tests for classes CpcsHandler and CpcHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs(?:\?(.*))?', CpcsHandler),
            (r'/api/cpcs/([^/]+)', CpcHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

        # the function to be tested:
        cpcs = self.urihandler.get(self.hmc, '/api/cpcs', True)

        exp_cpcs = {  # properties reduced to those returned by List
            'cpcs': [
                {
                    'object-uri': '/api/cpcs/1',
                    'name': 'cpc_1',
                    'status': 'operating',
                },
                {
                    'object-uri': '/api/cpcs/2',
                    'name': 'cpc_2',
                    'status': 'active',
                },
            ]
        }
        assert cpcs == exp_cpcs

    def test_get(self):

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
        }
        assert cpc1 == exp_cpc1

    def test_update_verify(self):
        update_cpc1 = {
            'description': 'updated cpc #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/cpcs/1',
                             update_cpc1, True, True)

        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['description'] == 'updated cpc #1'


class TestCpcSetPowerSaveHandler(object):
    """All tests for class CpcSetPowerSaveHandler."""

    def setup_method(self):
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
    def test_set_power_save(self, power_saving, exp_error):

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


class TestCpcSetPowerCappingHandler(object):
    """All tests for class CpcSetPowerCappingHandler."""

    def setup_method(self):
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
    def test_set_power_capping(self, power_capping_state, power_cap_current,
                               exp_error):

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


class TestCpcGetEnergyManagementDataHandler(object):
    """All tests for class CpcGetEnergyManagementDataHandler."""

    def setup_method(self):
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
    def test_get_energy_management_data(self, cpc_uri, energy_props):

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


class TestCpcStartStopHandler(object):
    """All tests for classes CpcStartHandler and CpcStopHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/start', CpcStartHandler),
            (r'/api/cpcs/([^/]+)/operations/stop', CpcStopHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_stop_classic(self):
        # CPC1 is in classic mode
        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['status'] == 'operating'

        # the function to be tested:
        with pytest.raises(CpcNotInDpmError):
            self.urihandler.post(self.hmc, '/api/cpcs/1/operations/stop',
                                 None, True, True)

        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['status'] == 'operating'

    def test_start_classic(self):
        # CPC1 is in classic mode
        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['status'] == 'operating'

        # the function to be tested:
        with pytest.raises(CpcNotInDpmError):
            self.urihandler.post(self.hmc, '/api/cpcs/1/operations/start',
                                 None, True, True)

        cpc1 = self.urihandler.get(self.hmc, '/api/cpcs/1', True)
        assert cpc1['status'] == 'operating'

    def test_stop_start_dpm(self):
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


class TestCpcExportPortNamesListHandler(object):
    """All tests for class CpcExportPortNamesListHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs(?:\?(.*))?', CpcsHandler),
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/export-port-names-list',
             CpcExportPortNamesListHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_no_input(self):

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/cpcs/2/operations/export-port-names-list',
                None, True, True)

    def test_invoke_ok(self):
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


class TestCpcImportProfilesHandler(object):
    """All tests for class CpcImportProfilesHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs(?:\?(.*))?', CpcsHandler),
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/import-profiles',
             CpcImportProfilesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_no_input(self):

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/cpcs/1/operations/import-profiles',
                None, True, True)

    def test_invoke_ok(self):
        operation_body = {
            'profile-area': 2,
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/cpcs/1/operations/import-profiles',
            operation_body, True, True)

        assert resp is None


class TestCpcExportProfilesHandler(object):
    """All tests for class CpcExportProfilesHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs(?:\?(.*))?', CpcsHandler),
            (r'/api/cpcs/([^/]+)', CpcHandler),
            (r'/api/cpcs/([^/]+)/operations/export-profiles',
             CpcExportProfilesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_no_input(self):

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/cpcs/1/operations/export-profiles',
                None, True, True)

    def test_invoke_ok(self):
        operation_body = {
            'profile-area': 2,
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/cpcs/1/operations/export-profiles',
            operation_body, True, True)

        assert resp is None


class TestMetricsContextHandlers(object):
    """All tests for classes MetricsContextsHandler and
    MetricsContextHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/services/metrics/context', MetricsContextsHandler),
            (r'/api/services/metrics/context/([^/]+)', MetricsContextHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_create_get_delete_context(self):

        mc_mgr = self.hmc.metrics_contexts

        # Prepare faked metric group definitions

        mg_name = 'partition-usage'
        mg_def = FakedMetricGroupDefinition(
            name=mg_name,
            types=[
                ('metric-1', 'string-metric'),
                ('metric-2', 'integer-metric'),
            ])
        mg_info = {
            'group-name': mg_name,
            'metric-infos': [
                {
                    'metric-name': 'metric-1',
                    'metric-type': 'string-metric',
                },
                {
                    'metric-name': 'metric-2',
                    'metric-type': 'integer-metric',
                },
            ],
        }
        mc_mgr.add_metric_group_definition(mg_def)

        mg_name2 = 'cpc-usage'
        mg_def2 = FakedMetricGroupDefinition(
            name=mg_name2,
            types=[
                ('metric-3', 'string-metric'),
                ('metric-4', 'integer-metric'),
            ])
        mg_info2 = {
            'group-name': mg_name2,
            'metric-infos': [
                {
                    'metric-name': 'metric-3',
                    'metric-type': 'string-metric',
                },
                {
                    'metric-name': 'metric-4',
                    'metric-type': 'integer-metric',
                },
            ],
        }
        mc_mgr.add_metric_group_definition(mg_def2)

        # Prepare faked metric values

        mo_val1_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid',
            timestamp=datetime(2017, 9, 5, 12, 13, 10, 0),
            values=[
                ('metric-1', "a"),
                ('metric-2', 5),
            ])
        mc_mgr.add_metric_values(mo_val1_input)

        mo_val2_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid',
            timestamp=datetime(2017, 9, 5, 12, 13, 20, 0),
            values=[
                ('metric-1', "b"),
                ('metric-2', -7),
            ])
        mc_mgr.add_metric_values(mo_val2_input)

        mo_val3_input = FakedMetricObjectValues(
            group_name=mg_name2,
            resource_uri='/api/cpcs/fake-oid',
            timestamp=datetime(2017, 9, 5, 12, 13, 10, 0),
            values=[
                ('metric-1', "c"),
                ('metric-2', 0),
            ])
        mc_mgr.add_metric_values(mo_val3_input)

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

        exp_mv_resp = '''"partition-usage"
"/api/partitions/fake-oid"
1504613590000
"a",5

"/api/partitions/fake-oid"
1504613600000
"b",-7


"cpc-usage"
"/api/cpcs/fake-oid"
1504613590000
"c",0



'''
        assert mv_resp == exp_mv_resp, \
            "Actual response string:\n{!r}\n" \
            "Expected response string:\n{!r}\n". \
            format(mv_resp, exp_mv_resp)

        # the delete function to be tested:
        self.urihandler.delete(self.hmc, uri, True)


class TestAdapterHandlers(object):
    """All tests for classes AdaptersHandler and AdapterHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/adapters(?:\?(.*))?', AdaptersHandler),
            (r'/api/adapters/([^/]+)', AdapterHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

        # the function to be tested:
        adapters = self.urihandler.get(self.hmc, '/api/cpcs/2/adapters', True)

        exp_adapters = {  # properties reduced to those returned by List
            'adapters': [
                {
                    'object-uri': '/api/adapters/1',
                    'name': 'osa_1',
                    'status': 'active',
                },
                {
                    'object-uri': '/api/adapters/2',
                    'name': 'fcp_2',
                    'status': 'active',
                },
                {
                    'object-uri': '/api/adapters/2a',
                    'name': 'fcp_2a',
                    'status': 'active',
                },
                {
                    'object-uri': '/api/adapters/3',
                    'name': 'roce_3',
                    'status': 'active',
                },
                {
                    'object-uri': '/api/adapters/4',
                    'name': 'crypto_4',
                    'status': 'active',
                },
            ]
        }
        assert adapters == exp_adapters

    def test_get(self):

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
        }
        assert adapter1 == exp_adapter1

    def test_update_verify(self):
        update_adapter1 = {
            'description': 'updated adapter #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/adapters/1',
                             update_adapter1, True, True)

        adapter1 = self.urihandler.get(self.hmc, '/api/adapters/1', True)
        assert adapter1['description'] == 'updated adapter #1'


class TestAdapterChangeCryptoTypeHandler(object):
    """All tests for class AdapterChangeCryptoTypeHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/adapters(?:\?(.*))?', AdaptersHandler),
            (r'/api/adapters/([^/]+)', AdapterHandler),
            (r'/api/adapters/([^/]+)/operations/change-crypto-type',
             AdapterChangeCryptoTypeHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_no_body(self):

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/adapters/4/operations/change-crypto-type',
                None, True, True)

    def test_invoke_err_no_crypto_type_field(self):

        operation_body = {
            # no 'crypto-type' field
        }

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/adapters/4/operations/change-crypto-type',
                operation_body, True, True)

    def test_invoke_ok(self):
        operation_body = {
            'crypto-type': 'cca-coprocessor',
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc,
            '/api/adapters/4/operations/change-crypto-type',
            operation_body, True, True)

        assert resp is None


class TestAdapterChangeAdapterTypeHandler(object):
    """All tests for class AdapterChangeAdapterTypeHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/adapters(?:\?(.*))?', AdaptersHandler),
            (r'/api/adapters/([^/]+)', AdapterHandler),
            (r'/api/adapters/([^/]+)/operations/change-adapter-type',
             AdapterChangeAdapterTypeHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_no_body(self):

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/adapters/2/operations/change-adapter-type',
                None, True, True)

    def test_invoke_err_no_type_field(self):

        operation_body = {
            # no 'type' field
        }

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/adapters/2/operations/change-adapter-type',
                operation_body, True, True)

    def test_invoke_ok(self):
        operation_body = {
            'type': 'fcp',
        }

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc,
            '/api/adapters/2/operations/change-adapter-type',
            operation_body, True, True)

        assert resp is None


class TestNetworkPortHandlers(object):
    """All tests for class NetworkPortHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/adapters/([^/]+)/network-ports/([^/]+)',
             NetworkPortHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_get(self):

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

    def test_update_verify(self):
        update_port1 = {
            'description': 'updated port #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/adapters/1/network-ports/1',
                             update_port1, True, True)

        port1 = self.urihandler.get(self.hmc,
                                    '/api/adapters/1/network-ports/1', True)
        assert port1['description'] == 'updated port #1'


class TestStoragePortHandlers(object):
    """All tests for class StoragePortHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/adapters/([^/]+)/storage-ports/([^/]+)',
             StoragePortHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_get(self):

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

    def test_update_verify(self):
        update_port1 = {
            'description': 'updated port #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/adapters/2/storage-ports/1',
                             update_port1, True, True)

        port1 = self.urihandler.get(self.hmc,
                                    '/api/adapters/2/storage-ports/1', True)
        assert port1['description'] == 'updated port #1'


class TestPartitionHandlers(object):
    """All tests for classes PartitionsHandler and PartitionHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/partitions(?:\?(.*))?', PartitionsHandler),
            (r'/api/partitions/([^/]+)', PartitionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

        # the function to be tested:
        partitions = self.urihandler.get(self.hmc, '/api/cpcs/2/partitions',
                                         True)

        exp_partitions = {  # properties reduced to those returned by List
            'partitions': [
                {
                    'object-uri': '/api/partitions/1',
                    'name': 'partition_1',
                    'status': 'stopped',
                },
            ]
        }
        assert partitions == exp_partitions

    def test_get(self):

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
            'hba-uris': ['/api/partitions/1/hbas/1'],
            'nic-uris': ['/api/partitions/1/nics/1'],
            'virtual-function-uris': ['/api/partitions/1/virtual-functions/1'],
        }
        assert partition1 == exp_partition1

    def test_create_verify(self):
        new_partition2 = {
            'object-id': '2',
            'name': 'partition_2',
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

        assert partition2 == exp_partition2

    def test_update_verify(self):
        update_partition1 = {
            'description': 'updated partition #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/partitions/1',
                             update_partition1, True, True)

        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        assert partition1['description'] == 'updated partition #1'

    def test_delete_verify(self):

        self.urihandler.get(self.hmc, '/api/partitions/1', True)

        # the function to be tested:
        self.urihandler.delete(self.hmc, '/api/partitions/1', True)

        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc, '/api/partitions/1', True)


class TestPartitionStartStopHandler(object):
    """All tests for classes PartitionStartHandler and PartitionStopHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/start',
             PartitionStartHandler),
            (r'/api/partitions/([^/]+)/operations/stop', PartitionStopHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_start_stop(self):
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


class TestPartitionScsiDumpHandler(object):
    """All tests for class PartitionScsiDumpHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/scsi-dump',
             PartitionScsiDumpHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_no_body(self):

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/scsi-dump',
                None, True, True)

    def test_invoke_err_missing_fields_1(self):
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

    def test_invoke_err_missing_fields_2(self):
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

    def test_invoke_err_missing_fields_3(self):
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

    def test_invoke_err_status_1(self):
        operation_body = {
            'dump-load-hba-uri': 'fake-uri',
            'dump-world-wide-port-name': 'fake-wwpn',
            'dump-logical-unit-number': 'fake-lun',
        }

        # Set the partition status to an invalid status for this operation
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1['status'] = 'stopped'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/scsi-dump',
                operation_body, True, True)

    def test_invoke_ok(self):
        operation_body = {
            'dump-load-hba-uri': 'fake-uri',
            'dump-world-wide-port-name': 'fake-wwpn',
            'dump-logical-unit-number': 'fake-lun',
        }

        # Set the partition status to a valid status for this operation
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1['status'] = 'active'

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/partitions/1/operations/scsi-dump',
            operation_body, True, True)

        assert resp == {}


class TestPartitionPswRestartHandler(object):
    """All tests for class PartitionPswRestartHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/psw-restart',
             PartitionPswRestartHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_status_1(self):

        # Set the partition status to an invalid status for this operation
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1['status'] = 'stopped'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/psw-restart',
                None, True, True)

    def test_invoke_ok(self):

        # Set the partition status to a valid status for this operation
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1['status'] = 'active'

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/partitions/1/operations/psw-restart',
            None, True, True)

        assert resp == {}


class TestPartitionMountIsoImageHandler(object):
    """All tests for class PartitionMountIsoImageHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/mount-iso-image(?:\?(.*))?',
             PartitionMountIsoImageHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_queryparm_1(self):

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/mount-iso-image?'
                'image-namex=fake-image&ins-file-name=fake-ins',
                None, True, True)

    def test_invoke_err_queryparm_2(self):

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/mount-iso-image?'
                'image-name=fake-image&ins-file-namex=fake-ins',
                None, True, True)

    def test_invoke_err_status_1(self):

        # Set the partition status to an invalid status for this operation
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1['status'] = 'starting'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/mount-iso-image?'
                'image-name=fake-image&ins-file-name=fake-ins',
                None, True, True)

    def test_invoke_ok(self):

        # Set the partition status to a valid status for this operation
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1['status'] = 'active'

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/partitions/1/operations/mount-iso-image?'
            'image-name=fake-image&ins-file-name=fake-ins',
            None, True, True)

        assert resp == {}

        boot_iso_image_name = partition1['boot-iso-image-name']
        assert boot_iso_image_name == 'fake-image'

        boot_iso_ins_file = partition1['boot-iso-ins-file']
        assert boot_iso_ins_file == 'fake-ins'


class TestPartitionUnmountIsoImageHandler(object):
    """All tests for class PartitionUnmountIsoImageHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/unmount-iso-image',
             PartitionUnmountIsoImageHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_status_1(self):

        # Set the partition status to an invalid status for this operation
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1['status'] = 'starting'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc, '/api/partitions/1/operations/unmount-iso-image',
                None, True, True)

    def test_invoke_ok(self):

        # Set the partition status to a valid status for this operation
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1['status'] = 'active'

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc, '/api/partitions/1/operations/unmount-iso-image',
            None, True, True)

        assert resp == {}

        boot_iso_image_name = partition1['boot-iso-image-name']
        assert boot_iso_image_name is None

        boot_iso_ins_file = partition1['boot-iso-ins-file']
        assert boot_iso_ins_file is None


class TestPartitionIncreaseCryptoConfigHandler(object):
    """All tests for class PartitionIncreaseCryptoConfigHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/'
             'increase-crypto-configuration',
             PartitionIncreaseCryptoConfigHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_missing_body(self):

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/increase-crypto-configuration',
                None, True, True)

    def test_invoke_err_status_1(self):

        # Set the partition status to an invalid status for this operation
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1['status'] = 'starting'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/increase-crypto-configuration',
                {}, True, True)

    def test_invoke_ok(self):

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
            partition1 = self.urihandler.get(
                self.hmc, '/api/partitions/1', True)
            partition1['status'] = 'active'

            # Set up the initial partition config
            partition1['crypto-configuration'] = None

            # the function to be tested:
            resp = self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/increase-crypto-configuration',
                operation_body, True, True)

            assert resp is None

            crypto_config = partition1['crypto-configuration']
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


class TestPartitionDecreaseCryptoConfigHandler(object):
    """All tests for class PartitionDecreaseCryptoConfigHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/'
             'decrease-crypto-configuration',
             PartitionDecreaseCryptoConfigHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_missing_body(self):

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/decrease-crypto-configuration',
                None, True, True)

    def test_invoke_err_status_1(self):

        # Set the partition status to an invalid status for this operation
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1['status'] = 'starting'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/decrease-crypto-configuration',
                {}, True, True)

    def test_invoke_ok(self):

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
            partition1 = self.urihandler.get(
                self.hmc, '/api/partitions/1', True)
            partition1['status'] = 'active'

            # Set up the initial partition config
            partition1['crypto-configuration'] = {
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

            crypto_config = partition1['crypto-configuration']
            assert isinstance(crypto_config, dict)

            adapter_uris = crypto_config['crypto-adapter-uris']
            assert isinstance(adapter_uris, list)

            domain_configs = crypto_config['crypto-domain-configurations']
            assert isinstance(domain_configs, list)


class TestPartitionChangeCryptoConfigHandler(object):
    """All tests for class PartitionChangeCryptoConfigHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/operations/'
             'change-crypto-domain-configuration',
             PartitionChangeCryptoConfigHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_missing_body(self):

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/'
                'change-crypto-domain-configuration',
                None, True, True)

    def test_invoke_err_missing_field_1(self):

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

    def test_invoke_err_missing_field_2(self):

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

    def test_invoke_err_status_1(self):

        # Set the partition status to an invalid status for this operation
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)
        partition1['status'] = 'starting'

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/operations/'
                'change-crypto-domain-configuration',
                {}, True, True)

    def test_invoke_ok(self):

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
            partition1 = self.urihandler.get(
                self.hmc, '/api/partitions/1', True)
            partition1['status'] = 'active'

            # Set up the initial partition config
            partition1['crypto-configuration'] = {
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

            crypto_config = partition1['crypto-configuration']
            assert isinstance(crypto_config, dict)

            adapter_uris = crypto_config['crypto-adapter-uris']
            assert isinstance(adapter_uris, list)

            domain_configs = crypto_config['crypto-domain-configurations']
            assert isinstance(domain_configs, list)


class TestHbaHandler(object):
    """All tests for classes HbasHandler and HbaHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/hbas(?:\?(.*))?', HbasHandler),
            (r'/api/partitions/([^/]+)/hbas/([^/]+)', HbaHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

        # the function to be tested:
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)

        hba_uris = partition1.get('hba-uris', [])

        exp_hba_uris = [
            '/api/partitions/1/hbas/1',
        ]
        assert hba_uris == exp_hba_uris

    def test_get(self):

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

    def test_create_verify(self):
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

    def test_update_verify(self):
        update_hba1 = {
            'description': 'updated hba #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/partitions/1/hbas/1',
                             update_hba1, True, True)

        hba1 = self.urihandler.get(self.hmc, '/api/partitions/1/hbas/1', True)
        assert hba1['description'] == 'updated hba #1'

    def test_delete_verify(self):

        self.urihandler.get(self.hmc, '/api/partitions/1/hbas/1', True)

        # the function to be tested:
        self.urihandler.delete(self.hmc, '/api/partitions/1/hbas/1', True)

        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc, '/api/partitions/1/hbas/1', True)


class TestHbaReassignPortHandler(object):
    """All tests for class HbaReassignPortHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/hbas/([^/]+)', HbaHandler),
            (r'/api/partitions/([^/]+)/hbas/([^/]+)'
             '/operations/reassign-storage-adapter-port',
             HbaReassignPortHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_err_missing_body(self):

        # the function to be tested:
        with pytest.raises(HTTPError):
            self.urihandler.post(
                self.hmc,
                '/api/partitions/1/hbas/1/operations/'
                'reassign-storage-adapter-port',
                None, True, True)

    def test_invoke_err_missing_field_1(self):
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

    def test_invoke_ok(self):
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


class TestNicHandler(object):
    """All tests for classes NicsHandler and NicHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/nics(?:\?(.*))?', NicsHandler),
            (r'/api/partitions/([^/]+)/nics/([^/]+)', NicHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

        # the function to be tested:
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)

        nic_uris = partition1.get('nic-uris', [])

        exp_nic_uris = [
            '/api/partitions/1/nics/1',
        ]
        assert nic_uris == exp_nic_uris

    def test_get(self):

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
        }
        assert nic1 == exp_nic1

    def test_create_verify(self):
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
        }

        assert nic2 == exp_nic2

    def test_update_verify(self):
        update_nic1 = {
            'description': 'updated nic #1',
        }

        # the function to be tested:
        self.urihandler.post(self.hmc, '/api/partitions/1/nics/1',
                             update_nic1, True, True)

        nic1 = self.urihandler.get(self.hmc, '/api/partitions/1/nics/1', True)
        assert nic1['description'] == 'updated nic #1'

    def test_delete_verify(self):

        self.urihandler.get(self.hmc, '/api/partitions/1/nics/1', True)

        # the function to be tested:
        self.urihandler.delete(self.hmc, '/api/partitions/1/nics/1', True)

        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc, '/api/partitions/1/nics/1', True)


class TestVirtualFunctionHandler(object):
    """All tests for classes VirtualFunctionsHandler and
    VirtualFunctionHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/partitions/([^/]+)', PartitionHandler),
            (r'/api/partitions/([^/]+)/virtual-functions(?:\?(.*))?',
             VirtualFunctionsHandler),
            (r'/api/partitions/([^/]+)/virtual-functions/([^/]+)',
             VirtualFunctionHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

        # the function to be tested:
        partition1 = self.urihandler.get(self.hmc, '/api/partitions/1', True)

        vf_uris = partition1.get('virtual-function-uris', [])

        exp_vf_uris = [
            '/api/partitions/1/virtual-functions/1',
        ]
        assert vf_uris == exp_vf_uris

    def test_get(self):

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
        }
        assert vf1 == exp_vf1

    def test_create_verify(self):
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

    def test_update_verify(self):
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

    def test_delete_verify(self):

        self.urihandler.get(self.hmc, '/api/partitions/1/virtual-functions/1',
                            True)

        # the function to be tested:
        self.urihandler.delete(self.hmc,
                               '/api/partitions/1/virtual-functions/1', True)

        with pytest.raises(InvalidResourceError):
            self.urihandler.get(self.hmc,
                                '/api/partitions/1/virtual-functions/1', True)


class TestVirtualSwitchHandlers(object):
    """All tests for classes VirtualSwitchesHandler and
    VirtualSwitchHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/virtual-switches(?:\?(.*))?',
             VirtualSwitchesHandler),
            (r'/api/virtual-switches/([^/]+)', VirtualSwitchHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

        # the function to be tested:
        vswitches = self.urihandler.get(self.hmc,
                                        '/api/cpcs/2/virtual-switches', True)

        exp_vswitches = {  # properties reduced to those returned by List
            'virtual-switches': [
                {
                    'object-uri': '/api/virtual-switches/1',
                    'name': 'vswitch_osa_1',
                    # status not set in resource -> not in response
                },
            ]
        }
        assert vswitches == exp_vswitches

    def test_get(self):

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
            'connected-vnic-uris': [],  # auto-generated
        }
        assert vswitch1 == exp_vswitch1


class TestVirtualSwitchGetVnicsHandler(object):
    """All tests for class VirtualSwitchGetVnicsHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/virtual-switches/([^/]+)', VirtualSwitchHandler),
            (r'/api/virtual-switches/([^/]+)/operations/get-connected-vnics',
             VirtualSwitchGetVnicsHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_invoke_ok(self):

        connected_nic_uris = ['/api/adapters/1/ports/1']

        # Set up the connected vNICs in the vswitch
        vswitch1 = self.urihandler.get(self.hmc, '/api/virtual-switches/1',
                                       True)
        vswitch1['connected-vnic-uris'] = connected_nic_uris

        # the function to be tested:
        resp = self.urihandler.post(
            self.hmc,
            '/api/virtual-switches/1/operations/get-connected-vnics',
            None, True, True)

        exp_resp = {
            'connected-vnic-uris': connected_nic_uris,
        }
        assert resp == exp_resp


class TestLparHandlers(object):
    """All tests for classes LparsHandler and LparHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/logical-partitions(?:\?(.*))?', LparsHandler),
            (r'/api/logical-partitions/([^/]+)', LparHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

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

    def test_get(self):

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


class TestLparActLoadDeactHandler(object):
    """All tests for classes LparActivateHandler, LparLoadHandler, and
    LparDeactivateHandler."""

    def setup_method(self):
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

    def test_start_stop(self):
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


class TestResetActProfileHandlers(object):
    """All tests for classes ResetActProfilesHandler and
    ResetActProfileHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/reset-activation-profiles(?:\?(.*))?',
             ResetActProfilesHandler),
            (r'/api/cpcs/([^/]+)/reset-activation-profiles/([^/]+)',
             ResetActProfileHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

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

    def test_get(self):

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


class TestImageActProfileHandlers(object):
    """All tests for classes ImageActProfilesHandler and
    ImageActProfileHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/image-activation-profiles/([^/]+)',
             ImageActProfileHandler),
            (r'/api/cpcs/([^/]+)/image-activation-profiles(?:\?(.*))?',
             ImageActProfilesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

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

    def test_get(self):

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


class TestLoadActProfileHandlers(object):
    """All tests for classes LoadActProfilesHandler and
    LoadActProfileHandler."""

    def setup_method(self):
        self.hmc, self.hmc_resources = standard_test_hmc()
        self.uris = (
            (r'/api/cpcs/([^/]+)/load-activation-profiles/([^/]+)',
             LoadActProfileHandler),
            (r'/api/cpcs/([^/]+)/load-activation-profiles(?:\?(.*))?',
             LoadActProfilesHandler),
        )
        self.urihandler = UriHandler(self.uris)

    def test_list(self):

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

    def test_get(self):

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
