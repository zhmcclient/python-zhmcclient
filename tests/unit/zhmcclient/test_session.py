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

"""
Unit tests for _session module.
"""


import time
import json
import re
from unittest import mock
import requests
import requests_mock
import pytest

from zhmcclient import Session, ParseError, Job, HTTPError, OperationTimeout, \
    ClientAuthError, DEFAULT_HMC_PORT

# Default value for the 'verify_cert' parameter of the Session class:
DEFAULT_VERIFY_CERT = True


# TODO: Test Session.get() in all variations (including errors)
# TODO: Test Session.post() in all variations (including errors)
# TODO: Test Session.delete() in all variations (including errors)

def mock_server_1(m):
    """
    Set up the mocked responses for a simple HMC server that supports
    logon and logoff.
    """
    m.register_uri('POST', '/api/sessions',
                   json={
                       'api-session': 'test-session-id',
                       'notification-topic': 'test-obj-topic.1',
                       'job-notification-topic': 'test-job-topic.1',
                       'session-credential':
                           'un8bu462g37aw9j0o8pltontz3szt35jh4b1qe2toxt6fkhl4',
                   },
                   headers={'X-Request-Id': 'fake-request-id'})
    m.register_uri('DELETE', '/api/sessions/this-session',
                   status_code=204)
    m.register_uri('GET', '/api/version',
                   json={
                       'api-major-version': 4,
                       'api-minor-version': 10,
                   })


@pytest.mark.parametrize(
    "host, userid, password, use_get_password, session_id, kwargs", [
        ('fake-host', None, None, False, None, {}),
        ('fake-host', 'fake-userid', None, False, None, {}),
        ('fake-host', 'fake-userid', 'fake-pw', False, None, {}),
        ('fake-host', 'fake-userid', 'fake-pw', True, None, {}),
        ('fake-host', 'fake-userid', 'fake-pw', True, None,
         {'port': 1234}),
        ('fake-host', 'fake-userid', 'fake-pw', True, None,
         {'verify_cert': True}),
    ]
)
def test_session_init(
        host, userid, password, use_get_password, session_id, kwargs):
    """Test initialization of Session object."""

    # TODO: Add support for input parameter: retry_timeout_config
    # TODO: Add support for input parameter: time_stats_keeper

    if use_get_password:
        def get_password(host, userid):
            pw = f'fake-pw-{host}-{userid}'
            return pw
    else:
        get_password = None

    session = Session(host, userid, password, session_id, get_password,
                      **kwargs)

    assert session.host == host
    assert session.userid == userid
    # pylint: disable=protected-access
    assert session._password == password
    assert session.session_id == session_id
    assert session.get_password == get_password
    assert session.port == kwargs.get('port', DEFAULT_HMC_PORT)
    assert session.verify_cert == kwargs.get('verify_cert', DEFAULT_VERIFY_CERT)

    assert session.headers['Content-type'] == 'application/json'
    assert session.headers['Accept'] == '*/*'

    if session_id is None:
        assert session.session is None
        assert 'X-API-Session' not in session.headers
        assert len(session.headers) == 3
        assert session.actual_host is None
        assert session.base_url is None
    else:
        assert isinstance(session.session, requests.Session)
        assert session.headers['X-API-Session'] == session_id
        assert len(session.headers) == 4
        assert session.actual_host == host
        base_url = f'https://{session.actual_host}:{session.port!s}'
        assert session.base_url == base_url


def test_session_repr():
    """Test Session.__repr__()."""

    session = Session('fake-host', 'fake-user', 'fake-pw')

    repr_str = repr(session)

    repr_str = repr_str.replace('\n', '\\n')
    # We check just the begin of the string:
    assert re.match(
        rf'^{session.__class__.__name__}\s+at\s+'
        rf'0x{id(session):08x}\s+\(\\n.*',
        repr_str)


