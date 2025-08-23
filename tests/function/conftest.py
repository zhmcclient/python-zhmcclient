"""
A conftest.py file is a Python module that is recognized by pytest via its name
and that contains directory-specific pytest hook implementations. See
https://docs.pytest.org/en/latest/writing_plugins.html#local-conftest-plugins.

This particular conftest.py module is responsible for treating the .yaml
files in this directory (nicknamed "testclient .yaml files" in some of the
documentation) as test cases and for running them.

A testclient .yaml file in this directory defines one or more test cases. Each
test case invokes a single WBEM operation, and the test case specifies the
WBEM operation along with its input parameters, the expected CIM-XML request,
a mocked CIM-XML response, and the expected results of the operation. The
test cases are run against a WBEMConnection object (i.e. not a
FakedWBEMConnection object), whereby its http level transport is mocked using
the Python 'requests_mock' package. This allows asserting the HTTP request and
injecting an HTTP response.

When running such a test case, the WBEMConnection method for the operation that
is specified in the test case will be invoked with the specified input
parameters. Pywbem will process the operation and will at some point try to
send the HTTP request. The HTTP request will be captured by requests_mock and
the test logic will be called back and will assert that the captured HTTP
request matches the expected HTTP request that is specified in the test case.
The HTTP response specified in the test case is then injected by requests_mock
and pywbem will process the HTTP response, and returns from the WBEMConnection
method with the operation results. The test case logic finally asserts that the
returned operation results match the expected results that are specified in the
test case.

The test case syntax allows specifying error cases and success cases.

This allows testing the entire pywbem client layer (at least of its
WBEMConnection class), with the exception of the lowest layers of the HTTP
transport logic in the _cim_http.py module of pywbem. This nearly holistic
test approach for the client inspired the term "testclient .yaml files".

The following is a description of a single test case in the testclient .yaml
files in YAML syntax, using curly braces to indicate syntax elements, and
using comment lines for informally stated conditions::

    - name: {tc_name}
      description: {tc_desc}
      skip: true/false  # default: false
      no_debug_details: true/false  # default: false
      zhmcclient_api_call:
        {WBEMConnection_ctor_args}
        operation:
          pywbem_method: {op_method_name}
          {op_method_args}
      zhmcclient_result:
# if operation is a non-pull operation and expected to succeed:
        result: {op_method_return}
# if operation is an open/pull operation and expected to succeed:
        pullresult: {pull_op_method_return}
# if operation is expected to fail with CIM status code (CIMError exception):
        cim_status: {op_cim_status}
        error_istances: {error_instances}  # optional
# if operation is expected to fail with an arbitrary exception:
        exception: {op_exc_type}
# optional:
        request_len: {request_len}
# optional:
        reply_len: {reply_len}
      http_request:
        verb: {http_method}
        url: {http_url}
        headers:
          {http_request_headers}
        data: {http_request_body}
      http_response:
# if the mocked HTTP layer should succeed:
        status: {http_status}
        headers:
          {http_response_headers}
        data: {http_response_body}
# if the mocked HTTP layer should fail:
        exception: {http_exc_type}

Syntax elements:

* {tc_name}: String that identfies the test case, unique within the .yaml file.
* {tc_desc}: One-line description of the test case.
* {WBEMConnection_ctor_args}: Dict items representing the WBEMConnection
  ctor arguments as kwargs. The argument values are represented as described in
  the obj() function.
* {op_method_name}: String that is the name of the WBEMConnection method
  for the WBEM operation to be invoked by the test case.
* {op_method_args}: Dict items representing the arguments for calling the
  WBEM operation method as kwargs. The argument values are represented as
  described in the obj() function. The following item keys are supported:
  - url: url argument
  - creds: creds argument
  - timeout: timeout argument
  - stats-enabled: stats_enabled argument
  - debug: debug attribute
* {op_exc_type}: String that is the Python class name of the expected exception
  raised by the operation method.
* {op_cim_status}: Numeric CIM status code. This implies an expected exception
  class CIMError.
* {error_instances}: List of CIM instances that should be returned as
  instances in an error response.
* {request_len}: Numeric length of HTTP request body
* {reply_len}: Numeric length of HTTP response body
* {op_method_return}: Expected return value of the operation method,
  represented as described in the obj() function.
* {pull_op_method_return}: Expected return value of the open or pull operation
  method, represented as described in the obj() function.
* {http_method}: String with the expected name of the HTTP method that is used
  in the generated HTTP request, in upper case (e.g. POST).
* {http_url}: String with the expected URL in the generated HTTP request.
* {http_request_headers}: Dict items for the expected HTTP header fields in the
  request. The request may contain more than those.
* {http_request_body}: String with the expected body (CIM-XML) of the generated
  HTTP request. The string can be split over
* {http_status}: HTTP status to be used for the injected HTTP response (e.g.
  200).
* {http_response_headers}: Dict items with the HTTP header fields to be used
  for the injected HTTP response. Some header fields are auto-generated without
  being specified in the test case (see the code for details).
* {http_response_body}: String with the body (CIM-XML) to be used for the
  injected HTTP response.
* {http_exc_type}: String that is the Python class name of the exception
  to be raised by the mocked HTTP transport layer, which is then to be handled
  by the pywbem code.
"""


