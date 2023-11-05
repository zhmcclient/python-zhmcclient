# Copyright 2017-2021 IBM Corp. All Rights Reserved.
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
End2end tests for activation profiles (with CPCs in classic mode).

These tests do not change any activation profiles.
"""

from __future__ import absolute_import, print_function

import warnings

import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import classic_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, runtest_find_list, \
    runtest_get_properties, setup_logging, End2endTestWarning

urllib3.disable_warnings()

# Logging for zhmcclient HMC interactions and test functions
LOGGING = False
LOG_FILE = 'test_profile.log'

# Properties in minimalistic ActivationProfile objects (e.g. find_by_name())
ACTPROF_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in ActivationProfile objects returned by list() without full props
ACTPROF_LIST_PROPS = ['element-uri', 'name', 'target-name']

# Properties in image ActivationProfile objects for list(additional_properties)
ACTPROF_ADDITIONAL_PROPS = ['description', 'ipl-address']

# Properties whose values can change between retrievals
ACTPROF_VOLATILE_PROPS = []


def standard_activation_profile_props(cpc, profile_name, profile_type):
    """
    Return the input properties for creating standard activation profile in the
    specified CPC.
    """
    actprof_input_props = {
        'profile-name': profile_name,
        'description': (
            '{} profile for zhmcclient end2end tests'.format(profile_type)),
    }
    if profile_type == 'image':
        # We provide the minimum set of properties needed to create a profile.
        if cpc.prop('processor-count-ifl'):
            actprof_input_props['number-shared-ifl-processors'] = 1
            actprof_input_props['operating-mode'] = 'linux-only'
        elif cpc.prop('processor-count-general-purpose'):
            actprof_input_props['number-shared-general-purpose-processors'] = 1
            actprof_input_props['operating-mode'] = 'esa390'
        else:
            actprof_input_props['number-shared-general-purpose-processors'] = 1
            actprof_input_props['operating-mode'] = 'esa390'
            warnings.warn(
                "CPC {c} shows neither IFL nor CP processors, specifying 1 CP "
                "for image activation profile creation.".
                format(c=cpc.name), End2endTestWarning)

    return actprof_input_props


@pytest.mark.parametrize(
    "profile_type", ['reset', 'image', 'load']
)
def test_actprof_crud(classic_mode_cpcs, profile_type):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete an activation profile.
    """
    if not classic_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in classic mode")

    logger = setup_logging(LOGGING, 'test_actprof_crud', LOG_FILE)

    for cpc in classic_mode_cpcs:
        assert not cpc.dpm_enabled

        actprof_mgr = getattr(cpc, profile_type + '_activation_profiles')

        msg = "Testing on CPC {c}".format(c=cpc.name)
        print(msg)
        logger.info(msg)

        actprof_name = 'ZHMC{}1'.format(profile_type[0].upper())

        # Preparation: Ensure clean starting point for this test
        try:
            _actprof = actprof_mgr.find(name=actprof_name)
        except zhmcclient.NotFound:
            pass
        else:
            msg = ("Preparation: Delete {pt} activation profile {ap!r} on CPC "
                   "{c} from previous run".
                   format(pt=profile_type, ap=actprof_name, c=cpc.name))
            warnings.warn(msg, UserWarning)
            logger.info(msg)
            _actprof.delete()

        # Test creating the activation profile
        actprof_input_props = standard_activation_profile_props(
            cpc, actprof_name, profile_type)

        logger.info("Test: Create %s activation profile %r on CPC %s",
                    profile_type, actprof_name, cpc.name)

        # The code to be tested
        actprof = actprof_mgr.create(actprof_input_props)

        try:
            for pn, exp_value in actprof_input_props.items():
                assert actprof.properties[pn] == exp_value, \
                    "Unexpected value for property {!r}".format(pn)
            actprof.pull_full_properties()
            for pn, exp_value in actprof_input_props.items():
                if pn == 'profile-name':
                    pn = 'name'
                assert actprof.properties[pn] == exp_value, \
                    "Unexpected value for property {!r}".format(pn)

            # Test updating a property of the activation profile

            new_desc = "Updated activation profile description."

            logger.info("Test: Update a property of %s activation profile "
                        "%r on CPC %s", profile_type, actprof_name, cpc.name)

            # The code to be tested
            actprof.update_properties(dict(description=new_desc))

            assert actprof.properties['description'] == new_desc
            actprof.pull_full_properties()
            assert actprof.properties['description'] == new_desc

        finally:
            # Test deleting the activation profile (also cleanup)

            logger.info("Test: Delete %s activation profile %r on CPC %s",
                        profile_type, actprof_name, cpc.name)

            # The code to be tested
            actprof.delete()


@pytest.mark.parametrize(
    "profile_type", ['reset', 'image', 'load']
)
def test_actprof_find_list(classic_mode_cpcs, profile_type):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not classic_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in classic mode")

    for cpc in classic_mode_cpcs:
        assert not cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition
        actprof_mgr = getattr(cpc, profile_type + '_activation_profiles')

        # Pick the activation profiles to test with
        actprof_list = actprof_mgr.list()
        if not actprof_list:
            skip_warn("No {t} activation profiles on CPC {c} managed by "
                      "HMC {h}".
                      format(t=profile_type, c=cpc.name, h=hd.host))
        actprof_list = pick_test_resources(actprof_list)

        for actprof in actprof_list:
            print("Testing on CPC {c} with {pt} activation profile {ap!r}".
                  format(c=cpc.name, pt=profile_type, ap=actprof.name))
            if profile_type == 'image':
                actprof_additional_props = ACTPROF_ADDITIONAL_PROPS
            else:
                actprof_additional_props = None
            runtest_find_list(
                session, actprof_mgr, actprof.name, 'name', 'element-uri',
                ACTPROF_VOLATILE_PROPS, ACTPROF_MINIMAL_PROPS,
                ACTPROF_LIST_PROPS, actprof_additional_props)


@pytest.mark.parametrize(
    "profile_type", ['reset', 'image', 'load']
)
def test_actprof_property(classic_mode_cpcs, profile_type):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test property related methods
    """
    if not classic_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in classic mode")

    for cpc in classic_mode_cpcs:
        assert not cpc.dpm_enabled

        client = cpc.manager.client
        session = cpc.manager.session
        hd = session.hmc_definition
        actprof_mgr = getattr(cpc, profile_type + '_activation_profiles')

        # Pick the activation profiles to test with
        actprof_list = actprof_mgr.list()
        if not actprof_list:
            skip_warn("No {t} activation profiles on CPC {c} managed by "
                      "HMC {h}".
                      format(t=profile_type, c=cpc.name, h=hd.host))
        actprof_list = pick_test_resources(actprof_list)

        for actprof in actprof_list:
            print("Testing on CPC {c} with {pt} activation profile {ap!r}".
                  format(c=cpc.name, pt=profile_type, ap=actprof.name))

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(
                client, actprof.manager, non_list_prop, (2, 15))
