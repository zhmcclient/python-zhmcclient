# Copyright 2026 IBM Corp. All Rights Reserved.
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
This conftest.py module treats the test_*.yaml files in this directory as test
files and runs the function testcases defined in them.

See
https://docs.pytest.org/en/latest/writing_plugins.html#local-conftest-plugins.
for details about conftest.py modules.

A test file in this directory defines one or more testcases. Each testcase
specifies a single zhmcclient API method call and return value or a single
zhmcclient API property access, and the corresponding HMC interactions with
their HTTP requests and responses.

When running a testcase, the zhmcclient API method for the specified zhmcclient
resource object will be invoked with the specified input parameters, or the
zhmcclient API property will be accessed. The zhmcclient library will process
that with zero or more HMC interactions.
The set of HMC interactions specified in the testcase defines the expected
interactions. The HTTP request in each HMC interaction defines the expected
request and that is compared against the actual request made by the zhmcclient
library. The corresponding HTTP response defined in the testcase is then
provided to the zhmcclient library. After performing all HMC interactions, the
zhmcclient API method returns and the return value defined in the testcase
is used to validate the actual return value.

The testcase syntax allows specifying error cases and success cases.

This allows testing the entire zhmcclient layer down to where it calls the
"requests" module for the HTTP interactions.

The test file format is described in schemas/test_file.schema.yaml.
"""

import re
import pathlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from immutabledict import immutabledict
import yaml
import pytest
import requests_mock
import requests
import jsonschema

import zhmcclient


# Enable for debugging this module with debug prints
DEBUG = False


def pytest_collect_file(parent, file_path):
    """
    pytest hook that is called for each file in the directory subtree with
    conftest.py, to collect its YAML test files.

    This function collects only the "test_*.yaml" files, except for any
    files in the "schemas" directory.

    For a similar example, see
    https://docs.pytest.org/en/latest/example/nonpython.html

    Parameters:

      parent (_pytest.python.Package): Pytest parent node (directory).

      file_path (pathlib.Path): Path name of a file in the directory
        subtree.

    Returns:

      YamlFile: Treat this file as a YAML test file.
      None: Skip this file.
    """
    if not file_path.match("test_*.yaml"):
        # Skip this file
        return None

    if file_path.parent.name == "schemas":
        # Skip any schema files
        return None

    return YamlFile.from_parent(parent, path=file_path)


class YamlFile(pytest.File):
    """
    pytest testcase collector class whose objects represent a YAML test file.
    """

    def collect(self):
        """
        Called by pytest to collect the testcases for a YAML test file.

        Yields:

          YamlItem: A testcase.
        """
        with self.path.open(encoding='utf-8') as fp:
            # Path name of test file, relative to current directory
            filepath = cwdpath(self.path)

            try:
                testfile_content = yaml.safe_load(fp)
            except (yaml.parser.ParserError, yaml.scanner.ScannerError) as exc:
                raise pytest.Collector.CollectError(
                    f"Cannot load test file {filepath}: {exc}")

            schema, schema_file = get_test_schema(self.parent.config)
            try:
                jsonschema.validate(testfile_content, schema)
            except jsonschema.exceptions.SchemaError as exc:
                elem_path = get_json_path(exc.absolute_path)
                schema_path = get_json_path(exc.absolute_schema_path)
                raise pytest.Collector.CollectError(
                    f"The JSON schema in {schema_file} is invalid: "
                    f"Element {elem_path!r} violates schema item "
                    f"{schema_path!r} in the JSON meta-schema. Details: "
                    f"Validator: {exc.validator}={exc.validator_value}"
                )
            except jsonschema.exceptions.ValidationError as exc:
                elem_path = get_json_path(exc.absolute_path)
                schema_path = get_json_path(exc.absolute_schema_path)
                raise pytest.Collector.CollectError(
                    f"Test file {filepath} does not conform to the test file "
                    f"schema, it failed on element {elem_path}: {exc.message}. "
                    f"Details: Schema item: {schema_path}, "
                    f"Validator: {exc.validator}={exc.validator_value}"
                )

            tf_setup = testfile_content.get("setup", None)
            try:
                testcases = testfile_content["testcases"]
            except KeyError:
                raise pytest.Collector.CollectError(
                    f"Test file {filepath} does not specify 'testcases'")
            for i, testcase in enumerate(testcases):
                try:
                    name = testcase['name']
                except KeyError:
                    raise pytest.Collector.CollectError(
                        f"Testcase #{i + 1} in test file {filepath} does not "
                        "have a 'name' property")
                testcase_data = TestcaseData(testcase, tf_setup, filepath)
                yield YamlItem.from_parent(
                    parent=self, name=name, testcase_data=testcase_data)


@dataclass
class TestcaseData:
    """
    Data class that holds the data for a testcase.

    An object of this class is added as an attribute to the YamlItem, and this
    class provides namespace isolation to any attributes inherited by the
    pytest base class of YamlItem.
    """

    testcase: dict  # The testcase item from the test file.
    tf_setup: dict  # The file-level setup item from the test file.
    filepath: Path  # Path name of test file.


class YamlItem(pytest.Item):
    """
    pytest testcase collector class whose objects represents a testcase within
    a YAML test file.
    """

    def __init__(self, parent, name, testcase_data):
        """
        Parameters:

          parent (YamlFile): Pytest parent node (YAML test file).

          name (string): Name of the testcase in the test file.

          testcase_data (TestcaseData): The testcase data.
        """
        super().__init__(name=name, parent=parent)
        # self.parent = parent, set by superclass
        # self.name = name, set by superclass
        self.testcase_data = testcase_data

    def runtest(self):
        """
        Called by pytest to run this testcase.
        """
        runtestcase(self.testcase_data)

    def repr_failure(self, excinfo, style=None):
        # pylint: disable=no-self-use
        """
        Called by pytest when the runtest() method raised an exception, to
        provide details about the failure.

        Parameters:

          excinfo (pytest.ExceptionInfo): Exception info.

          style (_pytest._code.code.TracebackStyle): Traceback style:
            "long", "short", "line", "no", "native", "value", "auto"
        """
        exc = excinfo.value

        if isinstance(exc, AssertionError):
            # Show an assertion error only with the deepest function
            tb = excinfo.traceback[-1:]
            excinfo = pytest.ExceptionInfo.from_exc_info(
                (excinfo.type, excinfo.value, tb))
            return excinfo.getrepr(
                showlocals=False, style="short", abspath=False, chain=False)

        if isinstance(exc, TestcaseDefinitionError):
            return f"Testcase definition error: {exc}"

        # Some programming error, will be shown with Python-like traceback
        return super().repr_failure(excinfo, "native")

    def reportinfo(self):
        """
        Called by pytest when the testcase failed, to provide information
        about the testcase. The third tuple item is a string that
        identifies the testcase in a human readable way.
        """
        return self.path, 0, f"{self.name} in {self.testcase_data.filepath}"


def runtestcase(testcase_data):
    """
    Run a single testcase.

    If the testcase passes, this function returns.
    If the testcase fails, it raises an exception.

    Parameters:

      testcase_data (TestcaseData): The testcase data from the test file.

    Raises:

      TestcaseDefinitionError: Invalid testcase definition.
      AssertionError: Failure running the testcase.
    """
    testcase = deepcopy(testcase_data.testcase)
    tf_setup = deepcopy(testcase_data.tf_setup)
    # filepath = deepcopy(testcase_data.filepath)

    tc_skip = tc_getitem("", testcase, "skip", None)
    if tc_skip is not None:
        pytest.skip(tc_skip)

    tc_debug = tc_getitem("", testcase, "debug", False)

    # tc_desc = tc_getitem("", testcase, "description")
    zhmcclient_call = tc_getitem("", testcase, "zhmcclient_call")
    zhmcclient_result = tc_getitem("", testcase, "zhmcclient_result")
    tc_setup = tc_getitem("", testcase, "setup", None)

    if tf_setup is not None:
        session_kwargs = tc_getitem("setup(tf)", tf_setup, "session", {})
        resources_spec = tc_getitem("setup(tf)", tf_setup, "resources", [])
    else:
        session_kwargs = {}
        resources_spec = []

    if tc_setup is not None:
        tc_session_kwargs = tc_getitem("setup", tc_setup, "session", {})
        tc_resources_spec = tc_getitem("setup", tc_setup, "resources", [])
        session_kwargs.update(tc_session_kwargs)
        resources_spec.extend(tc_resources_spec)

    # Keep these defaults in sync with the schema defaults
    session_kwargs.setdefault("host", "hmc-host")
    session_kwargs.setdefault("userid", "hmc-userid")
    session_kwargs.setdefault("password", "hmc-password")
    session_kwargs.setdefault("session_id", "hmc-session-id")

    session = zhmcclient.Session(**session_kwargs)
    client = zhmcclient.Client(session)

    # Create the resource objects defined in setup
    resource_by_uri = {}  # Lookup dict for all resources
    if resources_spec:
        create_setup_resources(
            "setup.resources(tf+tc)", resources_spec, client, resource_by_uri)

    hmc_interactions = tc_getitem("", testcase, "hmc_interactions", [])

    # Setup requests_mock for the HMC interactions. This will produce
    # the specified HTTP responses.
    mock_adapter = requests_mock.Adapter()

    # Because requests_mock.Adapter maintains a history of only the last
    # interactions, we need to record the interaction history ourselves.
    recorded_requests = []  # Items are requests.Response

    for i, hmc_interaction in enumerate(hmc_interactions):
        int_loc = f"hmc_interactions[{i}]"
        http_request = tc_getitem(int_loc, hmc_interaction, "http_request")
        http_response = tc_getitem(int_loc, hmc_interaction, "http_response")

        req_loc = f"hmc_interactions[{i}].http_request"
        method = tc_getitem(req_loc, http_request, "method")
        uri = tc_getitem(req_loc, http_request, "uri")

        resp_loc = f"hmc_interactions[{i}].http_response"
        resp_callback = tc_getitem(resp_loc, http_response, "callback", None)
        resp_status = tc_getitem(resp_loc, http_response, "status", None)

        if not ((resp_callback is None) ^ (resp_status is None)):
            raise TestcaseDefinitionError(
                f"'{resp_loc}' must specify exactly one of 'callback' or "
                "'status'.")

        if resp_callback is not None:
            # Register a callback function that provides the response data
            # or raises an exception.
            try:
                callback_func = getattr(ResponseCallbacks(), resp_callback)
            except AttributeError as exc:
                raise TestcaseDefinitionError(
                    f"'{resp_loc}.callback' specifies an unknown callback "
                    f"function: {resp_callback}") from exc

            callback = make_callback_for_callback(
                recorded_requests, callback_func)
            mock_adapter.register_uri(
                method=method, url=uri, content=callback)

        else:
            assert resp_status is not None
            # Register the response data directly.
            resp_headers = tc_getitem(resp_loc, http_response, "headers", {})
            body_spec = tc_getitem(resp_loc, http_response, "body", None)
            resp_body = body_from_spec(f"{resp_loc}.body", body_spec)

            callback = make_callback_for_direct(
                recorded_requests, resp_status, resp_body, resp_headers)
            mock_adapter.register_uri(
                method=method, url=uri, content=callback, complete_qs=True)

    call_loc = "zhmcclient_call"
    attr_name = tc_getitem(call_loc, zhmcclient_call, "attribute", None)
    prop_name = tc_getitem(call_loc, zhmcclient_call, "property", None)
    meth_name = tc_getitem(call_loc, zhmcclient_call, "method", None)
    meth_parms = tc_getitem(call_loc, zhmcclient_call, "parameters", {})

    if not ((prop_name is None) ^ (meth_name is None)):
        raise TestcaseDefinitionError(
            f"'{call_loc}' must specify exactly one of 'property' or "
            "'method'.")

    # Create the target resource or manager object
    target_spec = tc_getitem(call_loc, zhmcclient_call, "target")
    target_obj = get_target_object(
        f"{call_loc}.target", target_spec, resource_by_uri)

    if attr_name is not None:
        try:
            target_obj = getattr(target_obj, attr_name)
        except AttributeError as exc:
            raise TestcaseDefinitionError(
                f"'{call_loc}.attribute' specifies a non-existing attribute "
                f"on the zhmcclient.{target_obj.__class__.__name__} object: "
                f"{attr_name}") from exc

    exception = tc_getitem(
        "zhmcclient_result", zhmcclient_result, "exception", None)
    if exception is not None:
        exc_loc = "zhmcclient_result.exception"
        exp_exc_class_name = tc_getitem(exc_loc, exception, "class")
        exp_exc_msg_pat = tc_getitem(
            exc_loc, exception, "message_pattern", None)
        exp_exc_attrs = tc_getitem(exc_loc, exception, "attributes", {})
    else:
        exp_exc_class_name = None
        exp_exc_msg_pat = None
        exp_exc_attrs = None

    # Enable the mocking of requests
    session.session.mount("https://", mock_adapter)

    # Perform the call to zhmcclient code to be tested
    if prop_name is not None:
        msg_intro = ("Accessing property "
                     f"zhmcclient.{target_obj.__class__.__name__}.{prop_name}")

        # We split the access into a check for presence of the property and
        # accessing the properry, to make sure AttributeErrors raised when
        # accessing are not misinterpreted as a missing property.
        if not hasattr(target_obj, prop_name):
            raise TestcaseDefinitionError(
                f"'{call_loc}.attribute' specifies a non-existing property "
                f"on the zhmcclient.{target_obj.__class__.__name__} object: "
                f"{prop_name}")

        try:
            try:
                if tc_debug:
                    breakpoint()  # pylint: disable=forgotten-debug-statement

                # Run the zhmcclient code (access the property)
                result = getattr(target_obj, prop_name)

            except Exception as exc:  # pylint: disable=broad-exception-caught
                exc_class_name = exc.__class__.__name__
                if exception is None:
                    raise AssertionError(
                        f"{msg_intro} was expected to succeed but raised an "
                        f"exception: {exc_class_name}: {exc}") from exc

                assert exc_class_name == exp_exc_class_name
                if exp_exc_msg_pat is not None:
                    assert re.search(exp_exc_msg_pat, str(exc))
                for name, exp_value in exp_exc_attrs.items():
                    assert hasattr(exc, name)
                    value = getattr(exc, name)
                    assert exp_value == value
            else:
                if exception is not None:
                    raise AssertionError(
                        f"{msg_intro} was expected to raise exception "
                        f"{exp_exc_class_name} but succeeded")

        except requests_mock.exceptions.NoMockAddress as exc:
            request = exc.args[0]
            raise AssertionError(
                f"{msg_intro} performed an unexpected HTTP "
                f"request: {request}") from exc

    else:
        assert meth_name is not None
        msg_intro = ("Calling method zhmcclient."
                     f"{target_obj.__class__.__name__}.{meth_name}()")

        try:
            bound_method = getattr(target_obj, meth_name)
        except AttributeError as exc:
            raise TestcaseDefinitionError(
                f"'{call_loc}.method' specifies a non-existing method "
                f"on the zhmcclient.{target_obj.__class__.__name__} object: "
                f"{meth_name}") from exc

        # Prepare the method parameters
        for name, value_spec in meth_parms.items():
            if isinstance(value_spec, dict) and (
                    "_resource" in value_spec or
                    "_manager" in value_spec):
                parm_loc = f"{call_loc}.parameters.{name}"
                value = resolve_value_spec(
                    parm_loc, value_spec, resource_by_uri)
                meth_parms[name] = value

        try:
            try:
                if tc_debug:
                    breakpoint()  # pylint: disable=forgotten-debug-statement

                # Run the zhmcclient code (call the zhmcclient method)
                result = bound_method(**meth_parms)

            except Exception as exc:  # pylint: disable=broad-exception-caught
                exc_class_name = exc.__class__.__name__
                if exception is None:
                    raise AssertionError(
                        f"{msg_intro} was expected to succeed but raised an "
                        f"exception: {exc_class_name}: {exc}") from exc

                assert exc_class_name == exp_exc_class_name
                if exp_exc_msg_pat is not None:
                    assert re.search(exp_exc_msg_pat, str(exc))
                for name, exp_value in exp_exc_attrs.items():
                    assert hasattr(exc, name)
                    value = getattr(exc, name)
                    assert exp_value == value
            else:
                if exception is not None:
                    raise AssertionError(
                        f"{msg_intro} was expected to raise exception "
                        f"{exp_exc_class_name} but succeeded")

        except requests_mock.exceptions.NoMockAddress as exc:
            request = exc.args[0]
            raise AssertionError(
                f"{msg_intro} performed an unexpected HTTP "
                f"request: {request}") from exc

    if exception is None:

        if DEBUG:
            print(f"Debug: result={result!r}")

        # Validate the HTTP requests issued by the zhmcclient code
        if hmc_interactions:
            assert len(recorded_requests) == len(hmc_interactions)
            for i, hmc_interaction in enumerate(hmc_interactions):
                history_item = recorded_requests[i]

                int_loc = f"hmc_interactions[{i}]"
                http_request = tc_getitem(
                    int_loc, hmc_interaction, "http_request")

                req_loc = f"hmc_interactions[{i}].http_request"
                exp_method = tc_getitem(req_loc, http_request, "method")
                exp_uri = tc_getitem(req_loc, http_request, "uri")
                exp_headers = tc_getitem(req_loc, http_request, "headers", {})
                exp_body_spec = tc_getitem(req_loc, http_request, "body", None)

                assert history_item.method == exp_method
                for name, exp_value in exp_headers.items():
                    assert name in history_item.headers
                    assert history_item.headers[name] == exp_value
                m = re.search(r"^.*(/api/.*)$", history_item.url)
                uri = m.group(1)
                assert uri == exp_uri
                if exp_body_spec is not None:
                    assert_body(history_item.body, exp_body_spec)

        exp_result_spec = tc_getitem(
            "zhmcclient_result", zhmcclient_result, "return")

        exp_result = resolve_value_spec(
            "zhmcclient_result.return", exp_result_spec, resource_by_uri)

        assert_result(result, exp_result)


def make_callback_for_direct(recorded_requests, status_code, body, headers):
    """
    Return a requests_mock callback function that sets the specified HTTP
    response data directly.

    The returned requests_mock callback function adds the interaction to
    recorded_requests. This approach is necessary because requests_mock stores
    only the last interaction in its history.
    """

    def callback(request, context):
        recorded_requests.append(request)
        context.status_code = status_code
        if headers:
            context.headers.update(headers)
        return body

    return callback


def make_callback_for_callback(recorded_requests, callback_func):
    """
    Return a requests_mock callback function that calls the specified
    callback function.

    The returned requests_mock callback function adds the interaction to
    recorded_requests. This approach is necessary because requests_mock stores
    only the last interaction in its history.
    """

    def callback(request, context):
        recorded_requests.append(request)
        return callback_func(request, context)

    return callback


def get_target_object(tgt_loc, target_spec, resource_by_uri):
    """
    Return the target object (zhmcclient resource or manager) for a target
    definition in a testcase.

    The object must be in the resource lookup dict (resource_by_uri).

    Parameters:

      tgt_loc (str): Location of the target object definition in the test file,
        for messages.

      target_spec (dict): The target definition in the testcase.

      resource_by_uri (dict): Resource lookup dict that will be used to
        retrieve the target object based on its URI.

    Returns:

      zhmcclient.BaseResource or zhmcclient.BaseManager: The zhmcclient object
      for the target definition in the testcase.

    Raises:

      TestcaseDefinitionError
    """
    assert "_resource" in target_spec or "_manager" in target_spec
    return resolve_value_spec(tgt_loc, target_spec, resource_by_uri)


def resolve_value_spec(val_loc, value_spec, resource_by_uri):
    """
    Return a deep copy of the value spec where any zhmcclient resource or
    manager references are resolved to their actual objects.

    The objects tpo be resolved must be in the resource lookup dict
    (resource_by_uri).

    Parameters:

      val_loc (str): Location of the value definition in the test file,
        for messages.

      value_spec (object): The value definition in the testcase.

      resource_by_uri (dict): Resource lookup dict that will be used to
        retrieve the target object based on its URI.

    Returns:

      object: The resolved value.

    Raises:

      TestcaseDefinitionError
    """
    if isinstance(value_spec, list):
        resolved_value = []
        for val_spec in value_spec:
            val = resolve_value_spec(val_loc, val_spec, resource_by_uri)
            resolved_value.append(val)
        return resolved_value

    if isinstance(value_spec, dict):
        resolved_value = {}
        for name, val_spec in value_spec.items():
            if name == "_resource":
                if len(value_spec) > 1:
                    keys_str = ", ".join([f"{k!r}" for k in value_spec.keys()])
                    raise TestcaseDefinitionError(
                        f"'{val_loc}' specifies '_resource' but has "
                        f"additional dict keys: {keys_str}")
                res_loc = f"{val_loc}._resource"
                uri = tc_getitem(res_loc, val_spec, "uri")
                try:
                    resource_obj = resource_by_uri[uri]
                except KeyError as exc:
                    raise TestcaseDefinitionError(
                        f"'{res_loc}.uri' specifies the URI of a resource "
                        "that has not been created in the file-level or "
                        f"testcase-level setup: {uri}") from exc
                return resource_obj

            if name == "_manager":
                if len(value_spec) > 1:
                    keys_str = ", ".join([f"{k!r}" for k in value_spec.keys()])
                    raise TestcaseDefinitionError(
                        f"'{val_loc}' specifies '_manager' but has "
                        f"additional dict keys: {keys_str}")
                mgr_loc = f"{val_loc}._manager"
                parent_uri = tc_getitem(mgr_loc, val_spec, "parent_uri")
                attribute = tc_getitem(mgr_loc, val_spec, "attribute")
                try:
                    parent_obj = resource_by_uri[parent_uri]
                except KeyError as exc:
                    raise TestcaseDefinitionError(
                        f"'{mgr_loc}.parent_uri' specifies the URI of a "
                        "resource that has not been created in the file-level "
                        f"or testcase-level setup: {uri}") from exc
                try:
                    manager_obj = getattr(parent_obj, attribute)
                except AttributeError as exc:
                    raise TestcaseDefinitionError(
                        f"'{mgr_loc}.attribute' specifies a non-existing "
                        "attribute on the zhmcclient."
                        f"{parent_obj.__class__.__name__} "
                        f"object: {attribute}") from exc
                return manager_obj

            val = resolve_value_spec(
                f"{val_loc}.{name}", val_spec, resource_by_uri)
            resolved_value[name] = val
        return resolved_value

    return value_spec


def create_setup_resources(
        reslist_loc, resources_spec, client, resource_by_uri):
    """
    Create the zhmcclient resources defined in the file-level and testcase-level
    setup sections.

    Parameters:

      reslist_loc (str): Location of the resource definition list in the test
        file, for messages.

      resources_spec (list): The resource definition list in the setup sections
        of a testcase. This contains the file-level resources followed by the
        testcase-level resources. If a resource URI appears more than once,
        TestcaseDefinitionError is raised. The resources must be ordered top
        to bottom, so that a parent resource already exist when its child
        resource references it.

      client (zhmcclient.Client): The zhmcclient Client object that should be
        used as the top level resource object for all others.

      resource_by_uri (dict): Resource lookup dict that will be updated with
        the created resource.

    Raises:

      TestcaseDefinitionError
    """
    for i, resource_spec in enumerate(resources_spec):
        res_loc = f"{reslist_loc}[{i}]"
        uri = tc_getitem(res_loc, resource_spec, "uri")
        name = tc_getitem(res_loc, resource_spec, "name")
        parent_uri = tc_getitem(res_loc, resource_spec, "parent_uri")
        parent_attr = tc_getitem(res_loc, resource_spec, "parent_attribute")
        props = tc_getitem(res_loc, resource_spec, "properties", {})

        if parent_uri is None:
            parent_obj = client
        else:
            try:
                parent_obj = resource_by_uri[parent_uri]
            except KeyError as exc:
                raise TestcaseDefinitionError(
                    f"'{res_loc}' specifies 'parent_uri='{uri} "
                    "that has not been created yet") from exc
        try:
            manager_obj = getattr(parent_obj, parent_attr)
        except AttributeError as exc:
            raise TestcaseDefinitionError(
                f"'{res_loc}' specifies 'parent_attribute='{parent_attr} "
                f"but the parent resource {uri} does not have such an "
                "attribute.") from exc

        res_props = {}
        res_props[manager_obj.name_prop] = name
        res_props.update(props)
        resource_obj = manager_obj.resource_object(uri, res_props)
        if DEBUG:
            print("Debug: create_setup_resources: created resource object: "
                  f"{resource_obj!r}")

        # Check for duplicate resources in setup
        if uri in resource_by_uri:
            raise TestcaseDefinitionError(
                f"'{res_loc}' specifies a duplicate resource: {uri}")

        # Remember the new resource
        resource_by_uri[uri] = resource_obj


def get_test_schema(config):
    """
    Return the JSON schema for the YAML test files.

    The schema is loaded from a file and then cached in the config object
    as an attribute "zhmcclient_test_schema". The path name of the schema

    Parameters:

      config (pytest.Config): Pytest config object.

    Returns:

      tuple(schema, schema_file): Content and path name of the JSON schema
        file for the YAML test files, with:
        * schema (dict): Content of the JSON schema file.
        * schema_file (pathlib.Path): Path name of the JSON schema file.

    Raises:

      pytest.Collector.CollectError
    """
    # Return the cached schema, if already loaded
    if hasattr(config, "zhmcclient_schema"):
        return config.zhmcclient_schema, config.zhmcclient_schema_file

    # Load and validate the schema and cache it
    my_dir = pathlib.Path(__file__).parent
    schema_file = cwdpath(my_dir / "schemas" / "test_file.schema.yaml")
    print(f"Loading function test schema file: {schema_file}")
    try:
        with schema_file.open(encoding="utf-8") as fp:
            schema = yaml.safe_load(fp)
    except (OSError, yaml.parser.ParserError, yaml.scanner.ScannerError) \
            as exc:
        raise pytest.Collector.CollectError(
            f"Cannot load function test schema file {schema_file}: {exc}")
    config.zhmcclient_schema = schema
    config.zhmcclient_schema_file = schema_file
    return schema, schema_file


def tc_getitem(dict_path, the_dict, key, default=-1):
    """
    Returns the value of a dictionary item or a default value.

    If an item with the specified key exists in the dictionary, its value is
    returned.

    If an item with the specified key does not exist in the dictionary, the
    default value is returned.

    The special default value -1 causes a TestcaseDefinitionError to be raised
    instead of returning a default value.

    Parameters:

      dict_path (str): The path to the dictionary within the testcase.
        The empty string indicates the root.

      the_dict (dict): The dictionary within the testcase. Can also be the
        entire testcase.

      key (str): The dictionary key.

      default (object): The default value. The special value -1 causes a
        TestcaseDefinitionError to be raised instead of returning a default
        value.

    Returns:

      object: The dictionary item value, or the default value.

    Raises:

      TestcaseDefinitionError
    """
    location = dict_path or "the root"
    try:
        value = the_dict[key]
    except KeyError:
        if default == -1:
            raise TestcaseDefinitionError(
                f"{key!r} property at {location} is missing")
        return default
    return value


class TestcaseDefinitionError(Exception):
    """
    Exception indicating an error in the testcase definition.
    """
    pass


class ResponseCallbacks:
    """
    A class with static methods that are requests_mock callback functions for
    being called when requests_mock returns to the zhmcclient code.

    At this point, the callback functions all raise exceptions from the
    'requests' package.

    requests_mock callback functions define how the result of a 'requests' send
    function should look like, and follow this interface:

        def callback(request, context):
            ...
            context.status_code = 200  # response status code
            context.headers = { ... }  # response headers
            return content  # response content

        Parameters:

          request (requests.Request): The request object that was provided.

          context: An object for putting the response details into attributes:
            - headers: The dictionary of headers that are to be returned.
            - status_code: The status code that is to be returned.
            - reason: The string HTTP status code reason that is to be returned.
            - cookies: A requests_mock.CookieJar of cookies that will be merged
              into the response.

        Returns:

          bytes: The response body, if the send function is supposed to
            succeed (the HTTP response may still indicate an error).

        Raises:

          Exception: An exception, if the send function is supposed to
            raise an exception.

        Examples:

          * Example when the send call results in a response:

            def callback(request, context):
                context.status_code = 200   # response status code
                context.headers = { ... }   # response headers
                return content              # response content

          * Example when the send call raises an exception:

            def callback(request, context):
                raise Exception(...)
    """

    @staticmethod
    def raise_requests_connection_error(request, context):
        # pylint: disable=unused-argument
        """
        Callback function that raises requests.ConnectionError.
        """
        raise requests.exceptions.ConnectionError("ConnectionError")

    @staticmethod
    def raise_requests_read_timeout(request, context):
        # pylint: disable=unused-argument
        """
        Callback function that raises requests.ReadTimeout.
        """
        raise requests.exceptions.ReadTimeout("ReadTimeout")

    @staticmethod
    def raise_requests_retry_error(request, context):
        # pylint: disable=unused-argument
        """
        Callback function that raises requests.RetryError.
        """
        raise requests.exceptions.RetryError("RetryError")

    @staticmethod
    def raise_requests_http_error(request, context):
        # pylint: disable=unused-argument
        """
        Callback function that raises requests.HTTPError.
        """
        raise requests.exceptions.HTTPError("HTTPError")

    @staticmethod
    def raise_requests_ssl_error(request, context):
        # pylint: disable=unused-argument
        """
        Callback function that raises requests.SSLError.
        """
        raise requests.exceptions.SSLError("SSLError")


def cwdpath(path):
    """
    Return the file or directory path relative to the current directory, if
    possible. If not possible, the original path is returned.

    Parameters:

      path (pathlib.Path): The file or directory path.

    Returns:

      pathlib.Path: The path relative to the current directory, if possible.
      If not possible, the original path.
    """
    try:
        path = path.relative_to(pathlib.Path.cwd())
    except ValueError:
        pass
    return path


def get_json_path(path_list):
    """
    Convert a JSON element path or JSON schema path provided in the exception
    data of a jsonschema validation error into a human readable path string
    that can be used in messages.
    """
    path_str = ""
    for item in path_list:
        if isinstance(item, int):
            path_str += f"[{item}]"
        elif isinstance(item, str):
            path_str += f".{item}"
    return path_str.lstrip(".")


def body_from_spec(body_loc, body_spec):
    """
    Returns the HTTP body Bytes from a HTTP body specification in the testcase.

    A testcase can specify the HTTP body in these ways:

    * As a YAML object. In this case, it gets into this function as a dict or
      list and will be serialized to JSON and then used for the response body.
    * As a string. In this case, the string is used for the response body
      exactly as specified.
    * Omitted. In this case, it gets into this function as None.

    Parameters:

      body_loc (str): Location of the HTTP body element in the test file, for
        messages.

      body_spec (dict/list or str or None):
        HTTP body as specified in the testcase.

    Returns:

      bytes or None: If an HTTP body is specified, it is returned as UTF-8
      encoded Bytes. If an HTTP body is omitted, None is returned.

    Raises:

      TestcaseDefinitionError
    """
    if body_spec is None:
        return None

    if isinstance(body_spec, str):
        assert isinstance(body_spec, str)
        body_str = body_spec
    else:
        assert isinstance(body_spec, (dict, list))
        try:
            body_str = json.dumps(body_spec)
        except (json.JSONDecodeError, TypeError) as exc:
            raise TestcaseDefinitionError(
                f"Cannot serialize HTTP body specification in {body_loc} "
                f"to a JSON string: {exc}") from exc
    body_bytes = body_str.encode("utf-8")
    return body_bytes


def assert_body(act_body, exp_body_spec):
    """
    Assert that the actual HTTP body matches the expected HTTP body.

    A testcase can specify the expected HTTP body in these ways:

    * As a YAML object. In this case, it gets into this function as a dict.
      The actual body will be parsed as JSON and will be validated at the
      object level.
    * As a string. In this case, the expected string is used for the
      validation exactly as specified.
    * Omitted. In this case, this function is not called.

    Parameters:

      act_body (bytes or str): The actual HTTP body.

      exp_body_spec (dict or str): The expected HTTP body as specified in
        the testcase.

    Raises:

      AssertionError
    """
    if isinstance(act_body, bytes):
        act_body = act_body.decode("utf-8")

    if isinstance(exp_body_spec, str):
        # Validate at the string level
        assert act_body == exp_body_spec
    else:
        assert isinstance(exp_body_spec, (dict, list))
        try:
            act_body_obj = json.loads(act_body)
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"Cannot parse actual HTTP body as JSON: {exc}\n"
                f"HTTP body begin: {act_body[0:100]!r}") from exc
        # Validate at the object level
        assert act_body_obj == exp_body_spec


def assert_result(act_result, exp_result):
    # pylint: disable=protected-access
    """
    Assert that the actual result (property value or method return value)
    matches the expected result.

    If the result is a zhmcclient resource object or a zhmcclient manager
    object, the actual and expected objects are compared by taking into
    account that certain internal objects can be equal copies instead of being
    identical objects.

    Parameters:

      act_result (object): The actual result.

      exp_result (object): The expected result.

    Raises:

      AssertionError
    """

    if isinstance(act_result, zhmcclient.BaseResource):
        assert type(act_result) is type(exp_result)
        assert_result(act_result.manager, exp_result.manager)
        assert act_result.uri == exp_result.uri
        assert act_result.properties == exp_result.properties
        assert act_result.full_properties == exp_result.full_properties
        assert act_result._auto_update == exp_result._auto_update
        assert act_result.ceased_existence == exp_result.ceased_existence

    elif isinstance(act_result, zhmcclient.BaseManager):
        assert type(act_result) is type(exp_result)
        assert act_result.resource_class == exp_result.resource_class
        assert act_result.class_name == exp_result.class_name
        assert act_result.uri == exp_result.uri
        assert_result(act_result.parent, exp_result.parent)
        assert act_result._base_uri == exp_result._base_uri
        assert act_result._oid_prop == exp_result._oid_prop
        assert act_result._uri_prop == exp_result._uri_prop
        assert act_result._name_prop == exp_result._name_prop
        assert act_result._query_props == exp_result._query_props
        assert act_result._list_has_name == exp_result._list_has_name
        assert (act_result.case_insensitive_names ==
                exp_result.case_insensitive_names)
        assert act_result.supports_properties == exp_result.supports_properties

    elif isinstance(act_result, immutabledict):
        act_result_dict = dict(act_result)
        assert act_result_dict == exp_result

    elif isinstance(act_result, list):
        assert len(act_result) == len(exp_result)
        for i, act_result_item in enumerate(act_result):
            exp_result_item = exp_result[i]
            assert_result(act_result_item, exp_result_item)

    elif isinstance(act_result, dict):
        assert len(act_result) == len(exp_result)
        for key, act_result_item in act_result.items():
            assert key in exp_result
            exp_result_item = exp_result[key]
            assert_result(act_result_item, exp_result_item)

    else:
        assert act_result == exp_result