@pytest.mark.parametrize(
    "host, userid, password, use_get_password, exp_exc", [
        ('fake-host', None, None, False, ClientAuthError),
        ('fake-host', 'fake-userid', None, False, ClientAuthError),
        ('fake-host', 'fake-userid', 'fake-pw', False, None),
        ('fake-host', 'fake-userid', 'fake-pw', True, None),
        ('fake-host', 'fake-userid', None, True, None),
    ]
)
def test_session_logon(
        host, userid, password, use_get_password, exp_exc):
    """Test Session.logon() (and also Session.is_logon())."""

    with requests_mock.Mocker() as m:

        mock_server_1(m)

        if use_get_password:
            get_password = mock.MagicMock()
            get_password.return_value = \
                f'fake-pw-{host}-{userid}'
        else:
            get_password = None

        # Create a session in logged-off state
        session = Session(host, userid, password, None, get_password)

        assert session.session_id is None
        assert 'X-API-Session' not in session.headers
        assert session.session is None

        logged_on = session.is_logon()
        assert not logged_on

        if exp_exc:
            try:

                # The code to be tested:
                session.logon()

            except exp_exc:
                pass

            logged_on = session.is_logon()
            assert not logged_on
        else:

            # The code to be tested:
            session.logon()

            assert session.session_id == 'test-session-id'
            assert 'X-API-Session' in session.headers
            assert isinstance(session.session, requests.Session)

            if get_password:
                if password is None:
                    get_password.assert_called_with(host, userid)
                    # pylint: disable=protected-access
                    assert session._password == get_password.return_value
                else:
                    get_password.assert_not_called()

            logged_on = session.is_logon()
            assert logged_on


def test_session_logoff():
    """Test Session.logoff() (and also Session.is_logon())."""

    with requests_mock.Mocker() as m:

        mock_server_1(m)

        # Create a session in logged-off state
        session = Session('fake-host', 'fake-userid', 'fake-pw')

        session.logon()

        logged_on = session.is_logon()
        assert logged_on

        # The code to be tested:
        session.logoff()

        assert session.session_id is None
        assert session.session is None
        assert 'X-API-Session' not in session.headers
        assert len(session.headers) == 3

        logged_on = session.is_logon()
        assert not logged_on


def _do_parse_error_logon(m, json_content, exp_msg_pattern, exp_line, exp_col):
    """
    Perform a session logon, and mock the provided (invalid) JSON content
    for the response so that a JSON parsing error is triggered.

    Assert that this is surfaced via a `zhmcclient.ParseError` exception,
    with the expected message (as a regexp pattern), line and column.
    """

    m.register_uri('POST', '/api/sessions',
                   content=json_content,
                   headers={'X-Request-Id': 'fake-request-id'})
    m.register_uri('GET', '/api/version',
                   json={
                       'api-major-version': 4,
                       'api-minor-version': 10,
                   })

    session = Session('fake-host', 'fake-user', 'fake-pw')

    exp_pe_pattern = \
        rf"^JSON parse error in HTTP response: {exp_msg_pattern}\. " \
        r"HTTP request: [^ ]+ [^ ]+\. " \
        r"Response status .*"

    with pytest.raises(ParseError) as exc_info:
        session.logon()
    exc = exc_info.value

    assert re.match(exp_pe_pattern, str(exc))
    assert exc.line == exp_line
    assert exc.column == exp_col


# TODO: Merge the next 3 test functions into one that is parametrized

@requests_mock.mock()
def test_session_logon_error_invalid_delim(*args):
    """
    Logon with invalid JSON response that has an invalid delimiter.
    """
    m = args[0]
    json_content = b'{\n"api-session"; "test-session-id"\n}'
    exp_msg_pattern = r"Expecting ':' delimiter: .*"
    exp_line = 2
    exp_col = 14
    _do_parse_error_logon(m, json_content, exp_msg_pattern, exp_line, exp_col)


@requests_mock.mock()
def test_session_logon_error_invalid_quotes(*args):
    """
    Logon with invalid JSON response that incorrectly uses single quotes.
    """
    m = args[0]
    json_content = b'{\'api-session\': \'test-session-id\'}'
    exp_msg_pattern = r"Expecting property name enclosed in double " \
        "quotes: .*"
    exp_line = 1
    exp_col = 2
    _do_parse_error_logon(m, json_content, exp_msg_pattern, exp_line, exp_col)


@requests_mock.mock()
def test_session_logon_error_extra_closing(*args):
    """
    Logon with invalid JSON response that has an extra closing brace.
    """
    m = args[0]
    json_content = b'{"api-session": "test-session-id"}}'
    exp_msg_pattern = r"Extra data: .*"
    exp_line = 1
    exp_col = 35
    _do_parse_error_logon(m, json_content, exp_msg_pattern, exp_line, exp_col)