import sys
import doctest
import socket
import re
import io
import traceback
import warnings
import threading
from collections import namedtuple, OrderedDict
import codecs
import yaml
import yamlloader
import pytest
import requests_mock
import requests
from lxml import etree, doctestcompare

# pylint: disable=wrong-import-position, wrong-import-order, invalid-name
from ..utils import import_installed
pywbem = import_installed('pywbem')
from pywbem._utils import _ensure_unicode, _ensure_bytes  # noqa: E402
from pywbem._nocasedict import NocaseDict  # noqa: E402
# pylint: enable=wrong-import-position, wrong-import-order, invalid-name


class ExcThread(threading.Thread):
    """
    Thread that catches an exception and passes it to the creator
    in the Thread.join() method.
    """

    def run(self):
        # pylint: disable=attribute-defined-outside-init
        self.exc = None
        try:
            threading.Thread.run(self)
        except Exception:  # pylint: disable=broad-except
            self.exc = sys.exc_info()

    def join(self, timeout=None):
        threading.Thread.join(self, timeout)
        if self.exc:
            raise self.exc


def patched_makefile(self, mode='r', bufsize=-1):
    """
    Patched version of httpretty's makefile() function, which uses ExcThread
    instead of Thread, in order to properly catch exceptions. See httpretty
    issue https://github.com/gabrielfalcao/HTTPretty/issues/334.

    Returns this fake socket's own StringIO buffer.

    If there is an entry associated with the socket, the file
    descriptor gets filled in with the entry data before being
    returned.
    """
    # pylint: disable=protected-access
    self._mode = mode
    self._bufsize = bufsize

    if self._entry:
        # The patched version uses ExcThread instead of Thread
        t = ExcThread(
            target=self._entry.fill_filekind, args=(self.fd,)
        )
        t.start()
        if self.timeout == socket._GLOBAL_DEFAULT_TIMEOUT:
            timeout = None
        else:
            timeout = self.timeout
        t.join(timeout)
        if t.is_alive():
            raise socket.timeout  # pylint: disable=no-member

    return self.fd


def pytest_collect_file(parent, path):
    """
    py.test hook that is called for a directory to collect its test files.

    For an example very similar to what we do here, see
    https://docs.pytest.org/en/latest/example/nonpython.html
    """
    if path.ext == ".yaml":
        if hasattr(YamlFile, 'from_parent'):
            # pylint: disable=no-member
            return YamlFile.from_parent(fspath=path, parent=parent)
        # Direct creation has been deprecated in pytest, but
        # from_parent() was introduced only in pytest 6.0.0 and we
        # have to pin to lower pytest versions on py27/py34/py35.
        return YamlFile(fspath=path, parent=parent)
    return None  # to avoid pylint inconsistent-return-statements


class YamlFile(pytest.File):
    """
    py.test test case collector class that parses a testclient .yaml file and
    yields its test cases.
    """

    def collect(self):
        with self.fspath.open(encoding='utf-8') as fp:
            filepath = self.fspath.relto(self.parent.fspath)

            # We need to be able to load illegal Unicode sequences for testing,
            # so we use the non-C loader. This causes the yaml parser to
            # tolerate these sequences. The C loader rejects them.
            testcases = yaml.load(
                fp, Loader=yamlloader.ordereddict.Loader)

            # Note: All the strings in the testcases object are byte strings

            for i, testcase in enumerate(testcases):
                try:
                    tc_name = testcase['name']
                except KeyError:
                    raise ClientTestError(
                        f"Test case #{i + 1} does not have a 'name' attribute")
                if hasattr(YamlItem, 'from_parent'):
                    # pylint: disable=no-member
                    yield YamlItem.from_parent(
                        name=tc_name, parent=self,
                        testcase=testcase, filepath=filepath)
                else:
                    # Direct creation has been deprecated in pytest, but
                    # from_parent() was introduced only in pytest 6.0.0 and we
                    # have to pin to lower pytest versions on py27/py34/py35.
                    yield YamlItem(
                        name=tc_name, parent=self,
                        testcase=testcase, filepath=filepath)


class YamlItem(pytest.Item):
    """
    py.test test case collector class that runs the test on a single test case.
    """

    def __init__(self, name, parent, testcase, filepath):
        """
        Parameters:

          name (string): Name of the testcase as recognized by py.test.

          parent (YamlFile): Parent of this testcase as seen by py.test.

          testcase (dict): The dict representing the subset of the testclient
            .yaml file for a single test case.

          filepath (string): Path name of the testclient .yaml file.
        """
        super().__init__(name, parent)
        self.testcase = testcase
        self.filepath = filepath

    def tc_name(self):
        """
        Return test case name.
        """
        name = self.testcase.get('name', 'unknown')
        return name

    def runtest(self):
        """
        Called by py.test to run this test case.
        """
        runtestcase(self.testcase)

    def repr_failure(self, excinfo, style=None):
        # pylint: disable=unused-argument,no-self-use
        """
        Called by py.test when the runtest() method raised an exception, to
        provide details about the failure.
        """
        exc = excinfo.value
        if isinstance(exc, ClientTestFailure):  # pylint: disable=no-else-return
            return f"Failure running test case: {exc}"
        if isinstance(exc, ClientTestError):
            return f"Error in definition of test case: {exc}"
        return f"Error: {exc}"

    def reportinfo(self):
        """
        Called by py.test when the test case failed, to provide information
        about the test case. The third tuple item is a string that
        identifies the test case in a human readable way.
        """
        return self.fspath, 0, f"{self.name} in {self.filepath}"


