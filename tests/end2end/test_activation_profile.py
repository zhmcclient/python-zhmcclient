# Copyright 2017,2021 IBM Corp. All Rights Reserved.
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


import warnings

import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import classic_mode_cpcs  # noqa: F401, E501
from .utils import logger  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, runtest_find_list, \
    runtest_get_properties, End2endTestWarning, skip_missing_api_feature

urllib3.disable_warnings()

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
            f'{profile_type} profile for zhmcclient end2end tests'),
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
                f"CPC {cpc.name} shows neither IFL nor CP processors, "
                "specifying 1 CP for image activation profile creation.",
                End2endTestWarning)

    return actprof_input_props


@pytest.mark.parametrize(
    "profile_type", ['reset', 'image', 'load']
)
def test_actprof_crud(logger, classic_mode_cpcs, profile_type):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete an activation profile.
    """
    if not classic_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in classic mode")

    for cpc in classic_mode_cpcs:
        assert not cpc.dpm_enabled

        console = cpc.manager.console
        skip_missing_api_feature(
            console, 'create-delete-activation-profiles',
            cpc, 'create-delete-activation-profiles')

        actprof_mgr = getattr(cpc, profile_type + '_activation_profiles')

        msg = f"Testing on CPC {cpc.name}"
        print(msg)
        logger.debug(msg)

        actprof_name = f'ZHMC{profile_type[0].upper()}1'

        # Preparation: Ensure clean starting point for this test
        try:
            _actprof = actprof_mgr.find(name=actprof_name)
        except zhmcclient.NotFound:
            pass
        else:
            msg = (
                f"Preparation: Delete {profile_type} activation profile "
                f"{actprof_name!r} on CPC {cpc.name} from previous run")
            warnings.warn(msg, UserWarning)
            logger.debug(msg)
            _actprof.delete()

        # Test creating the activation profile
        actprof_input_props = standard_activation_profile_props(
            cpc, actprof_name, profile_type)

        logger.debug("Create %s activation profile %r on CPC %s",
                     profile_type, actprof_name, cpc.name)

        # The code to be tested
        actprof = actprof_mgr.create(actprof_input_props)

        try:
            for pn, exp_value in actprof_input_props.items():
                assert actprof.properties[pn] == exp_value, \
                    f"Unexpected value for property {pn!r}"
            actprof.pull_full_properties()
            for pn, exp_value in actprof_input_props.items():
                if pn == 'profile-name':
                    pn = 'name'
                assert actprof.properties[pn] == exp_value, \
                    f"Unexpected value for property {pn!r}"

            # Test updating a property of the activation profile

            new_desc = "Updated activation profile description."

            logger.debug("Update a property of %s activation profile "
                         "%r on CPC %s", profile_type, actprof_name, cpc.name)

            # The code to be tested
            actprof.update_properties(dict(description=new_desc))

            assert actprof.properties['description'] == new_desc
            actprof.pull_full_properties()
            assert actprof.properties['description'] == new_desc

        finally:
            # Test deleting the activation profile (also cleanup)

            logger.debug("Delete %s activation profile %r on CPC %s",
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
            skip_warn(
                f"No {profile_type} activation profiles on CPC {cpc.name} "
                f"managed by HMC {hd.host}")
        actprof_list = pick_test_resources(actprof_list)

        for actprof in actprof_list:
            print(f"Testing on CPC {cpc.name} with {profile_type} activation "
                  f"profile {actprof.name!r}")
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

        session = cpc.manager.session
        hd = session.hmc_definition
        actprof_mgr = getattr(cpc, profile_type + '_activation_profiles')

        # Pick the activation profiles to test with
        actprof_list = actprof_mgr.list()
        if not actprof_list:
            skip_warn(
                f"No {profile_type} activation profiles on CPC {cpc.name} "
                f"managed by HMC {hd.host}")
        actprof_list = pick_test_resources(actprof_list)

        for actprof in actprof_list:
            print(f"Testing on CPC {cpc.name} with {profile_type} activation "
                  f"profile {actprof.name!r}")

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(actprof.manager, non_list_prop)
