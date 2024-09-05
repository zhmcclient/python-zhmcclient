# Copyright 2023 IBM Corp. All Rights Reserved.
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
HTTP-mocked pytest fixtures for unit tests.

HTTP-mocked pytest fixtures can be used in cases where the zhmcclient mock
support is not implemented, to mock at the level of the HTTP requests and
responses instead.

Example use in a pytest test function that invokes a (hypothetical) method
``Cpc.xyz()``:

.. code-block:: python

    from tests.common.http_mocked_fixtures import http_mocked_session
    from tests.common.http_mocked_fixtures import http_mocked_cpc_dpm


    def test_cpc_xyz(http_mocked_cpc_dpm):

        uri = http_mocked_cpc_dpm.uri + '/operations/xyz'

        rm_adapter = requests_mock.Adapter(case_sensitive=True)
        with requests_mock.mock(adapter=rm_adapter) as m:

            m.post(uri, status_code=200)

            result = http_mocked_cpc.xyz()

            assert rm_adapter.called
            request_body = rm_adapter.last_request.json()
            assert request_body == ...
            assert result == ...
"""

import pytest
import requests_mock
import zhmcclient


@pytest.fixture(
    scope='module'
)
def http_mocked_session(request):  # noqa: F811
    # pylint: disable=unused-argument
    """
    Pytest fixture representing a HTTP-mocked zhmcclient session that is logged
    on.

    A test function parameter using this fixture resolves to a
    :class:`~zhmcclient.Session` object that is logged on.
    """

    session = zhmcclient.Session(
        host='test-hmc', userid='test-user', password='test-pwd',
        verify_cert=False)

    with requests_mock.mock() as m:
        # Because logon is deferred until needed, we perform it
        # explicitly in order to keep mocking in the actual test simple.
        m.post('/api/sessions', status_code=200, json={
            'api-session': 'test-session-id.1',
            'notification-topic': 'test-obj-topic.1',
            'job-notification-topic': 'test-job-topic.1',
            'api-major-version': 4,
            'api-minor-version': 10,
            'password-expires': 90,
            'session-credential':
                'un8bu462g37aw9j0o8pltontz3szt35jh4b1qe2toxt6fkhl4'
        })
        m.get(
            '/api/version', json={
                'api-major-version': 4,
                'api-minor-version': 10,
            })
        session.logon()

    yield session

    with requests_mock.mock() as m:
        m.delete('/api/sessions/this-session', status_code=204)
        session.logoff()


@pytest.fixture(
    scope='module'
)
def http_mocked_cpc_dpm(request, http_mocked_session):  # noqa: F811
    # pylint: disable=unused-argument,redefined-outer-name
    """
    Pytest fixture representing a HTTP-mocked CPC in DPM mode.

    A test function parameter using this fixture resolves to a
    :class:`~zhmcclient.Cpc` object that is in DPM mode but has only a minimal
    set of properties in the object (those that are returned with the 'List
    CPCs' operation).
    """

    client = zhmcclient.Client(http_mocked_session)

    with requests_mock.mock() as m:
        m.get('/api/cpcs', status_code=200, json={
            'cpcs': [
                {
                    'object-uri': '/api/cpcs/cpc-id-1',
                    'name': 'CPC1',
                    'status': 'active',
                    'has-unacceptable-status': False,
                    'dpm-enabled': True,
                    'se-version': '2.16.0',
                }
            ]
        })
        cpcs = client.cpcs.list()
        cpc = cpcs[0]

    return cpc


@pytest.fixture(
    scope='module'
)
def http_mocked_cpc_classic(request, http_mocked_session):  # noqa: F811
    # pylint: disable=unused-argument,redefined-outer-name
    """
    Pytest fixture representing a HTTP-mocked CPC in classic mode.

    A test function parameter using this fixture resolves to a
    :class:`~zhmcclient.Cpc` object that is in classic mode but has only a
    minimal set of properties in the object (those that are returned with the
    'List CPCs' operation).
    """

    client = zhmcclient.Client(http_mocked_session)

    with requests_mock.mock() as m:
        m.get('/api/cpcs', status_code=200, json={
            'cpcs': [
                {
                    'object-uri': '/api/cpcs/cpc-id-2',
                    'name': 'CPC2',
                    'status': 'operating',
                    'has-unacceptable-status': False,
                    'dpm-enabled': False,
                    'se-version': '2.16.0',
                }
            ]
        })
        cpcs = client.cpcs.list()
        cpc = cpcs[0]

    return cpc


@pytest.fixture(
    scope='module'
)
def http_mocked_lpar(request, http_mocked_cpc_classic):  # noqa: F811
    # pylint: disable=unused-argument,redefined-outer-name
    """
    Pytest fixture representing a HTTP-mocked LPAR on a CPC in classic mode.

    Its CPC object can be accessed as the parent object.

    A test function parameter using this fixture resolves to a
    :class:`~zhmcclient.Lpar` object that has only a
    minimal set of properties in the object (those that are returned with the
    'List Logical Partitions of CPC' operation).
    """

    with requests_mock.mock() as m:
        uri = http_mocked_cpc_classic.uri + '/logical-partitions'
        m.get(uri, status_code=200, json={
            'logical-partitions': [
                {
                    'object-uri': '/api/logical-partitions/lpar-id-1',
                    'name': 'LPAR1',
                    'status': 'operating',
                }
            ]
        })
        lpars = http_mocked_cpc_classic.lpars.list()
        lpar = lpars[0]

    return lpar


@pytest.fixture(
    scope='module'
)
def http_mocked_partition(request, http_mocked_cpc_dpm):  # noqa: F811
    # pylint: disable=unused-argument,redefined-outer-name
    """
    Pytest fixture representing a HTTP-mocked Partition on a CPC in DPM mode.

    Its CPC object can be accessed as the parent object.

    A test function parameter using this fixture resolves to a
    :class:`~zhmcclient.Partition` object that has only a
    minimal set of properties in the object (those that are returned with the
    'List Partitions of CPC' operation).
    """

    with requests_mock.mock() as m:
        uri = http_mocked_cpc_dpm.uri + '/partitions'
        m.get(uri, status_code=200, json={
            'partitions': [
                {
                    'object-uri': '/api/partitions/part-id-1',
                    'name': 'PART1',
                    'status': 'active',
                }
            ]
        })
        partitions = http_mocked_cpc_dpm.partitions.list()
        partition = partitions[0]

    return partition


@pytest.fixture(
    scope='module'
)
def http_mocked_console(request, http_mocked_session):  # noqa: F811
    # pylint: disable=unused-argument,redefined-outer-name
    """
    Pytest fixture representing a HTTP-mocked HMC console.

    A test function parameter using this fixture resolves to a
    :class:`~zhmcclient.Console` object representing the HMC the session
    was opened against, that has only a subset of its properties in the object.
    """

    client = zhmcclient.Client(http_mocked_session)

    with requests_mock.mock() as m:
        m.get('/api/console', status_code=200, json={
            'object-uri': '/api/console',
            'parent': None,
            'class': 'console',
            'name': 'HMC1',
            'description': None,
            'version': '2.16.0',
            # 'ec-mcl-description':
            # 'network-info':
            # 'machine-info':
            # 'cpc-machine-info':
            'has-hardware-messages': False,
            'hardware-messages': [],
            # 'mobile-app-preferences':
            'sna-name': None,
            'shutdown-in-process': False,
            'shutdown-delay-allowed': False,
            'shutdown-delay-remaining': 0,
            'shutdown-delay-apps': [],
            'shutdown-delay-disable-reasons': [],
            'hma-info': {
                'peer-hmc': None,
            }
        })
        consoles = client.consoles.list(full_properties=True)
        console = consoles[0]

    return console