class ClientTestError(Exception):
    """Exception indicating an error in the test case definition."""
    pass


class ClientTestFailure(Exception):
    """Exception indicating a failure when running a test case."""
    pass


def show_diff(conn, expected, actual, display_text):
    """Display the actual and expected data"""

    print("Details for the following assertion error:")
    print(f"- Expected result {display_text}: {expected}")
    print(f"- Actual result {display_text}: {actual}")
    if conn is not None and conn.debug:
        print(f"- HTTP response data: {conn.last_raw_reply!r}")


def str_tuple(tuple_):
    """
    Prepare a tuple or NoneType for output.

    This gets around issues of type failure when trying to
    print tuples.

    Returns str rep of tuple on None if tuple_ is None
    """
    return 'NoneType' if tuple_ is None else f'{tuple_}'


def obj(value, tc_name):
    """
    Create a PyWBEM CIM object or list of CIM Objects from a testcase value.

    If the input value is not a valid type or list of valid types an
    error is raised.

    If the pywbem_object defines a valid type (ex. CIMInstance) or
    list of items where the pywbem_object entry defines a valid type,
    the type is evaluated with the remaining entries in the
    dictionary and returned.

    Examples for a testcase value (JSON object / Python dict):

    1. CIMInstance object:

        {
            "pywbem_object": "CIMInstance",
            "classname": "PyWBEM_Person",
            "properties": {
                "Name": "Fritz",
                "Address": "Fritz Town"
            },
            "path": {
                "pywbem_object": "CIMInstanceName",
                "classname": "PyWBEM_Person",
                "keybindings": {
                    "Name": "Fritz"
                }
            }
        }
        Returns a CIMInstance with the classname, properties, and path defined

    2. boolean object:

        False

        Returns boolean false

    3. list of objects
       A list of objects as defined by 1 above or boolean objects defined
       by 2. A list of corresponding results is returned

       Returns a list of the objects defined by each entry in the list

       See enumerateinstances.yaml for an example of list of instances.
       [] defines a null list
    """

    if isinstance(value, dict):
        if "pywbem_object" in value:
            ctor_name = value["pywbem_object"]
            try:
                ctor_call = getattr(pywbem, ctor_name)
            except AttributeError:
                raise ClientTestError(
                    "Unknown type specified in "
                    f"'pywbem_object' attribute: {ctor_name}")
            ctor_args = OrderedDict()
            for arg_name in value:
                if arg_name == "pywbem_object":
                    continue
                ctor_args[arg_name] = obj(value[arg_name], tc_name)
            with warnings.catch_warnings(record=True) as rec_warnings:
                obj_ = ctor_call(**ctor_args)
            for w in rec_warnings:
                # Ignore DeprecationWarnings, re-issue any others
                if w.category is not DeprecationWarning:
                    warnings.warn(w.message, w.category, 1)
        else:
            obj_ = OrderedDict()
            for key in value:
                obj_[key] = obj(value[key], tc_name)
    elif isinstance(value, list):
        obj_ = [obj(x, tc_name) for x in value]
    else:
        obj_ = value
    return obj_


def tc_getattr(tc_name, dict_, key, default=-1):
    """
    Gets the attribute of a name/value pair defined by key in dictionary
    defined by dict_.

    Get the attribute for the key and if the attribute is list or tuple
    only return the first item. If the attribute is a dictionary
    return the attribute

    If the key is not in the dictionary, return the provided default or
    raise an error if no default provided.
    """

    try:
        value = dict_[key]
        if isinstance(value, (list, tuple)):
            value = value[0]
    except (KeyError, IndexError, TypeError):
        if default != -1:
            return default
        raise ClientTestError(
            f"{key!r} attribute missing in test case {tc_name}")
    return value


def tc_getattr_list(tc_name, dict_, key, default=-1):
    """
    Gets the attribute of a name/value pair defined by key in dictionary
    defined by dict_. The entry may be dictionary, ordinary value or
    a list

    Gets the attribute for the key return it.  Does not test for
    type of the attribute.

    If the key is not in the dictionary, return the provided default or
    raise an error if no default provided.
    """

    try:
        value = dict_[key]
    except KeyError:
        if default != -1:
            return default
        raise ClientTestError(
            f"{key!r} attribute missing in test case {tc_name}")
    return value


def tc_hasattr(dict_, key):
    """Return true if key is in dict_"""
    return key in dict_