def test_session_get_notification_topics():
    """
    This tests the 'Get Notification Topics' operation.
    """
    session = Session('fake-host', 'fake-user', 'fake-id')
    with requests_mock.mock() as m:
        # Because logon is deferred until needed, we perform it
        # explicitly in order to keep mocking in the actual test simple.
        m.post(
            '/api/sessions', json={
                'api-session': 'test-session-id',
                'notification-topic': 'test-obj-topic.1',
                'job-notification-topic': 'test-job-topic.1',
                'session-credential':
                    'un8bu462g37aw9j0o8pltontz3szt35jh4b1qe2toxt6fkhl4',
            })
        m.get(
            '/api/version', json={
                'api-major-version': 4,
                'api-minor-version': 10,
            })
        session.logon()
        gnt_uri = "/api/sessions/operations/get-notification-topics"
        gnt_result = {
            "topics": [
                {
                    'topic-name': 'ensadmin.145',
                    'topic-type': 'object-notification',
                },
                {
                    'topic-name': 'ensadmin.145job',
                    'topic-type': 'job-notification',
                },
                {
                    'topic-name': 'ensadmin.145aud',
                    'topic-type': 'audit-notification',
                },
                {
                    'topic-name': 'ensadmin.145sec',
                    'topic-type': 'security-notification',
                }
            ]
        }
        m.get(gnt_uri, json=gnt_result)

        result = session.get_notification_topics()

        assert result == gnt_result['topics']

        m.delete('/api/sessions/this-session', status_code=204)

        session.logoff()


def test_session_get_error_html_1():
    """
    This tests a dummy GET with a 500 response with HTML content.
    """
    session = Session('fake-host', 'fake-user', 'fake-id')
    with requests_mock.mock() as m:
        get_uri = "/api/version"
        get_resp_status = 500
        get_resp_content_type = 'text/html; charset=utf-8'
        get_resp_headers = {
            'content-type': get_resp_content_type,
        }
        get_resp_content = """\
<!doctype html public "-//IETF//DTD HTML 2.0//EN">\
 <html>\
<head>\
<title>Console Internal Error</title>\
 <link href="/skin/HMCskin.css" rel="stylesheet" type="text/css"/>\
</head>\
 <body>\
<h1>Console Internal Error</h1>\
<br><hr size="1" noshade>\
<h2>Details:</h2>\
<p><br>HTTP status code: 500\
<p><br>The server encountered an internal error that prevented it from\
 fulfilling this request.\
<p><br>\
<pre>javax.servlet.ServletException: Web Services are not enabled.
\tat com.ibm.hwmca.fw.api.ApiServlet.execute(ApiServlet.java:135)
\t. . .
</pre>\
<hr size="1" noshade>\
</body>\
</html>"""
        m.get(get_uri, text=get_resp_content, headers=get_resp_headers,
              status_code=get_resp_status)

        # The following expected results reflect what is done in
        # _session._result_object().

        exp_reason = 900
        exp_message = \
            "Console Configuration Error: " \
            "Web Services API is not enabled on the HMC."

        with pytest.raises(HTTPError) as exc_info:
            session.get(get_uri, logon_required=False)
        exc = exc_info.value

        assert exc.http_status == get_resp_status
        assert exc.reason == exp_reason
        assert exc.message == exp_message
        assert exc.request_uri.endswith(get_uri)
        assert exc.request_method == 'GET'


JOB_URI = '/api/jobs/fake-job-uri'


# TODO: Add parametrization to the next test function.

def test_job_init():
    """Test initialization of Job object."""
    session = Session('fake-host', 'fake-user', 'fake-pw')

    # Jobs exist only for POST, but we want to test that the specified HTTP
    # method comes back regardless:
    op_method = 'GET'

    op_uri = '/api/bla'

    job = Job(session, JOB_URI, op_method, op_uri)

    assert job.uri == JOB_URI
    assert job.session == session
    assert job.op_method == op_method
    assert job.op_uri == op_uri


# TODO: Merge the next 7 test functions into one that is parametrized

def test_job_check_incomplete():
    """Test check_for_completion() with incomplete job."""
    with requests_mock.mock() as m:
        mock_server_1(m)
        session = Session('fake-host', 'fake-user', 'fake-pw')
        op_method = 'POST'
        op_uri = '/api/foo'
        job = Job(session, JOB_URI, op_method, op_uri)
        query_job_status_result = {
            'status': 'running',
        }
        m.get(JOB_URI, json=query_job_status_result)
        m.delete(JOB_URI, status_code=204)

        job_status, op_result = job.check_for_completion()

        assert job_status == 'running'
        assert op_result is None


