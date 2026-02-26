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
Unit tests for _tape_link module.
"""


import re
import copy
import pytest

from zhmcclient import Client, TapeLink, TapeLinkManager, \
    HTTPError, NotFound
from zhmcclient.mock import FakedSession
from tests.common.utils import assert_resources


# Object IDs and names of our faked resources:
CPC_OID = 'fake-cpc1-oid'
CPC_URI = f'/api/cpcs/{CPC_OID}'
PARTITION_OID = 'partition1-oid'
PARTITION_URI = f'/api/partitions/{PARTITION_OID}'
TL_OID = 'tape-library1-oid'
TL_NAME = 'tape-library 1'
TL_URI = f'/api/tape-libraries/{TL_OID}'
TLINK1_OID = 'tlink1-oid'
TLINK1_NAME = 'tape link 1'
TLINK2_OID = 'tlink2-oid'
TLINK2_NAME = 'tape link 2'


class TestTapeLink:
    """All tests for the TapeLink and TapeLinkManager classes."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.

        Set up a faked session, and add a faked CPC in DPM mode with a
        tape library.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.16.0', '4.10')
        self.client = Client(self.session)

        # Add a faked CPC
        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': CPC_OID,
            # object-uri is set up automatically
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1 (DPM mode)',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
        })
        assert self.faked_cpc.uri == CPC_URI
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')

        # Add a faked partition
        self.faked_partition = self.faked_cpc.partitions.add({
            'object-id': PARTITION_OID,
            # object-uri is set up automatically
            'parent': CPC_URI,
            'class': 'partition',
            'name': 'fake-partition1-name',
            'description': 'Partition #1',
            'status': 'stopped',
        })
        assert self.faked_partition.uri == PARTITION_URI

        # Add a faked console
        self.faked_console = self.session.hmc.consoles.add({
            # object-id is set up automatically
            # object-uri is set up automatically
            # parent will be automatically set
            # class will be automatically set
            'name': 'fake-console-name',
            'description': 'The HMC',
        })
        self.console = self.client.consoles.console

        # Add a faked tape library
        self.faked_tape_library = self.faked_console.tape_library.add({
            'object-id': TL_OID,
            # object-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'cpc-uri': CPC_URI,
            'name': TL_NAME,
            'description': 'Tape Library #1',
            'state': 'online',
        })
        assert self.faked_tape_library.uri == TL_URI
        self.tape_library = self.console.tape_library.find(name=TL_NAME)

    def add_tape_link1(self):
        """Add tape link 1."""

        faked_tape_link = self.faked_tape_library.tape_links.add({
            'element-id': TLINK1_OID,
            # element-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'name': TLINK1_NAME,
            'description': 'Tape Link #1',
            'partition-uri': PARTITION_URI,
        })
        return faked_tape_link

    def add_tape_link2(self):
        """Add tape link 2."""

        faked_tape_link = self.faked_tape_library.tape_links.add({
            'element-id': TLINK2_OID,
            # element-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'name': TLINK2_NAME,
            'description': 'Tape Link #2',
            'partition-uri': PARTITION_URI,
        })
        return faked_tape_link

    def test_tlm_initial_attrs(self):
        """Test initial attributes of TapeLinkManager."""

        tape_link_mgr = self.tape_library.tape_links

        assert isinstance(tape_link_mgr, TapeLinkManager)

        # Verify all public properties of the manager object
        assert tape_link_mgr.resource_class == TapeLink
        assert tape_link_mgr.session == self.session
        assert tape_link_mgr.parent == self.tape_library
        assert tape_link_mgr.tape_library == self.tape_library

    # TODO: Test for TapeLinkManager.__repr__()

    testcases_tlm_list_full_properties = (
        "full_properties_kwargs, prop_names", [
            ({},
             ['element-uri', 'name', 'partition-uri']),
            (dict(full_properties=False),
             ['element-uri', 'name', 'partition-uri']),
        ]
    )

    @pytest.mark.parametrize(
        *testcases_tlm_list_full_properties
    )
    def test_tlm_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test TapeLinkManager.list() with full_properties."""

        # Add two faked tape links
        faked_tape_link1 = self.add_tape_link1()
        faked_tape_link2 = self.add_tape_link2()

        exp_faked_tape_links = [faked_tape_link1, faked_tape_link2]
        tape_link_mgr = self.tape_library.tape_links

        # Execute the code to be tested
        tape_links = tape_link_mgr.list(**full_properties_kwargs)

        assert_resources(tape_links, exp_faked_tape_links, prop_names)

    testcases_tlm_list_filter_args = (
        "filter_args, exp_names", [
            ({'element-id': TLINK1_OID},
             [TLINK1_NAME]),
            ({'element-id': TLINK2_OID},
             [TLINK2_NAME]),
            ({'element-id': [TLINK1_OID, TLINK2_OID]},
             [TLINK1_NAME, TLINK2_NAME]),
            ({'element-id': [TLINK1_OID, TLINK1_OID]},
             [TLINK1_NAME]),
            ({'element-id': TLINK1_OID + 'foo'},
             []),
            ({'element-id': [TLINK1_OID, TLINK2_OID + 'foo']},
             [TLINK1_NAME]),
            ({'element-id': [TLINK2_OID + 'foo', TLINK1_OID]},
             [TLINK1_NAME]),
            ({'name': TLINK1_NAME},
             [TLINK1_NAME]),
            ({'name': TLINK2_NAME},
             [TLINK2_NAME]),
            ({'name': [TLINK1_NAME, TLINK2_NAME]},
             [TLINK1_NAME, TLINK2_NAME]),
            ({'name': TLINK1_NAME + 'foo'},
             []),
            ({'name': [TLINK1_NAME, TLINK2_NAME + 'foo']},
             [TLINK1_NAME]),
            ({'name': [TLINK2_NAME + 'foo', TLINK1_NAME]},
             [TLINK1_NAME]),
            ({'name': [TLINK1_NAME, TLINK1_NAME]},
             [TLINK1_NAME]),
            ({'name': '.*tape link 1'},
             [TLINK1_NAME]),
            ({'name': 'tape link 1.*'},
             [TLINK1_NAME]),
            ({'name': 'tape link .'},
             [TLINK1_NAME, TLINK2_NAME]),
            ({'name': '.ape link 1'},
             [TLINK1_NAME]),
            ({'name': '.+'},
             [TLINK1_NAME, TLINK2_NAME]),
            ({'name': 'tape link 1.+'},
             []),
            ({'name': '.+tape link 1'},
             []),
            ({'name': TLINK1_NAME,
              'element-id': TLINK1_OID},
             [TLINK1_NAME]),
            ({'name': TLINK1_NAME,
              'element-id': TLINK1_OID + 'foo'},
             []),
            ({'name': TLINK1_NAME + 'foo',
              'element-id': TLINK1_OID},
             []),
            ({'name': TLINK1_NAME + 'foo',
              'element-id': TLINK1_OID + 'foo'},
             []),
        ]
    )

    @pytest.mark.parametrize(
        *testcases_tlm_list_filter_args
    )
    def test_tlm_list_filter_args(
            self, filter_args, exp_names):
        """Test TapeLinkManager.list() with filter_args."""

        # Add two faked tape links
        self.add_tape_link1()
        self.add_tape_link2()

        tape_link_mgr = self.tape_library.tape_links

        # Execute the code to be tested
        tape_links = tape_link_mgr.list(filter_args=filter_args)

        assert len(tape_links) == len(exp_names)
        if exp_names:
            names = [tl.properties['name'] for tl in tape_links]
            assert set(names) == set(exp_names)

    testcases_tlm_create = (
        "input_props, exp_prop_names, exp_exc", [
            ({},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-tlink-x'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-tlink-x',
              'partition-uri': PARTITION_URI},
             ['element-uri', 'name', 'partition-uri'],
             None),
        ]
    )

    @pytest.mark.parametrize(
        *testcases_tlm_create
    )
    def test_tlm_create(
            self, input_props, exp_prop_names, exp_exc):
        """Test TapeLinkManager.create()."""

        tape_link_mgr = self.tape_library.tape_links

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                tape_link = tape_link_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            # Note: the TapeLink object returned by TapeLink.create()
            # has the input properties plus 'element-uri'.
            tape_link = tape_link_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(tape_link, TapeLink)
            tape_link_name = tape_link.name
            exp_tape_link_name = tape_link.properties['name']
            assert tape_link_name == exp_tape_link_name
            tape_link_uri = tape_link.uri
            exp_tape_link_uri = tape_link.properties['element-uri']
            assert tape_link_uri == exp_tape_link_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in tape_link.properties
                if prop_name in input_props:
                    value = tape_link.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_tlm_resource_object(self):
        """
        Test TapeLinkManager.resource_object().

        This test exists for historical reasons, and by now is covered by the
        test for BaseManager.resource_object().
        """

        # Add a faked tape link
        faked_tape_link = self.add_tape_link1()
        tape_link_oid = faked_tape_link.oid

        tape_link_mgr = self.tape_library.tape_links

        # Execute the code to be tested
        tape_link = tape_link_mgr.resource_object(tape_link_oid)

        tape_link_uri = f"{TL_URI}/tape-links/{tape_link_oid}"

        assert isinstance(tape_link, TapeLink)

        # Note: Properties inherited from BaseResource are tested there,
        # but we test them again:
        assert tape_link.properties['element-uri'] == tape_link_uri
        assert tape_link.properties['element-id'] == tape_link_oid
        assert tape_link.properties['class'] == 'tape-link'
        assert tape_link.properties['parent'] == TL_URI

    def test_tl_repr(self):
        """Test TapeLink.__repr__()."""

        # Add a faked tape link
        faked_tape_link = self.add_tape_link1()

        tape_link_mgr = self.tape_library.tape_links
        tape_link = tape_link_mgr.find(name=faked_tape_link.name)

        # Execute the code to be tested
        repr_str = repr(tape_link)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{tape_link.__class__.__name__}\s+at\s+'
            rf'0x{id(tape_link):08x}\s+\(\\n.*',
            repr_str)

    def test_tl_delete(self):
        """Test TapeLink.delete()."""

        # Add a faked tape link to be tested and another one
        faked_tape_link = self.add_tape_link1()
        self.add_tape_link2()

        tape_link_mgr = self.tape_library.tape_links

        tape_link = tape_link_mgr.find(name=faked_tape_link.name)

        # Execute the code to be tested.
        tape_link.delete()

        # Check that the tape link no longer exists
        with pytest.raises(NotFound):
            tape_link_mgr.find(name=faked_tape_link.name)

    def test_tl_delete_create_same(self):
        """Test TapeLink.delete() followed by create() with same name."""

        # Add a faked tape link to be tested and another one
        faked_tape_link = self.add_tape_link1()
        tape_link_name = faked_tape_link.name
        self.add_tape_link2()

        # Construct the input properties for a third tape link
        tl3_props = copy.deepcopy(faked_tape_link.properties)
        tl3_props['description'] = 'Third tape link'

        tape_link_mgr = self.tape_library.tape_links
        tape_link = tape_link_mgr.find(name=tape_link_name)

        # Execute the deletion code to be tested.
        tape_link.delete()

        # Check that the tape link no longer exists
        with pytest.raises(NotFound):
            tape_link_mgr.find(name=tape_link_name)

        # Execute the creation code to be tested.
        tape_link_mgr.create(tl3_props)

        # Check that the tape link exists again under that name
        tape_link3 = tape_link_mgr.find(name=tape_link_name)
        description = tape_link3.get_property('description')
        assert description == 'Third tape link'

    testcases_tl_update_properties_tls = (
        "tape_link_name", [
            TLINK1_NAME,
            TLINK2_NAME,
        ]
    )

    testcases_tl_update_properties_props = (
        "input_props", [
            {},
            {'description': 'New tape link description'},
        ]
    )

    @pytest.mark.parametrize(
        *testcases_tl_update_properties_tls
    )
    @pytest.mark.parametrize(
        *testcases_tl_update_properties_props
    )
    def test_tl_update_properties(
            self, input_props, tape_link_name):
        """Test TapeLink.update_properties()."""

        # Add faked tape links
        self.add_tape_link1()
        self.add_tape_link2()

        tape_link_mgr = self.tape_library.tape_links
        tape_link = tape_link_mgr.find(name=tape_link_name)

        tape_link.pull_full_properties()
        saved_properties = copy.deepcopy(tape_link.properties)

        # Execute the code to be tested
        tape_link.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in tape_link.properties
            prop_value = tape_link.properties[prop_name]
            assert prop_value == exp_prop_value

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        tape_link.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in tape_link.properties
            prop_value = tape_link.properties[prop_name]
            assert prop_value == exp_prop_value

    def test_tl_update_name(self):
        """
        Test TapeLink.update_properties() with 'name' property.
        """

        # Add a faked tape link
        faked_tape_link = self.add_tape_link1()
        tape_link_name = faked_tape_link.name

        tape_link_mgr = self.tape_library.tape_links
        tape_link = tape_link_mgr.find(name=tape_link_name)

        new_tape_link_name = "new-" + tape_link_name

        # Execute the code to be tested
        tape_link.update_properties(
            properties={'name': new_tape_link_name})

        # Verify that the resource is no longer found by its old name, using
        # list() (this does not use the name-to-URI cache).
        tape_links_list = tape_link_mgr.list(
            filter_args=dict(name=tape_link_name))
        assert len(tape_links_list) == 0

        # Verify that the resource is no longer found by its old name, using
        # find() (this uses the name-to-URI cache).
        with pytest.raises(NotFound):
            tape_link_mgr.find(name=tape_link_name)

        # Verify that the resource object already reflects the update, even
        # though it has not been refreshed yet.
        assert tape_link.properties['name'] == new_tape_link_name

        # Refresh the resource object and verify that it still reflects the
        # update.
        tape_link.pull_full_properties()
        assert tape_link.properties['name'] == new_tape_link_name

        # Verify that the resource can be found by its new name, using find()
        new_tape_link_find = tape_link_mgr.find(
            name=new_tape_link_name)
        assert new_tape_link_find.properties['name'] == \
            new_tape_link_name

        # Verify that the resource can be found by its new name, using list()
        new_tape_links_list = tape_link_mgr.list(
            filter_args=dict(name=new_tape_link_name))
        assert len(new_tape_links_list) == 1
        new_tape_link_list = new_tape_links_list[0]
        assert new_tape_link_list.properties['name'] == \
            new_tape_link_name

    def test_tl_get_partitions(self):
        """Test TapeLink.get_partitions()."""

        # Add a faked tape link
        faked_tape_link = self.add_tape_link1()

        tape_link_mgr = self.tape_library.tape_links
        tape_link = tape_link_mgr.find(name=faked_tape_link.name)

        # Execute the code to be tested
        partitions = tape_link.get_partitions()

        # Verify the result
        assert isinstance(partitions, list)
        # The partition should be in the list
        assert len(partitions) >= 0

    def test_tl_get_partitions_with_filters(self):
        """Test TapeLink.get_partitions() with name and status filters."""

        # Add a faked tape link
        faked_tape_link = self.add_tape_link1()

        tape_link_mgr = self.tape_library.tape_links
        tape_link = tape_link_mgr.find(name=faked_tape_link.name)

        # Execute the code to be tested with filters
        partitions = tape_link.get_partitions(
            name='fake-partition.*', status='stopped')

        # Verify the result
        assert isinstance(partitions, list)

    def test_tl_get_histories(self):
        """Test TapeLink.get_histories()."""

        # Add a faked tape link
        faked_tape_link = self.add_tape_link1()

        tape_link_mgr = self.tape_library.tape_links
        tape_link = tape_link_mgr.find(name=faked_tape_link.name)

        # Execute the code to be tested
        histories = tape_link.get_histories()

        # Verify the result
        assert isinstance(histories, dict)
        # The histories should contain expected keys
        # (actual keys depend on HMC API response structure)

    def test_tl_get_environment_report(self):
        """Test TapeLink.get_environment_report()."""

        # Add a faked tape link
        faked_tape_link = self.add_tape_link1()

        tape_link_mgr = self.tape_library.tape_links
        tape_link = tape_link_mgr.find(name=faked_tape_link.name)

        # Execute the code to be tested
        report = tape_link.get_environment_report()

        # Verify the result
        assert isinstance(report, dict)
        # The report should contain expected keys
        # (actual keys depend on HMC API response structure)

    def test_tl_update_environment_report(self):
        """Test TapeLink.update_environment_report()."""

        # Add a faked tape link
        faked_tape_link = self.add_tape_link1()

        tape_link_mgr = self.tape_library.tape_links
        tape_link = tape_link_mgr.find(name=faked_tape_link.name)

        # Prepare update properties
        update_props = {
            'acknowledged': True,
            'notes': 'Environment report updated'
        }

        # Execute the code to be tested
        result = tape_link.update_environment_report(properties=update_props)

        # Verify the result
        assert isinstance(result, dict)
        # The result should contain operation results
        # (actual structure depends on HMC API response)

    def test_tl_partition_property(self):
        """Test TapeLink.partition property."""

        # Add a faked tape link
        faked_tape_link = self.add_tape_link1()

        tape_link_mgr = self.tape_library.tape_links
        tape_link = tape_link_mgr.find(name=faked_tape_link.name)

        # Execute the code to be tested
        partition = tape_link.partition

        # Verify the result
        assert partition is not None
        assert partition.uri == PARTITION_URI