class Callback:
    """
    A class with static methods that are requests_mock callback functions for
    raising expected exceptions at the socket level.

    requests_mock callback functions follow this interface:

       def callback(request, context):
            ...
            context.status_code = 200  # response status code
            context.headers = { ... }  # response headers
            return content  # response content

    Parameters:
      * `request`: The requests.Request object that was provided.
      * `context`: An object for putting the response details into attributes:
        - headers: The dictionary of headers that are to be returned.
        - status_code: The status code that is to be returned.
        - reason: The string HTTP status code reason that is to be returned.
        - cookies: A requests_mock.CookieJar of cookies that will be merged into
          the response.

    Return value:
      byte string: response body.

    They can also raise an exception, which is passed to the caller of the
    socket send call.
    """

    @staticmethod
    def requests_connection_error(request, context):
        # pylint: disable=unused-argument
        """
        Callback function that raises requests.ConnectionError.
        """
        raise requests.exceptions.ConnectionError("ConnectionError")

    @staticmethod
    def requests_read_timeout(request, context):
        # pylint: disable=unused-argument
        """
        Callback function that raises requests.ReadTimeout.
        """
        raise requests.exceptions.ReadTimeout("ReadTimeout")

    @staticmethod
    def requests_retry_error(request, context):
        # pylint: disable=unused-argument
        """
        Callback function that raises requests.RetryError.
        """
        raise requests.exceptions.RetryError("RetryError")

    @staticmethod
    def requests_http_error(request, context):
        # pylint: disable=unused-argument
        """
        Callback function that raises requests.HTTPError.
        """
        raise requests.exceptions.HTTPError("HTTPError")

    @staticmethod
    def requests_ssl_error(request, context):
        # pylint: disable=unused-argument
        """
        Callback function that raises requests.SSLError.
        """
        raise requests.exceptions.SSLError("SSLError")


def xml_embed(tree_elem):
    """
    Embed the CIM-XML representation of a CIM object.

    This is done by converting the XML tree representing the CIM object into a
    single XML element whose character text is the embedded representation,
    which has some special XML characters (defined in DSP0201) replaced with
    their character entity references (= XML escape sequences).

    Parameters:
      tree_elem (etree.Element):
        XML tree of the CIM-XML representation of the CIM object that is to
        be embedded.

    Returns:
      string: The embedded CIM-XML representation of the CIM object.
    """
    return xml_escape(etree.tostring(tree_elem))


def xml_escape(s):  # pylint: disable=invalid-name
    """
    Return the XML-escaped input string.
    """
    if isinstance(str, str):
        s = s.replace("&", "&amp;")
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        s = s.replace("\"", "&quot;")
        s = s.replace("'", "&apos;")
    else:
        s = s.replace(b"&", b"&amp;")
        s = s.replace(b"<", b"&lt;")
        s = s.replace(b">", b"&gt;")
        s = s.replace(b"\"", b"&quot;")
        s = s.replace(b"'", b"&apos;")
    return s


def xml_unembed(emb_str):
    """
    Unembed the CIM-XML representation of a CIM object.

    This is done by converting an XML element whose character text is the
    embedded representation, into an XML tree representing the CIM object,
    whereby the character entity references (= XML escape sequences) of
    some special XML characters (defined in DSP0201) are replaced with
    their characters.

    Parameters:
      emb_str (string):
        The embedded CIM-XML representation of the CIM object that is to be
        unembedded.

    Returns:
      etree.Element:
        XML tree of the CIM-XML representation of the CIM object.
    """
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.XML(xml_unescape(emb_str), parser=parser)


def xml_unescape(s):  # pylint: disable=invalid-name
    """
    Return the XML-unescaped input string.
    """
    if isinstance(s, str):
        s = s.replace("&lt;", "<")
        s = s.replace("&gt;", ">")
        s = s.replace("&quot;", "\"")
        s = s.replace("&apos;", "'")
        s = s.replace("&amp;", "&")
    else:
        s = s.replace(b"&lt;", b"<")
        s = s.replace(b"&gt;", b">")
        s = s.replace(b"&quot;", b"\"")
        s = s.replace(b"&apos;", b"'")
        s = s.replace(b"&amp;", b"&")
    return s


