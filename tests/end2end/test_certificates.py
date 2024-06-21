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
End2end tests for Certificates.
"""


import pytest
from requests.packages import urllib3

import zhmcclient

# pylint: disable=unused-import
from zhmcclient.testutils import all_cpcs  # noqa: F401, E501
# pylint: disable=unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from .utils import pick_test_resources, runtest_find_list, skip_warn, \
    skipif_no_secure_boot_feature, standard_partition_props, \
    cleanup_and_import_example_certificate

urllib3.disable_warnings()

# Properties in minimalistic Certificate objects (e.g. find_by_name())
CERT_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Certificate objects returned by list() without full props
CERT_LIST_PROPS = ['object-uri', 'name', 'type', 'parent', 'parent-name']

# Properties in Certificate objects for list(additional_properties)
CERT_ADDITIONAL_PROPS = ['description', 'assigned']

# Properties whose values can change between retrievals of Certificate objects
CERT_VOLATILE_PROPS = []


def test_certificates_find_list(all_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not all_cpcs:
        pytest.skip("HMC definition does not include any defined CPCs.")

    for cpc in all_cpcs:
        skipif_no_secure_boot_feature(cpc)

        session = cpc.manager.session
        hd = session.hmc_definition
        console = cpc.manager.console

        # Pick the certificates to test with
        cert_list = console.certificates.list()
        if not cert_list:
            skip_warn(
                f"No certificates on CPC {cpc.name} managed by HMC {hd.host}")
        cert_list = pick_test_resources(cert_list)

        for cert in cert_list:
            print(f"Testing on CPC {cpc.name} with cert {cert.name!r}")
            # noinspection PyTypeChecker
            runtest_find_list(
                session, console.certificates, cert.name, 'name', None,
                CERT_VOLATILE_PROPS, CERT_MINIMAL_PROPS, CERT_LIST_PROPS,
                CERT_ADDITIONAL_PROPS)


def test_cert_crud(all_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a certificate.
    For DPM cpcs, also create a partition and assign/unassign certificates.
    """
    if not all_cpcs:
        pytest.skip("HMC definition does not include any defined CPCs.")

    for cpc in all_cpcs:
        skipif_no_secure_boot_feature(cpc)

        print(f"Testing on CPC {cpc.name}")

        console = cpc.manager.console
        assert console == console.certificates.console

        # Test creating the certificate
        cert, cert_input_props = cleanup_and_import_example_certificate(cpc)

        cert_name = cert_input_props['name']
        cert_name_new = cert_name + ' updated'

        encoded = cert_input_props.pop('certificate')
        cert_auto_props = {
            'assigned': False,
        }

        for pn, exp_value in cert_input_props.items():
            assert cert.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"
        cert.pull_full_properties()
        for pn, exp_value in cert_input_props.items():
            assert cert.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"
        for pn, exp_value in cert_auto_props.items():
            assert cert.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"

        # Test get_encoded()
        assert cert.get_encoded()['certificate'] == encoded

        # Test dump()
        assert cert.dump()

        # Test updating a property of the certificate

        new_desc = "Update certificate for end2end tests."

        # The code to be tested
        cert.update_properties(dict(description=new_desc))

        assert cert.properties['description'] == new_desc
        cert.pull_full_properties()
        assert cert.properties['description'] == new_desc

        # Test renaming the certificate

        # The code to be tested
        cert.update_properties(dict(name=cert_name_new))

        assert cert.properties['name'] == cert_name_new
        cert.pull_full_properties()
        assert cert.properties['name'] == cert_name_new
        with pytest.raises(zhmcclient.NotFound):
            cpc.partitions.find(name=cert_name)

        # Test assign/unassign the certificate (DPM only)

        # The code to be tested
        if cpc.dpm_enabled:
            print(f"Testing for DPM on CPC {cpc.name}")

            part_name = cert_name_new + " partition"
            part = cpc.partitions.create(
                standard_partition_props(cpc, part_name))

            cert.pull_full_properties()
            part.pull_full_properties()
            assert cert.properties['assigned'] is False
            assert not part.get_property('assigned-certificate-uris')

            part.assign_certificate(cert)

            cert.pull_full_properties()
            part.pull_full_properties()
            assert cert.properties['assigned'] is True
            assert cert.properties['object-uri'] in \
                   part.get_property('assigned-certificate-uris')

            part.unassign_certificate(cert)

            cert.pull_full_properties()
            part.pull_full_properties()
            assert cert.properties['assigned'] is False
            assert not part.get_property('assigned-certificate-uris')

            part.delete()

        # Test deleting the certificate

        # The code to be tested
        cert.delete()

        with pytest.raises(zhmcclient.NotFound):
            console.certificates.find(name=cert_name_new)
