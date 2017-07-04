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
Utility functions for unit tests.
"""


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