def assertXMLEqual(s_act, s_exp, entity):
    """
    Assert that the two XML fragments are equal, tolerating the following
    variations:

      * whitespace outside of element content and attribute values.
      * order of attributes.
      * order of certain child elements (see `sort_elements` in this
        function).

    Parameters:

      * s_act and s_exp are string representations of an XML fragment. The
        strings may be Unicode strings or UTF-8 encoded byte strings.
        The strings may contain an encoding declaration even when
        they are Unicode strings.

        Note: An encoding declaration is the `encoding` attribute in the
        XML declaration (aka XML processing statement), e.g.:
            <?xml version="1.0" encoding="utf-8" ?>

      * entity (string): A human readable identification for what is compared.
    """

    # Make sure that None values are already excluded by the caller
    assert isinstance(s_act, (str, bytes))
    assert isinstance(s_exp, (str, bytes))

    # Ensure Unicode strings and remove encoding from XML declaration
    encoding_pattern = re.compile(
        r'^<\?xml +(([a-zA-Z0-9_]+=".*")?) +' +
        r'encoding="utf-8" +(([a-zA-Z0-9_]+=".*")?) *\?>')
    encoding_repl = r'<?xml \1 \3 ?>'
    s_act = re.sub(encoding_pattern, encoding_repl, _ensure_unicode(s_act))
    s_exp = re.sub(encoding_pattern, encoding_repl, _ensure_unicode(s_exp))

    parser = etree.XMLParser(remove_blank_text=True)
    try:
        # Note: lxml.etree.XML() has issues with unicode strings as input,
        # so we pass UTF-8 encoded byte strings. See lxml bug
        # https://bugs.launchpad.net/lxml/+bug/1902364 for a similar issue
        # with lxml.etree.fromstring().
        x_act = etree.XML(_ensure_bytes(s_act), parser=parser)
        x_exp = etree.XML(_ensure_bytes(s_exp), parser=parser)
    except etree.XMLSyntaxError as exc:
        raise AssertionError(
            f"XML cannot be validated for {entity}: {exc}")

    def sort_embedded(root, sort_elements):
        """
        Helper function for `sort_children()`, in support of embedded
        objects. This function invokes sort_children() on each embedded
        object in `root`, after unembedding the embedded object.

        Parameters:
          root (etree.Element):
            XML tree of the CIM-XML representation of the CIM element that
            contains an embedded CIM object (e.g. the CIM element may be
            an INSTANCE XML element and one of its PROPERTY child elements
            has a value that is an embedded CIM instance).
        """
        emb_elems = root.xpath("//*[@EmbeddedObject or @EMBEDDEDOBJECT]"
                               "/*[local-name() = 'VALUE' or "
                               "local-name() = 'VALUE.ARRAY']")
        for emb_elem in emb_elems:
            elem = xml_unembed(emb_elem.text)
            sort_children(elem, sort_elements)
            emb_elem.text = xml_embed(elem)

    def sort_children(root, sort_elements):
        """
        Sort certain elements in the `root` parameter to facilitate
        comparison of two XML documents.

        In addition, make sure this is also applied to any embedded
        objects (in their unembedded state).
        """
        sort_embedded(root, sort_elements)
        for tag, attr in sort_elements:
            # elems is a list of elements with this tag name
            elems = root.xpath("//*[local-name() = $tag]", tag=tag)
            if elems:
                parent = elems[0].getparent()
                first = None
                after = None
                for i, p in enumerate(parent):
                    # TODO 6/18 AM: Loop above should probably be on elems
                    if p.tag == tag and first is None:
                        first = i
                    if p.tag != tag and first is not None:
                        after = i
                # The following changes the original XML tree:
                # The following pylint warning can safely be disabled, see
                # https://stackoverflow.com/a/25314665
                # pylint: disable=cell-var-from-loop
                parent[first:after] = sorted(elems,
                                             key=lambda e: e.attrib[attr])

    sort_elements = [
        # Sort sibling elements with <first> tag by its <second> attribute
        ("IPARAMVALUE", "NAME"),
        ("PROPERTY", "NAME"),
        ("PROPERTY.ARRAY", "NAME"),
        ("PARAMETER", "NAME"),
        ("KEYBINDING", "NAME"),
    ]
    sort_children(x_act, sort_elements)
    sort_children(x_exp, sort_elements)

    ns_act = _ensure_unicode(etree.tostring(x_act))
    ns_exp = _ensure_unicode(etree.tostring(x_exp))

    checker = doctestcompare.LXMLOutputChecker()

    # This tolerates differences in whitespace and attribute order
    if not checker.check_output(ns_act, ns_exp, 0):
        diff = checker.output_difference(doctest.Example("", ns_exp),
                                         ns_act, 0)
        raise AssertionError(
            f"XML is not as expected in {entity}: {diff}")


def utf8_with_surrogate_issues(in_str):
    """
    Convert an input string (unicode or bytes) to a UTF-8 encoded byte string,
    tolerating issues with surrogate characters (U+D800 to U+DFFF).

    Returns: UTF-8 encoded byte string

    Background for having this function:

    For testing purposes, the response body should support characters that are
    illegal from as many different perspectives as possible. At this point, the
    response body may specify anything that is legal in a Python unicode
    string. Up to now, Python unicode strings allow for unpaired surrogates
    (i.e. a surrogate code point followed by a non-surrogate code point), or
    swapped surrogates (i.e. a high surrogate code point followed by a low
    surrogate code point). However, httpretty converts a body presented as a
    Python unicode string into a byte string using str.encode() which fails in
    Python 3 in case of such surrogate issues (it tolerates that in Python 2).
    In order to allow such invalid surrogates in responses to be tested, this
    function converts the unicode body string to a UTF-8 byte string in a way
    that tolerates surrogate issues in both Python 2 and Python 3.
    """
    utf8_str = codecs.encode(in_str, 'utf-8', 'surrogatepass')
    return utf8_str