def test_job_check_complete_success_noresult():
    """Test check_for_completion() with successful complete job without
    result."""
    with requests_mock.mock() as m:
        mock_server_1(m)
        session = Session('fake-host', 'fake-user', 'fake-pw')
        op_method = 'POST'
        op_uri = '/api/foo'
        job = Job(session, JOB_URI, op_method, op_uri)
        query_job_status_result = {
            'status': 'complete',
            'job-status-code': 200,
            # 'job-reason-code' omitted because HTTP status good
            # 'job-results' is optional and is omitted
        }
        m.get(JOB_URI, json=query_job_status_result)
        m.delete(JOB_URI, status_code=204)

        job_status, op_result = job.check_for_completion()

        assert job_status == 'complete'
        assert op_result is None


def test_job_check_complete_success_result():
    """Test check_for_completion() with successful complete job with a
    result."""
    with requests_mock.mock() as m:
        mock_server_1(m)
        session = Session('fake-host', 'fake-user', 'fake-pw')
        op_method = 'POST'
        op_uri = '/api/foo'
        job = Job(session, JOB_URI, op_method, op_uri)
        exp_op_result = {
            'foo': 'bar',
        }
        query_job_status_result = {
            'status': 'complete',
            'job-status-code': 200,
            # 'job-reason-code' omitted because HTTP status good
            'job-results': exp_op_result,
        }
        m.get(JOB_URI, json=query_job_status_result)
        m.delete(JOB_URI, status_code=204)

        job_status, op_result = job.check_for_completion()

        assert job_status == 'complete'
        assert op_result == exp_op_result


def test_job_check_complete_error1():
    """Test check_for_completion() with complete job in error (1)."""
    with requests_mock.mock() as m:
        mock_server_1(m)
        session = Session('fake-host', 'fake-user', 'fake-pw')
        op_method = 'POST'
        op_uri = '/api/foo'
        job = Job(session, JOB_URI, op_method, op_uri)
        query_job_status_result = {
            'status': 'complete',
            'job-status-code': 500,
            'job-reason-code': 42,
            # no 'job-results' field (it is not guaranteed to be there)
        }

        m.get(JOB_URI, json=query_job_status_result)
        m.delete(JOB_URI, status_code=204)

        with pytest.raises(HTTPError) as exc_info:
            job.check_for_completion()
        exc = exc_info.value

        assert exc.http_status == 500
        assert exc.reason == 42
        assert exc.message is None


def test_job_check_complete_error2():
    """Test check_for_completion() with complete job in error (2)."""
    with requests_mock.mock() as m:
        mock_server_1(m)
        session = Session('fake-host', 'fake-user', 'fake-pw')
        op_method = 'POST'
        op_uri = '/api/foo'
        job = Job(session, JOB_URI, op_method, op_uri)
        query_job_status_result = {
            'status': 'complete',
            'job-status-code': 500,
            'job-reason-code': 42,
            'job-results': {},  # it is not guaranteed to have any content
        }

        m.get(JOB_URI, json=query_job_status_result)
        m.delete(JOB_URI, status_code=204)

        with pytest.raises(HTTPError) as exc_info:
            job.check_for_completion()
        exc = exc_info.value

        assert exc.http_status == 500
        assert exc.reason == 42
        assert exc.message is None


def test_job_check_complete_error3():
    """Test check_for_completion() with complete job in error (3)."""
    with requests_mock.mock() as m:
        mock_server_1(m)
        session = Session('fake-host', 'fake-user', 'fake-pw')
        op_method = 'POST'
        op_uri = '/api/foo'
        job = Job(session, JOB_URI, op_method, op_uri)
        query_job_status_result = {
            'status': 'complete',
            'job-status-code': 500,
            'job-reason-code': 42,
            'job-results': {
                # Content is not documented for the error case.
                # Some failures result in an 'error' field.
                'error': 'bla message',
            },
        }

        m.get(JOB_URI, json=query_job_status_result)
        m.delete(JOB_URI, status_code=204)

        with pytest.raises(HTTPError) as exc_info:
            job.check_for_completion()
        exc = exc_info.value

        assert exc.http_status == 500
        assert exc.reason == 42
        assert exc.message == 'bla message'


