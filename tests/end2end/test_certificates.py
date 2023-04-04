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

from __future__ import absolute_import, print_function

import time
import warnings

import pytest
from requests.packages import urllib3

import zhmcclient

# pylint: disable=unused-import
from zhmcclient.testutils import all_cpcs  # noqa: F401, E501
# pylint: disable=unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from .utils import pick_test_resources, runtest_find_list, skip_warn, \
    skipif_no_secure_boot_feature, standard_partition_props, TEST_PREFIX

urllib3.disable_warnings()

# Properties in minimalistic Certificate objects (e.g. find_by_name())
CERT_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Certificate objects returned by list() without full props
CERT_LIST_PROPS = ['object-uri', 'name', 'type', 'parent', 'parent-name']

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
            skip_warn("No certificates on CPC {c} managed by HMC {h}".
                      format(c=cpc.name, h=hd.host))
        cert_list = pick_test_resources(cert_list)

        for cert in cert_list:
            print("Testing on CPC {c} with cert {ce!r}".
                  format(c=cpc.name, ce=cert.name))
            # noinspection PyTypeChecker
            runtest_find_list(
                session, console.certificates, cert.name, 'name', None,
                CERT_VOLATILE_PROPS, CERT_MINIMAL_PROPS, CERT_LIST_PROPS)


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

        print("Testing on CPC {c}".format(c=cpc.name))

        console = cpc.manager.console
        assert console == console.certificates.console

        cert_name = "{} timestamp {}".format(TEST_PREFIX,
                                             time.strftime('%H.%M.%S'))
        cert_name_new = cert_name + ' updated'

        # Ensure a clean starting point for this test
        try:
            cert = console.certificates.find(name=cert_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test cert from previous run: {ce!r} on CPC {c}".
                format(ce=cert_name, c=cpc.name), UserWarning)
            cert.delete()
        try:
            cert = console.certificates.find(name=cert_name_new)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test cert from previous run: {ce!r} on CPC {c}".
                format(ce=cert_name_new, c=cpc.name), UserWarning)
            cert.delete()

        # Test creating the certificate
        cert, cert_input_props = _import_example_certificate(cpc)
        encoded = cert_input_props.pop('certificate')
        cert_auto_props = {
            'assigned': False,
        }

        for pn, exp_value in cert_input_props.items():
            assert cert.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        cert.pull_full_properties()
        for pn, exp_value in cert_input_props.items():
            assert cert.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        for pn, exp_value in cert_auto_props.items():
            assert cert.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)

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
            print("Testing for DPM on CPC {c}".format(c=cpc.name))

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


def _import_example_certificate(cpc):
    props = {
        # pylint: disable=line-too-long
        "certificate": "MIIFdjCCA14CCQCILyUhzc9RUjANBgkqhkiG9w0BAQsFADB9MQswCQYDVQQGEwJVUzELMAkGA1UECAwCTlkxDzANBgNVBAcMBkFybW9uazETMBEGA1UECgwKemhtY2NsaWVudDETMBEGA1UECwwKemhtY2NsaWVudDEmMCQGA1UEAwwdaHR0cHM6Ly9naXRodWIuY29tL3pobWNjbGllbnQwHhcNMjMwNDE4MDY0OTAyWhcNMzMwNDE1MDY0OTAyWjB9MQswCQYDVQQGEwJVUzELMAkGA1UECAwCTlkxDzANBgNVBAcMBkFybW9uazETMBEGA1UECgwKemhtY2NsaWVudDETMBEGA1UECwwKemhtY2NsaWVudDEmMCQGA1UEAwwdaHR0cHM6Ly9naXRodWIuY29tL3pobWNjbGllbnQwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQDH8F7xMisAESV35LqjC3p6AsrGZ3kEOE5W8wcy0q7TEF9TO7TsAPdWit0e7WT20R1gYErv9uyFJeI4idIjWgTT8GVPixwcXClyywh/ND54voHrMZdbDGbvs5+wcfX/7BDtjRUtzuMtvDswEZqaQU/2W+rDRpb/FolwXDTNm17dSomegm7sw8xQsZGACkU2GPXarJcHWrgytyVghxbIPEvtrOP8XQf/FIBud6Z7/WFONFPSYVFkkmxCM/hOPJBj0CvG6WXV0yNN9a10lcy0yVel0JfX9g0FM0FH4H8pSKEqV2byTcoQjlKQehsuw49TzKEU5pEcdwIz5sMN2XOy8V0bHuoIyoZ54NpkVtqPAMr5MQjvluuiZnU5/6shVfJjChHfYHZQ/rRQbnJhIaKTXgfCUKjm/RrzHwMhy71upSDmhKDB2A5Z1o/pOsHqwUPDW17GBNmFDE/SnbpHhGxemnWWebfxTredFQ6YAy+zThDCXTzglSLsgi64ThDJsHN32/PEa0IiXM6moeRPZOK2NapFF8jFq8WYXvlk0Ianfl9TvgrfEufVx2o+V/0DUxo7TxeoukRuHWsJ7SGfFnWUhoj75mJxgvVLA82SdgTllPWYXTIJBUZ+XsoauOsH+VkDoNINEU3pQOySZj5dzzTYwglnLTBOP8KGxA5zLXSRleSFqwIDAQABMA0GCSqGSIb3DQEBCwUAA4ICAQAXnZZoJgo8I8zOHoQQa0Ocik9k9MCeO7M0gPtD+Xe9JRfoMolxaEZnezmADuJTCepUOUi1cgZXCScmDer2Zc2Y9pldJKhAitBiaajUrTfd0Dl8Gd8WGip8NN+8L9CsELZ+/hQnTG2GHGwi21s/yWt4yT3h2cIViuBqRvNTaxkMh1Devtzlx7haVjNCcDO5muIVBTBynJiaQV5zRaTYiLh+hT6O4OccOHJfnRdFkBRCnnCXE4qtrJg9XJ+NqkP3y0MBZueeQsdnmz9LgSwTiQHWgBI7nJSk0sLgw4AaT18xaZsx9xalKDcy7PN9Ya8IldcG4z+DP2cAoZsKejbZBfsvkV/gYC0g/LxBw0sGJrDaFc8BGDeJRxqwrpsJC8YnXFDi5/SwKII0CpOtb2MxwZC2uzmA9srnV05ta8MbdIQ2xsA8T0MDkTjOPqpJDUg9cqXZbOEOiUywJpYG6XxJdkbxx+IYyOyv8Rn0kLwwAgml7JF3w75fCDKwMw2gEY/0inqtS2NleA8XmA+CZ16YTTBQobyLUrsauVmJm4adRKFgq1OxCRbCGPeRRtD772cpAue2ZTD6Oa8UQlCkEdmXQYjp2PoguWmFI/X9T9P4oREZ182hP4b3EFr2WAhH2waURJmXVATR8IsvKxkSbBxCdVn1zhD55zuOBNLX5f4kq/4ipQ==",  # noqa: E501
        "description":
            "Example certificate for end2end tests.",
        "name":
            "{} timestamp {}".format(TEST_PREFIX, time.strftime('%H.%M.%S')),
        "type": "secure-boot"
    }

    console = cpc.manager.console
    return console.certificates.import_certificate(cpc, props), props