def runtestcase(testcase):
    """Run a single test case."""

    tc_name = tc_getattr("", testcase, "name")
    # tc_desc = tc_getattr(tc_name, testcase, "description", None)
    tc_skip_test = tc_getattr(
        tc_name, testcase, "skip", False)
    tc_exclude_from_debug = tc_getattr(
        tc_name, testcase, "no_debug_details", False)

    # Determine if this test case should be skipped
    if tc_skip_test:
        pytest.skip("Test case has 'skip' set")
        return

    zhmcclient_api_call = tc_getattr(tc_name, testcase, "zhmcclient_api_call")
    exp_http_request = tc_getattr(tc_name, testcase, "http_request", None)
    http_response = tc_getattr(tc_name, testcase, "http_response", None)
    exp_zhmcclient_result = tc_getattr(tc_name, testcase, "zhmcclient_result")

    mock_adapter = requests_mock.Adapter()

    # Setup requests_mock for one WBEM operation
    if exp_http_request is not None:
        exp_http_exception = tc_getattr(tc_name, http_response,
                                        "exception", None)
        if exp_http_exception is None:
            body = tc_getattr(tc_name, http_response, "data")
            # body is a UTF-8 encoded byte string
            body = utf8_with_surrogate_issues(body)
            params = {
                "content": body,
                "headers": tc_getattr(tc_name, http_response, "headers", None),
                "status_code": tc_getattr(tc_name, http_response, "status")
            }
        else:
            callback_name = exp_http_exception
            try:
                callback_func = getattr(Callback(), callback_name)
            except AttributeError:
                raise ClientTestError(
                    f"Unknown exception callback: {callback_name}")
            params = {
                "text": callback_func
            }

        method = tc_getattr(tc_name, exp_http_request, "verb")
        url = tc_getattr(tc_name, exp_http_request, "url")

        mock_adapter.register_uri(method=method, url=url, **params)

    conn = pywbem.WBEMConnection(
        url=tc_getattr(tc_name, zhmcclient_api_call, "url"),
        creds=tc_getattr(tc_name, zhmcclient_api_call, "creds"),
        timeout=tc_getattr(tc_name, zhmcclient_api_call, "timeout"),
        stats_enabled=tc_getattr(tc_name, zhmcclient_api_call, "stats-enabled",
                                 False))

    conn.session.mount(conn.scheme + '://', mock_adapter)

    conn.debug = tc_getattr(tc_name, zhmcclient_api_call, "debug", False)

    op = tc_getattr(tc_name, zhmcclient_api_call, "operation")
    # Example:
    #  "operation": {
    #      "pywbem_method": "GetInstance",
    #      "InstanceName": {
    #          "pywbem_object": "CIMInstanceName",
    #          "classname": "PyWBEM_Person",
    #          "keybindings": {
    #              "Name": "Fritz"
    #          }
    #      },
    #      "LocalOnly": False
    #  }

    op_name = tc_getattr(tc_name, op, "pywbem_method")
    op_args = OrderedDict()
    for arg_name in op:
        if arg_name == "pywbem_method":
            continue
        op_args[arg_name] = obj(op[arg_name], tc_name)
    try:
        op_call = getattr(conn, op_name)

    except AttributeError:
        raise ClientTestError(f"Unknown operation name: {op_name}")

    # Invoke the PyWBEM operation to be tested
    raised_exception = None
    raised_traceback_str = None  # avoid pylint warning used-before-assignment
    try:
        result = op_call(**op_args)
    except Exception as exc:      # pylint: disable=broad-except
        raised_exception = exc
        stringio = io.StringIO()
        traceback.print_exc(file=stringio)
        raised_traceback_str = stringio.getvalue()
        stringio.close()
        result = None

    # Validate PyWBEM result and exceptions.
    # We validate exceptions before validating the HTTP request, because
    # an exception might have been raised on the way down before the
    # request was actually made.

    exp_exception = tc_getattr(tc_name, exp_zhmcclient_result,
                               "exception", None)
    exp_cim_status = tc_getattr(tc_name, exp_zhmcclient_result,
                                "cim_status", 0)
    exp_error_instances = tc_getattr_list(tc_name, exp_zhmcclient_result,
                                          "error_instances", None)

    # get the optional expected request and reply sizes if specified. The
    # default is None if not specified
    exp_request_len = tc_getattr_list(tc_name, exp_zhmcclient_result,
                                      "request_len", None)
    exp_reply_len = tc_getattr_list(tc_name, exp_zhmcclient_result,
                                    "reply_len", None)
    # get the expected result.  This may be either the the definition
    # of a value or cimobject or a list of values or cimobjects or
    # a named tuple of results.
    exp_result = tc_getattr_list(tc_name, exp_zhmcclient_result,
                                 "result", None)

    exp_pull_result = tc_getattr(tc_name, exp_zhmcclient_result,
                                 "pullresult", None)

    if exp_pull_result and exp_result:
        raise ClientTestError("Result and pull result attributes are are not "
                              "compatible.")

    if exp_exception is not None and exp_result is not None:
        raise ClientTestError("The 'result' and 'exception' attributes in "
                              "'pywbem_result' are not compatible.")
    if exp_cim_status != 0 and exp_result is not None:
        raise ClientTestError("The 'result' and 'cim_status' attributes in "
                              "'pywbem_result' are not compatible.")

    if exp_cim_status != 0:
        exp_exception = 'CIMError'

    if exp_exception is not None:
        if raised_exception is None:
            raise AssertionError(
                f"Testcase {tc_name}: A {exp_exception} exception was "
                f"expected to be raised by PyWBEM operation {op_name}, "
                "but no exception was actually raised.")
        if raised_exception.__class__.__name__ != exp_exception:
            raise AssertionError(
                f"Testcase {tc_name}: A {exp_exception} exception was "
                f"expected to be raised by PyWBEM operation {op_name}, "
                "but a different exception was actually raised:\n"
                f"{raised_traceback_str}\n")
        if isinstance(raised_exception,
                      (pywbem.CIMXMLParseError, pywbem.XMLParseError)):
            req = raised_exception.request_data  # pylint: disable=no-member
            if req != conn.last_raw_request:
                raise AssertionError(
                    f"Testcase {tc_name}: The "
                    f"{raised_exception.__class__.__name__} exception "
                    f"raised by PyWBEM operation {op_name} has unexpected "
                    "CIM-XML request data:\n"
                    f"{req}\n"
                    "Expected CIM-XML request data:\n"
                    f"{conn.last_raw_request}\n")
            resp = raised_exception.response_data  # pylint: disable=no-member
            if resp != conn.last_raw_reply:
                raise AssertionError(
                    f"Testcase {tc_name}: The "
                    f"{raised_exception.__class__.__name__} exception "
                    f"raised by PyWBEM operation {op_name} has unexpected "
                    "CIM-XML response data:\n"
                    f"{resp}\n"
                    "Expected CIM-XML response data:\n"
                    f"{conn.last_raw_reply}\n")
    else:
        if raised_exception is not None:
            raise AssertionError(
                f"Testcase {tc_name}: No exception was expected to be "
                f"raised by PyWBEM operation {op_name}, but an exception was "
                "actually raised:\n"
                f"{raised_traceback_str}\n")

    # Validate HTTP request produced by PyWBEM

    if exp_http_request is not None:

        http_request = mock_adapter.last_request

        exp_verb = tc_getattr(tc_name, exp_http_request, "verb")
        assert http_request.method == exp_verb
        exp_headers = tc_getattr(tc_name, exp_http_request, "headers", {})
        for header_name in exp_headers:
            act_header = http_request.headers[header_name]
            exp_header = exp_headers[header_name]
            assert act_header == exp_header, (
                f"Value of {header_name} header in HTTP request is: "
                f"{act_header} (expected: {exp_header})")
        exp_data = tc_getattr(tc_name, exp_http_request, "data", None)
        if exp_data:
            assertXMLEqual(http_request.body, exp_data, "HTTP request")
            if not tc_exclude_from_debug and conn.debug:
                if conn.last_raw_request:
                    assertXMLEqual(conn.last_raw_request, exp_data,
                                   "conn.last_raw_request")
                if conn.last_request:
                    assertXMLEqual(conn.last_request, exp_data,
                                   "conn.last_request")

    if http_response is not None:
        exp_response_data = tc_getattr(tc_name, http_response, "data", None)
        if exp_response_data:
            if not tc_exclude_from_debug and conn.debug:
                if conn.last_raw_reply:
                    assertXMLEqual(conn.last_raw_reply, exp_response_data,
                                   "conn.last_raw_reply")
                if conn.last_reply:
                    assertXMLEqual(conn.last_reply, exp_response_data,
                                   "conn.last_reply")

    if exp_request_len is not None:
        assert exp_request_len == conn.last_request_len

        if conn.stats_enabled:
            snapshot = conn.statistics.snapshot()
            assert len(snapshot) == 1  # one operation; one stat

            for name, stats in snapshot:  # pylint: disable=unused-variable
                stat = stats
            assert stat.count == 1
            assert stat.min_request_len == stat.max_request_len
            assert stat.min_request_len == exp_request_len

    if exp_reply_len is not None:
        assert exp_reply_len == conn.last_reply_len, (
            f"Reply lengths do not match. exp {exp_reply_len} "
            f"rcvd {conn.last_reply_len}")

        if conn.stats_enabled:
            snapshot = conn.statistics.snapshot()
            assert len(snapshot) == 1  # one operation; one stat

            for name, stats in snapshot:
                stat = stats
            assert stat.count == 1, "Expected a single statistic"
            assert stat.min_reply_len == stat.max_reply_len
            assert stat.min_reply_len == exp_reply_len

    # Continue with validating the result

    if isinstance(raised_exception, pywbem.CIMError):
        # pylint: disable=no-member
        cim_status = raised_exception.status_code
        # pylint: disable=no-member
        error_instances = raised_exception.instances
    else:
        cim_status = 0
        error_instances = None

    assert cim_status == exp_cim_status, (
        "Error in WBEMConnection operation CIM status code. "
        f"Expected {exp_cim_status}; received {cim_status}")

    exp_error_inst_objs = obj(exp_error_instances, tc_name)
    assert error_instances == exp_error_inst_objs, (
        "Error in WBEMConnection operation error instances.\n"
        f"Expected: {exp_error_inst_objs}\n"
        f"Received: {error_instances}")

    # Returns either exp_result or exp_pull_result
    if exp_result is not None:
        exp_result_obj = obj(exp_result, tc_name)

        # The testcase can only specify lists but not tuples, so we
        # tolerate tuple/list mismatches:
        act_type = type(result)
        if act_type is tuple:
            act_type = list
        exp_type = type(exp_result_obj)
        # pylint: disable=unidiomatic-typecheck
        if act_type != exp_type:
            show_diff(None, type(exp_result_obj), type(result), 'type')
            raise AssertionError("PyWBEM CIM result type is not"
                                 " as expected.")

        # The testcase can only specify dicts but not NocaseDicts, so we
        # tolerate such mismatches (in case of InvokeMethod):
        if isinstance(exp_result_obj, list) and \
           len(exp_result_obj) == 2 and \
           isinstance(exp_result_obj[1], dict):
            _exp_result_obj = (
                exp_result_obj[0],
                NocaseDict(exp_result_obj[1])
            )
        else:
            _exp_result_obj = exp_result_obj

        # If result items are tuple, convert to lists. This is for
        # class ref and assoc results.
        if isinstance(result, list) and \
                result and isinstance(result[0], tuple):
            _result = []
            for item in result:
                if isinstance(item, tuple):
                    _result.append(list(item))
                else:
                    _result.append(item)
        else:
            _result = result

        if _result != _exp_result_obj:
            # TODO 2016/07 AM: Improve the presentation of the difference
            show_diff(conn, repr(exp_result_obj), repr(_result), 'data')
            raise AssertionError("WBEMConnection operation method result "
                                 "is not as expected.")

    # if this is a pull result, compare the components of expected
    # and actual results. Pull results return a tuple
    elif exp_pull_result is not None:
        exp_pull_result_obj = result_tuple(exp_pull_result, tc_name)

        # Result length should be the same as expected result
        if len(result) != len(exp_pull_result_obj):
            show_diff(conn, len(conn, exp_pull_result_obj), len(result),
                      'tuple size')
            raise AssertionError("PyWBEM CIM result type is not"
                                 " as expected.")
        # eos is required result
        if result.eos != exp_pull_result_obj.eos:
            show_diff(conn, exp_pull_result_obj.eos, result.eos,
                      'result.eos')
            raise AssertionError("WBEMConnection operation method result "
                                 "is not as expected.")

        # Context is required result
        # NOTE: pyaml does not natively support tuples. It supports very
        #   simple tuples but only with single objects and in block mode.
        exp_context = tuple(exp_pull_result_obj.context) \
            if exp_pull_result_obj.context \
            else None
        if result.context != exp_context:
            show_diff(conn, repr(str_tuple(exp_context)),
                      repr(str_tuple(result.context)), 'result.context')
            raise AssertionError("WBEMConnection operation method result "
                                 "is not as expected.")

        if "instances" in exp_pull_result:
            _result = result.instances
            _exp_result = exp_pull_result_obj.instances
        elif "paths" in exp_pull_result:
            _result = result.paths
            _exp_result = exp_pull_result_obj.paths
        else:
            raise AssertionError("WBEMConnection operation method result "
                                 "is not as expected. No 'instances' "
                                 "or 'paths' component.")

        if _result != _exp_result:
            # TODO 2016/07 AM: Improve the presentation of the diff.
            show_diff(conn, repr(_exp_result), repr(_result), 'result data')
            raise AssertionError("WBEMConnection operation method "
                                 "result is not as expected.")

        # TODO redo as indexed loop to compare all items.

    else:
        assert result is None, f"PyWBEM CIM result is not None: {result!r}"


