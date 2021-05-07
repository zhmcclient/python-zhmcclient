#!/usr/bin/env python
# Copyright 2016 IBM Corp. All Rights Reserved.
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
Functional test against an HMC, using an *HMC info file* that defines the
expected values.

HMC info files can be created for example by the `hmcinfo_extract` script.
"""

from __future__ import absolute_import

import sys
import os
import yaml
from collections import namedtuple
from requests.packages import urllib3
import pytest

from zhmcclient import Session, Client
from _hmcinfo import HMCInfo

CONFIG_BASEFILE = 'config.yaml'  # in directory of this module

mod_path = sys.modules[__name__].__file__

config_file = os.path.join(os.path.dirname(mod_path), CONFIG_BASEFILE)


# TODO: Consolidate this function into a new _tools/_config module
def get_required_item(config, key, parent_section=None):
    try:
        value = config[key]
    except KeyError:
        parent_str = " within %s section" % parent_section \
                     if parent_section else ""
        print("'%s' not found%s in config file %s" %
              (key, parent_str, config_file))
        sys.exit(1)
    return value


# TODO: Consolidate this function into a new _tools/_config module
def get_optional_item(config, key, default=None):
    try:
        return config[key]
    except KeyError:
        return default


Config = namedtuple('Config',
                    'hmc, userid, password, hmcinfo_file, loglevel, '
                    'logmodule, timestats')


def get_config(config_file):
    """
    Return an Config named tuple with information about this testcase.
    """

    with open(config_file, 'r') as fp:
        config = yaml.load(fp)

    # Expected items in the config file:
    #
    #   general:
    #       loglevel:     - Log level.
    #                       Values: empty->None, 'error', 'warning', 'info',
    #                               'debug'.
    #                       Default: None
    #       logmodule:    - Log module.
    #                       Values: empty->None, 'zhmcclient'.
    #                       Default: None
    #       timestats:    - Controls printing of time statistics.
    #                       Values: 'yes'->True, 'no'->False.
    #                       Default: False
    #   run_hmcinfo:
    #       hmc:          - Hostname or IP address of HMC to use
    #       hmcinfo_file: - File path of HMC info file to use
    #

    run_hmcinfo = get_required_item(config, 'run_hmcinfo')

    hmc = get_required_item(run_hmcinfo, 'hmc', 'run_hmcinfo')
    hmcinfo_file = get_required_item(run_hmcinfo, 'hmcinfo_file',
                                     'run_hmcinfo')

    cred = get_required_item(config, hmc)

    userid = get_required_item(cred, 'userid', hmc)
    password = get_required_item(cred, 'password', hmc)

    general = get_optional_item(config, 'general', None)

    if general:
        loglevel = get_optional_item(general, 'loglevel', None)
        logmodule = get_optional_item(general, 'logmodule', None)
        timestats = get_optional_item(general, 'timestats', False)
    else:
        loglevel = None
        logmodule = None
        timestats = False

    return Config(hmc, userid, password, hmcinfo_file, loglevel, logmodule,
                  timestats)


def get_hmcinfo(hmcinfo_file, hmc, userid):
    """
    Return a new HMCInfo object with the content of the HMC info file.
    """
    hmcinfo = HMCInfo(hmc, userid)
    with open(hmcinfo_file, 'r') as fp:
        hmcinfo.load(fp)
    return hmcinfo


@pytest.fixture(scope='function')
def hmc_client(request):
    """
    Setup/teardown fixture for an HMC session and client.

    It sets attributes on the testcase object (hmc, userid, session, client,
    exp_hmcinfo).
    """

    urllib3.disable_warnings()

    def tearDown():
        self.session.logoff()

    request.addfinalizer(tearDown)
    config = get_config(config_file)
    self = request.instance  # test case object
    self.hmc = config.hmc
    self.userid = config.userid
    self.session = Session(config.hmc, config.userid, config.password)
    self.client = Client(self.session)
    self.exp_hmcinfo = get_hmcinfo(config.hmcinfo_file, config.hmc,
                                   config.userid)


@pytest.fixture(scope='function')
def iter_cpcs(request):
    """
    Parametrization 'fixture' for CPC iteration.

    It returns an iterator over the Cpc objects for the CPCs listed in the HMC
    info file. Unfortunately, this cannot be done from the information in the
    HMC info file alone, but requires to issue the "List CPCs" operation.

    The iterated Cpc objects have the short list of properties.
    """
    def _iter_cpcs():
        self = request.instance  # test case object

        # List the CPCs, in order to get to the Cpc objects
        cpcs = self.client.cpcs.list()

        # The basis for this are the CPCs listed in the HMC info file:
        cpc_uris = [cpc['object-uri'] for cpc in self.exp_hmcinfo.
                    get_op('get', '/api/cpcs')['response_body']['cpcs']]
        for cpc_uri in cpc_uris:
            if self.exp_hmcinfo.get_op('get', cpc_uri) is None:
                print("Skipping verification of CPC without properties in "
                      "HMC info file: uri={}".format(cpc_uri))
                continue

            # Look up the Cpc object for this URI
            found_cpc = None
            for cpc in cpcs:
                if cpc.properties['object-uri'] == cpc_uri:
                    found_cpc = cpc
                    break
            assert found_cpc is not None

            yield found_cpc

    return _iter_cpcs


@pytest.mark.usefixtures("hmc_client")
class TestHmcReadonly(object):
    """
    Test certain read-only operations against an HMC.
    """

    def test_session_properties(self):
        """Test some Session properties."""

        # the properties to be tested already have been set.

        assert self.session.host == self.hmc
        assert self.session.userid == self.userid

    def test_client_properties(self):
        """Test some Client properties."""

        # the properties to be tested already have been set.

        assert self.client.session == self.session

    def test_client_version_info(self):
        """Test Client.version_info()."""

        # the function to be tested:
        version_info = self.client.version_info()

        assert version_info[0] == self.exp_hmcinfo.get_op(
            'get', '/api/version')['response_body']['api-major-version']
        assert version_info[1] == self.exp_hmcinfo.get_op(
            'get', '/api/version')['response_body']['api-minor-version']

    def test_cpcmanager_list(self):
        """Test CpcManager.list()."""
        # Compare these properties with the HMC info. We omit 'status'
        # because it could have changed.
        check_props = ('name', 'object-uri')

        # the function to be tested:
        cpcs = self.client.cpcs.list()

        assert len(cpcs) == len(self.exp_hmcinfo.get_op(
            'get', '/api/cpcs')['response_body']['cpcs'])
        for cpc in cpcs:
            cpc_uri = cpc.properties['object-uri']
            cpc_item = self.exp_hmcinfo.get_op('get', cpc_uri)
            if cpc_item is None or cpc_item['response_body'] is None:
                print("Warning: test_cpcmanager_list() skipped verification "
                      "of CPC without properties in HMC info file: uri={}".
                      format(cpc_uri))
                continue
            exp_cpc_props = cpc_item['response_body']
            for p in check_props:
                assert cpc.properties[p] == exp_cpc_props[p]

    @pytest.mark.parametrize("find_prop", ['name', 'object-uri', 'object-id'])
    def test_cpcmanager_find(self, find_prop):
        """
        Test CpcManager.find() with a single property whose name is specified
        in `find_prop`.

        The test algorithm relies on the property specified in `find_prop` to
        uniquely identify the CPC within the HMC (e.g. 'object-uri' is valid to
        use, but not 'status').
        """
        # Compare these properties with the HMC info. We omit 'status'
        # because it could have changed.
        check_props = ('name', 'object-uri')
        cpc_uris = [cpc['object-uri'] for cpc in self.exp_hmcinfo.get_op(
                    'get', '/api/cpcs')['response_body']['cpcs']]
        for cpc_uri in cpc_uris:
            cpc_item = self.exp_hmcinfo.get_op('get', cpc_uri)
            if cpc_item is None or cpc_item['response_body'] is None:
                print("Warning: test_cpcmanager_find() skipped test of CPC "
                      "without properties in HMC info file: uri={}".
                      format(cpc_uri))
                continue
            exp_cpc_props = cpc_item['response_body']
            find_args = {find_prop: exp_cpc_props[find_prop]}

            # the function to be tested:
            cpc = self.client.cpcs.find(**find_args)

            for p in check_props:
                assert cpc.properties[p] == exp_cpc_props[p]

    @pytest.mark.usefixtures("iter_cpcs")
    def test_cpc_dpm_enabled(self, iter_cpcs):
        """Test Cpc.dpm_enabled, for all CPCs in the HMC info file."""
        for cpc in iter_cpcs():

            # the function to be tested:
            dpm_enabled = cpc.dpm_enabled

            cpc_uri = cpc.properties['object-uri']
            cpc_item = self.exp_hmcinfo.get_op('get', cpc_uri)
            if cpc_item is None or cpc_item['response_body'] is None:
                print("Warning: test_cpc_dpm_enabled() skipped verification "
                      "of CPC without properties in HMC info file: uri={}".
                      format(cpc_uri))
                continue
            exp_cpc_props = cpc_item['response_body']
            assert dpm_enabled == exp_cpc_props.get('dpm-enabled', False)

    @pytest.mark.usefixtures("iter_cpcs")
    def test_lparmanager_list(self, iter_cpcs):
        """Test LparManager.list()."""

        cpcs_tested = 0
        for cpc in iter_cpcs():
            if not cpc.dpm_enabled:
                cpcs_tested += 1
                cpc_uri = cpc.properties['object-uri']

                # Compare these properties with the HMC info. We omit 'status'
                # because it could have changed.
                check_props = ('name', 'object-uri')

                # the function to be tested:
                lpars = cpc.lpars.list()

                assert len(lpars) == len(self.exp_hmcinfo.get_op(
                    'get', cpc_uri + '/logical-partitions')['response_body']
                    ['logical-partitions'])
                for lpar in lpars:
                    lpar_uri = lpar.properties['object-uri']
                    lpar_item = self.exp_hmcinfo.get_op('get', lpar_uri)
                    if lpar_item is None or lpar_item['response_body'] is None:
                        print("Warning: test_lparmanager_list() skipped "
                              "verification of LPAR without properties in "
                              "HMC info file: uri={}".format(lpar_uri))
                        continue
                    exp_lpar_props = lpar_item['response_body']
                    for p in check_props:
                        assert lpar.properties[p] == exp_lpar_props[p]

        if cpcs_tested == 0:
            print("Warning: test_lparmanager_list() did not test any "
                  "CPC (no CPC was in classic mode).")

    @pytest.mark.usefixtures("iter_cpcs")
    def test_partmanager_list(self, iter_cpcs):
        """Test PartitionManager.list()."""

        cpcs_tested = 0
        for cpc in iter_cpcs():
            if cpc.dpm_enabled:
                cpcs_tested += 1
                cpc_uri = cpc.properties['object-uri']

                # Compare these properties with the HMC info. We omit 'status'
                # because it could have changed.
                check_props = ('name', 'object-uri')

                # the function to be tested:
                parts = cpc.partitions.list()

                assert len(parts) == len(self.exp_hmcinfo.get_op(
                    'get', cpc_uri + '/partitions')['response_body']
                    ['partitions'])
                for part in parts:
                    part_uri = part.properties['object-uri']
                    part_item = self.exp_hmcinfo.get_op('get', part_uri)
                    if part_item is None or part_item['response_body'] is None:
                        print("Warning: test_partmanager_list() skipped "
                              "verification of partition without properties "
                              "in HMC info file: uri={}".format(part_uri))
                        continue
                    exp_part_props = part_item['response_body']
                    for p in check_props:
                        assert part.properties[p] == exp_part_props[p]

        if cpcs_tested == 0:
            print("Warning: test_partmanager_list() did not test any "
                  "CPC (no CPC was in DPM mode).")

    @pytest.mark.parametrize("profile_type", ['reset', 'image', 'load'])
    @pytest.mark.usefixtures("iter_cpcs")
    def test_activationprofile_list(self, iter_cpcs, profile_type):
        """Test ActivationProfileManager.list()."""

        cpcs_tested = 0
        for cpc in iter_cpcs():
            cpc_uri = cpc.properties['object-uri']

            if not cpc.dpm_enabled:
                cpcs_tested += 1

                # Compare these properties with the HMC info. We omit 'status'
                # because it could have changed.
                check_props = ('name', 'element-uri')

                profiles_pyname = profile_type + '_activation_profiles'
                profile_mgr = getattr(cpc, profiles_pyname)

                # the function to be tested:
                profiles = profile_mgr.list()

                profiles_jsonname = profile_type + '-activation-profiles'
                assert len(profiles) == len(self.exp_hmcinfo.get_op(
                    'get', cpc_uri + '/' + profiles_jsonname)['response_body']
                    [profiles_jsonname])
                for prof in profiles:
                    prof_uri = prof.properties['element-uri']
                    prof_item = self.exp_hmcinfo.get_op('get', prof_uri)
                    if prof_item is None or prof_item['response_body'] is None:
                        print("Warning: test_activationprofile_list() skipped "
                              "verification of {} activation profile without "
                              "properties in HMC info file: uri={}".
                              format(profile_type, prof_uri))
                        continue
                    exp_prof_props = prof_item['response_body']
                    for p in check_props:
                        assert prof.properties[p] == exp_prof_props[p]

        if cpcs_tested == 0:
            print("Warning: test_activationprofile_list() did not test any "
                  "CPC (no CPC was in classic mode).")


if __name__ == '__main__':
    print("Error: This test cannot be run as a script; use py.test to run it.")
    sys.exit(1)
