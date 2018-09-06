# Copyright 2017 IBM Corp. All Rights Reserved.
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
Utility functions for tests.
"""

import sys
import os
import yaml
import logging

import zhmcclient
import zhmcclient_mock

# Logger names by log component
LOGGER_NAMES = {
    'all': '',  # root logger
    'api': zhmcclient.API_LOGGER_NAME,
    'hmc': zhmcclient.HMC_LOGGER_NAME,
}

DEFAULT_LOG = 'all=warning'

DEFAULT_RT_CONFIG = zhmcclient.RetryTimeoutConfig(
    connect_timeout=10,
    connect_retries=1,
    operation_timeout=300,
    status_timeout=60,
)


def assert_resources(resources, exp_resources, prop_names):
    """
    Assert that a list of resource objects is equal to an expected list of
    resource objects (or faked resource objects).

    This is done by comparing:
    - The resource URIs, making sure that the two lists have matching URIs.
    - The specified list of property names.

    Parameters:

      resources (list): List of BaseResource objects to be checked.

      exp_resources (list): List of BaseResource or FakedResource objects
        defining the expected number of objects and property values.

      prop_names (list): List of property names to be checked.
    """

    # Assert the resource URIs
    uris = set([res.uri for res in resources])
    exp_uris = set([res.uri for res in exp_resources])
    assert uris == exp_uris

    for res in resources:

        # Search for the corresponding expected profile
        for exp_res in exp_resources:
            if exp_res.uri == res.uri:
                break

        # Assert the specified property names
        if prop_names is None:
            _prop_names = exp_res.properties.keys()
        else:
            _prop_names = prop_names
        for prop_name in _prop_names:
            prop_value = res.properties[prop_name]
            exp_prop_value = exp_res.properties[prop_name]
            assert prop_value == exp_prop_value


def info(capsys, format_str, format_args=None):
    """
    Print an information message during test execution that is not being
    captured by py.test (i.e. it is shown even when py.test is not invoked
    with '-s').

    Parameters:

      capsys: The pytest 'capsys' fixture the testcase function must specify as
        an argument and pass to this function here.

      format_str (string): Percent-based format string.

      format_args: Argument(s) for the format string.
    """

    if format_args is not None:
        msg = (format_str % format_args)
    else:
        msg = format_str

    with capsys.disabled():
        print("Info: " + msg)


class HmcCredentials(object):
    """
    Utility class to encapsulate the data in an HMC credentials file (for the
    purpose of zhmcclient function tests).

    The HMC credentials file must be in YAML and must have entries for each
    CPC specify certain data about the HMC managing it, as in the following
    example::

        cpcs:

          "CPC1":
            description: "z13 test system"
            contact: "Amy"
            hmc_host: "10.10.10.11"           # required
            hmc_userid: "myuser1"             # required
            hmc_password: "mypassword1"       # required

          "CPC2":
            description: "z14 development system"
            contact: "Bob"
            hmc_host: "10.10.10.12"
            hmc_userid: "myuser2"
            hmc_password: "mypassword2"

    In the example above, any words in double quotes are data and can change,
    and any words without double quotes are considered keywords and must be
    specified as shown.

    "CPC1" and "CPC2" are CPC names that are used to select an entry in the
    file. The entry for a CPC contains data about the HMC managing that CPC,
    with its host, userid and password. If two CPCs are managed by the same
    HMC, there would be two CPC entries with the same HMC data.
    """

    default_filepath = 'examples/hmccreds.yaml'

    def __init__(self, filepath=None):
        if filepath is None:
            filepath = self.default_filepath
        self._filepath = filepath

    @property
    def filepath(self):
        """
        File path of this HMC credentials file.
        """
        return self._filepath

    def get_cpc_items(self):
        """
        Return a list of CPC data items from this HMC credentials file.

        Returns:

          list of dict:
            If the HMC credentials file could be opened and successfully be
            processed, returns a list of data items for all CPCs in the HMC
            credentials file, where each data item is a dictionary with with
            the following keys:

              * description: Short description of the CPC (optional)
              * contact: Contact info for the CPC (optional)
              * hmc_host: Hostname or IP address of HMC managing the CPC (req)
              * hmc_userid: Userid to log on to that HMC (required)
              * hmc_password: Password to log on to that HMC (required)

            If the HMC credentials file did not exist or could not be opened
            for reading, returns `None`.

        Raises:

          yaml.parser.ParserError: YAML parsing error in HMC credentials file.

          KeyError: Required 'cpcs' key not found in HMC credentials file.
        """

        try:
            with open(self.filepath, 'r') as fp:
                hmccreds_data = yaml.load(fp)
        except IOError:
            return None

        cpc_items = hmccreds_data['cpcs']
        return cpc_items

    def get_cpc_item(self, cpc_name):
        """
        Return the CPC data item for a given CPC from this HMC credentials
        file.

        Parameters:

          cpc_name (string): CPC name used to select the corresponding HMC
            entry in the HMC credentials file.

        Returns:

          dict:
            If the HMC credentials file could be opened and successfully be
            processed, returns a CPC data item for the specified CPC, with the
            following keys:

              * description: Short description of the CPC (optional)
              * contact: Contact info for the CPC (optional)
              * hmc_host: Hostname or IP address of HMC managing the CPC (req)
              * hmc_userid: Userid to log on to that HMC (required)
              * hmc_password: Password to log on to that HMC (required)

            If the HMC credentials file did not exist or could not be opened
            for reading, returns `None`.

        Raises:

          yaml.parser.ParserError: YAML parsing error in HMC credentials file.

          KeyError: Required 'cpcs' key not found in HMC credentials file.

          ValueError: CPC item not found or required keys missing in CPC item.
        """

        cpc_items = self.get_cpc_items()
        if cpc_items is None:
            return None

        cpc_item = cpc_items.get(cpc_name, None)
        if cpc_item is None:
            raise ValueError(
                "No item found for CPC {!r} in HMC credentials file {!r}".
                format(cpc_name, self.filepath))

        # Required keys in a CPC data item in the HMC credentials file
        required_keys = ['hmc_host', 'hmc_userid', 'hmc_password']

        # Check required keys in CPC data item:
        for key in required_keys:
            if key not in cpc_item or not cpc_item[key]:
                raise ValueError(
                    "Required key {!r} missing in item for CPC {!r} in "
                    "HMC credentials file {!r}".
                    format(key, cpc_name, self.filepath))

        return cpc_item


def get_test_cpc():
    """
    Return the CPC name of the CPC to be tested.

    This is taken from the value of the 'TESTCPC' environment variable.
    If that variable is not set or empty, `None` is returned.

    Returns:

      string: Name of CPC to be tested, or `None` if no CPC has been defined.
    """
    cpc_name = os.environ.get('TESTCPC', None)
    return cpc_name


def setup_cpc(capsys, hmc_creds, fake_data, rt_config=None):
    """
    Set up and return some objects for the CPC that is to be used for testing.

    This function uses the get_test_cpc() function to determine the CPC to be
    used for testing. If no CPC has been defined, this function sets up a faked
    CPC using the zhmcclient mock support.

    Parameters:

      capsys: The pytest 'capsys' fixture the testcase function must specify as
        an argument and pass to this functionhere.

      hmc_creds (HmcCredentials): HMC credentials with CPC data.

      fake_data (dict): Input data in case a mock environment needs to be set
        up. The dict has the following keys:

        * hmc_host (string): Hostname or IP address of the faked HMC.

        * hmc_name (string): HMC name of the faked HMC.

        * hmc_version (string): HMC version of the faked HMC.

        * api_version (string): API version of the faked HMC.

        * cpc_properties (dict): Properties for the faked CPC. 'name' must be
          set.

      rt_config (zhmcclient.RetryTimeoutConfig): Retry / timeout config
        to override the default values. The default values used by this
        function are the global defaults defined for the zhmcclient package,
        whereby connection retries, connection timeout, operation timeout, and
        status timeout have been shortened. The resulting default values should
        be good for most function testcases.

    Returns:

      tuple: Tuple with the objects thathave been set up:

        * cpc_name (string): Name of the CPC to be used (some fake name or
          the real name that has been set up).

        * session (zhmcclient.Session or zhmcclient_mock-FakedSession):
          zhmcclient session object (faked or real) to be used for accessing
          the HMC managing that CPC.

        * client (zhmcclient.Client):
          zhmcclient Client object to be used for accessing the HMC managing
          that CPC.

        * cpc (zhmcclient.Cpc): Cpc resource object representing the CPC to be
          used (faked or real).

        * faked_cpc (zhmcclient_mock.FakedCpc): FakedCpc object in case a
          mock environment was set up (so the caller can add resources to it),
          or otherwise `None`.
    """

    cpc_name = get_test_cpc()

    if cpc_name is None:

        # No test CPC defined in the environment -> use mock support and
        # add a faked CPC.

        cpc_properties = fake_data['cpc_properties']
        cpc_name = cpc_properties['name']

        info(capsys, "Testing with faked CPC %r", cpc_name)

        session = zhmcclient_mock.FakedSession(
            fake_data['hmc_host'], fake_data['hmc_name'],
            fake_data['hmc_version'], fake_data['api_version'])

        faked_cpc = session.hmc.cpcs.add(cpc_properties)

    else:
        # A test CPC is defined in the environment -> use it!

        info(capsys, "Testing with CPC %r", cpc_name)

        eff_rt_config = DEFAULT_RT_CONFIG
        if rt_config:
            eff_rt_config.override_with(rt_config)

        cpc_item = hmc_creds.get_cpc_item(cpc_name)

        assert cpc_item, "HMC credentials file not found: {!r}".\
            format(hmc_creds.filepath)

        session = zhmcclient.Session(
            cpc_item['hmc_host'], cpc_item['hmc_userid'],
            cpc_item['hmc_password'], retry_timeout_config=eff_rt_config)

        faked_cpc = None

    client = zhmcclient.Client(session)

    cpc = client.cpcs.find(name=cpc_name)

    return cpc_name, session, client, cpc, faked_cpc


def print_logging():
    """
    Debug function that prints the relevant settings of all Python loggers
    that are relevant for zhmcclient.
    """
    logger_names = LOGGER_NAMES.values()
    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        print_logger(logger)


def print_logger(logger):
    """
    Debug function that prints the relevant settings of a Python logger.
    """
    print("Debug: Logger %r:" % logger.name)
    print("Debug:   logger level: %s (%s)" %
          (logger.level, logging.getLevelName(logger.level)))
    if not logger.handlers:
        print("Debug:   No handlers")
    for handler in logger.handlers:
        print("Debug:   Handler %s:" % type(handler))
        print("Debug:     handler level: %s (%s)" %
              (handler.level, logging.getLevelName(handler.level)))
        format = getattr(handler.formatter, '_fmt', None)
        print("Debug:     handler format: %r" % format)


def setup_logging():
    """
    Set up logging for the zhmcclient, based on the value of the ZHMC_LOG
    env. variable with the following value::

        COMP=LEVEL[,COMP=LEVEL[,...]]

    Where:

      * ``COMP`` is one of: ``all``, ``api``, ``hmc``.
      * ``LEVEL`` is one of: ``error``, ``warning``, ``info``, ``debug``.

    If the variable is not set, this defaults to::

        all=warning
    """

    log = os.environ.get('ZHMC_LOG', None)

    if log is None:
        log = DEFAULT_LOG

    log_components = LOGGER_NAMES.keys()

    for lc in log_components:
        reset_logger(lc)

    handler = logging.StreamHandler(stream=sys.stderr)
    fs = '%(levelname)s %(name)s: %(message)s'
    handler.setFormatter(logging.Formatter(fs))

    log_specs = log.split(',')
    for log_spec in log_specs:

        # ignore extra ',' at begin, end or in between
        if log_spec == '':
            continue

        try:
            log_comp, log_level = log_spec.split('=', 1)
        except ValueError:
            raise ValueError("Missing '=' in COMP=LEVEL specification "
                             "in ZHMC_LOG variable: {}".format(log_spec))

        level = getattr(logging, log_level.upper(), None)
        if level is None:
            raise ValueError("Invalid level in COMP=LEVEL specification "
                             "in ZHMC_LOG variable: {}".format(log_spec))

        if log_comp not in log_components:
            raise ValueError("Invalid component in COMP=LEVEL specification "
                             "in ZHMC_LOG variable: {}".format(log_spec))

        setup_logger(log_comp, handler, level)


def reset_logger(log_comp):
    """
    Reset the logger for the specified log component (unless it is the root
    logger) to add a NullHandler if it does not have any handlers. Having a
    handler prevents a log request to be propagated to the parent logger.
    """

    name = LOGGER_NAMES[log_comp]
    logger = logging.getLogger(name)

    if name != '' and not logger.handlers:
        logger.addHandler(logging.NullHandler())


def setup_logger(log_comp, handler, level):
    """
    Setup the logger for the specified log component to add the specified
    handler (removing a possibly present NullHandler) and to set it to the
    specified log level. The handler is also set to the specified log level
    because the default level of a handler is 0 which causes it to process all
    levels.
    """

    name = LOGGER_NAMES[log_comp]
    logger = logging.getLogger(name)

    for h in logger.handlers:
        if isinstance(h, logging.NullHandler):
            logger.removeHandler(h)

    handler.setLevel(level)
    logger.addHandler(handler)
    logger.setLevel(level)