def test_job_check_complete_error4():
    """Test check_for_completion() with complete job in error (4)."""
    with requests_mock.mock() as m:
        mock_server_1(m)
        session = Session('fake-host', 'fake-user', 'fake-pw')
        op_method = 'POST'
        op_uri = '/api/foo'
        job = Job(session, JOB_URI, op_method, op_uri)
        query_job_status_result = {
            'status': 'complete',
            'job-status-code': 500,
            'job-reason-code': 42,
            'job-results': {
                # Content is not documented for the error case.
                # Some failures result in an 'message' field.
                'message': 'bla message',
            },
        }

        m.get(JOB_URI, json=query_job_status_result)
        m.delete(JOB_URI, status_code=204)

        with pytest.raises(HTTPError) as exc_info:
            job.check_for_completion()
        exc = exc_info.value

        assert exc.http_status == 500
        assert exc.reason == 42
        assert exc.message == 'bla message'


# TODO: Merge the next 3 test functions into one that is parametrized

def test_job_wait_complete1_success_result():
    """Test wait_for_completion() with successful complete job with a
    result."""
    with requests_mock.mock() as m:
        mock_server_1(m)
        session = Session('fake-host', 'fake-user', 'fake-pw')
        op_method = 'POST'
        op_uri = '/api/foo'
        job = Job(session, JOB_URI, op_method, op_uri)
        exp_op_result = {
            'foo': 'bar',
        }
        query_job_status_result = {
            'status': 'complete',
            'job-status-code': 200,
            # 'job-reason-code' omitted because HTTP status good
            'job-results': exp_op_result,
        }
        m.get(JOB_URI, json=query_job_status_result)
        m.delete(JOB_URI, status_code=204)

        op_result = job.wait_for_completion()

        assert op_result == exp_op_result


def test_job_wait_complete3_success_result():
    """Test wait_for_completion() with successful complete job with a
    result."""
    with requests_mock.mock() as m:
        mock_server_1(m)
        session = Session('fake-host', 'fake-user', 'fake-pw')
        op_method = 'POST'
        op_uri = '/api/foo'
        job = Job(session, JOB_URI, op_method, op_uri)
        exp_op_result = {
            'foo': 'bar',
        }
        m.get(JOB_URI,
              [
                  {'text': result_running_callback},
                  {'text': result_complete_callback},
              ])
        m.delete(JOB_URI, status_code=204)

        op_result = job.wait_for_completion()

        assert op_result == exp_op_result


def test_job_wait_complete3_timeout():
    """Test wait_for_completion() with timeout."""
    with requests_mock.mock() as m:
        mock_server_1(m)
        session = Session('fake-host', 'fake-user', 'fake-pw')
        op_method = 'POST'
        op_uri = '/api/foo'
        job = Job(session, JOB_URI, op_method, op_uri)
        m.get(JOB_URI,
              [
                  {'text': result_running_callback},
                  {'text': result_running_callback},
                  {'text': result_complete_callback},
              ])
        m.delete(JOB_URI, status_code=204)

        # Here we provoke a timeout, by setting the timeout to less than
        # the time it would take to return the completed job status.
        # The time it would take is the sum of the following:
        # - 2 * 1 s (1 s is the sleep time in Job.wait_for_completion(),
        #   and this happens before each repeated status retrieval)
        # - 3 * 1 s (1 s is the sleep time in result_*_callback() in this
        #   module, and this happens in each mocked status retrieval)
        # Because status completion is given priority over achieving the
        # timeout duration, the timeout value needed to provoke the
        # timeout exception needs to be shorter by the last status
        # retrieval (the one that completes the job), so 3 s is the
        # boundary for the timeout value.
        operation_timeout = 2.9
        try:
            start_time = time.time()
            job.wait_for_completion(operation_timeout=operation_timeout)
            duration = time.time() - start_time
            raise AssertionError(
                f"No OperationTimeout raised. Actual duration: {duration} s, "
                f"timeout: {operation_timeout} s")
        except OperationTimeout as exc:
            msg = exc.args[0]
            assert msg.startswith("Waiting for completion of job")


def result_running_callback(request, context):
    # pylint: disable=unused-argument
    """
    Callback function returning 'running' JSON.
    """
    job_result_running = {
        'status': 'running',
    }
    time.sleep(1)
    return json.dumps(job_result_running)


def result_complete_callback(request, context):
    # pylint: disable=unused-argument
    """
    Callback function returning 'complete' JSON.
    """
    exp_op_result = {
        'foo': 'bar',
    }
    job_result_complete = {
        'status': 'complete',
        'job-status-code': 200,
        # 'job-reason-code' omitted because HTTP status good
        'job-results': exp_op_result,
    }
    time.sleep(1)
    return json.dumps(job_result_complete)