def result_tuple(value, tc_name):
    """
    Process the value (a dictionary) to create a named tuple of
    the components that are part of a pull result.

    Returns the  namedtuple of either
        instance, eos, context
    or
        paths, eos, context

    For openqueryinstances it returns a named tuple with 4 elements
    in place of 3
    """
    if not isinstance(value, dict):
        raise AssertionError("WBEMConnection operation invalid tuple "
                             "definition.")

    # test for both paths and instances.
    objs = None
    if "query_result_class" in value:
        result = namedtuple("result", ["instances", "eos", "context",
                                       "query_result_class"])
    else:
        result = namedtuple("result", ["instances", "eos", "context"])

    # either path or instances should be in value
    if "instances" in value:
        # instances = value["instances"]
        objs = obj(value["instances"], tc_name)
        if 'paths' in value:
            raise AssertionError("WBEMConnection operation method "
                                 "result is not as expected. Both "
                                 "'instances' and 'paths' component.")
    elif "paths" in value:
        # paths = value["paths"]
        objs = obj(value["paths"], tc_name)
        result = namedtuple("result", ["paths", "eos", "context"])
    else:
        raise AssertionError("WBEMConnection operation method result "
                             "is not as expected. No 'instances' "
                             "or 'paths' component.")

    # if query_result_class in value, add it to result
    if "query_result_class" in value:
        return result(objs, value["eos"], value["context"],
                      value["query_result_class"])

    return result(objs, value["eos"], value["context"])
