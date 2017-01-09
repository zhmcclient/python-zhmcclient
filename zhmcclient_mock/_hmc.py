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
The `zhmcclient_mock` package provides a faked HMC with all resources that are
relevant for the `zhmcclient` package. The faked HMC is implemented as a
local Python object and maintains its resource state across operations.
"""

from __future__ import absolute_import

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import six
# from six.moves.urllib.parse import urlparse, parse_qsl

# TODO: Move the resources into their own files.

__all__ = ['FakedBaseResource', 'FakedBaseManager', 'FakedHmc',
           'FakedActivationProfileManager', 'FakedActivationProfile',
           'FakedAdapterManager', 'FakedAdapter',
           'FakedCpcManager', 'FakedCpc',
           'FakedHbaManager', 'FakedHba',
           'FakedLparManager', 'FakedLpar',
           'FakedNicManager', 'FakedNic',
           'FakedPartitionManager', 'FakedPartition',
           'FakedPortManager', 'FakedPort',
           'FakedVirtualFunctionManager', 'FakedVirtualFunction',
           'FakedVirtualSwitchManager', 'FakedVirtualSwitch',
           ]


class FakedBaseResource(object):
    """
    A base class for faked resource classes in the faked HMC.
    """

    def __init__(self, manager, properties):
        self._manager = manager
        self._properties = properties

        if self.manager.oid_prop not in self.properties:
            new_oid = self.manager._new_oid()
            self.properties[self.manager.oid_prop] = new_oid
        self._oid = self.properties[self.manager.oid_prop]

        if self.manager.uri_prop not in self.properties:
            new_uri = self.manager.base_uri + '/' + self.oid
            self.properties[self.manager.uri_prop] = new_uri
        self._uri = self.properties[self.manager.uri_prop]

    @property
    def manager(self):
        """
        The manager for this resource (a derived class of
        :class:`~zhmcclient_mock.FakedBaseManager`).
        """
        return self._manager

    @property
    def properties(self):
        """
        The properties of this resource (a dictionary).
        """
        return self._properties

    @property
    def oid(self):
        """
        The object ID (property 'object-id' or 'element-id') of this resource.
        """
        return self._oid

    @property
    def uri(self):
        """
        The object URI (property 'object-uri' or 'element-uri') of this
        resource.
        """
        return self._uri


class FakedBaseManager(object):
    """
    A base class for manager classes for faked resources in the faked HMC.
    """

    api_root = '/api'  # root of all resource URIs
    next_oid = 1  # next object ID, for auto-generating them

    def __init__(self, parent, resource_class, base_uri, oid_prop, uri_prop):
        self._parent = parent
        self._resource_class = resource_class
        self._base_uri = base_uri  # Base URI for resources of this type
        self._oid_prop = oid_prop
        self._uri_prop = uri_prop
        self._resources = OrderedDict()  # Resource objects, by object ID

    @property
    def parent(self):
        """
        The parent (scoping resource) for this manager (an object of a derived
        class of :class:`~zhmcclient_mock.FakedBaseResource`).
        """
        return self._parent

    @property
    def resource_class(self):
        """
        The resource class managed by this manager (a derived class of
        :class:`~zhmcclient_mock.FakedBaseResource`).
        """
        return self._resource_class

    @property
    def base_uri(self):
        """
        The base URI for URIs of resources managed by this manager.
        """
        return self._base_uri

    @property
    def oid_prop(self):
        """
        The name of the resource property for the object ID ('object-id' or
        'element-id').
        """
        return self._oid_prop

    @property
    def uri_prop(self):
        """
        The name of the resource property for the object URI ('object-uri' or
        'element-uri').
        """
        return self._uri_prop

    def _new_oid(self):
        new_oid = self.next_oid
        self.next_oid += 1
        return str(new_oid)

    def add(self, properties):
        """
        Add a faked resource to this manager.

        Parameters:

          properties (dict):
            Resource properties. If the URI property (e.g. 'object-uri') or the
            object ID property (e.g. 'object-id') are not specified, they
            will be auto-generated.

        Returns:
          FakedBaseResource: The faked resource object.
        """
        resource = self.resource_class(self, properties)
        self._resources[resource.oid] = resource
        return resource

    def remove(self, oid):
        """
        Remove a faked resource from this manager.

        Parameters:

          oid (string):
            The object ID of the resource (e.g. value of the 'object-uri'
            property).
        """
        del self._resources[oid]

    def list(self):
        """
        List the faked resources of this manager.

        Returns:
          list of FakedBaseResource: The faked resource objects of this
            manager.
        """
        return list(six.itervalues(self._resources))

    def lookup_by_oid(self, oid):
        """
        Look up a faked resource by its object ID.

        Parameters:

          oid (string):
            The object ID of the faked resource (e.g. value of the 'object-uri'
            property).

        Returns:
          FakedBaseResource: The faked resource object.

        Raises:
          KeyError: No resource found for this object ID.
        """
        return self._resources[oid]


class FakedHmc(FakedBaseResource):
    """
    A faked HMC.

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common metrhods and attributes.

    An object of this class represents a faked HMC that can have all faked
    resources that are relevant for the zhmcclient package.

    The Python API to this class and its child resource classes is not
    compatible with the zhmcclient API. Instead, these classes serve as an
    in-memory backend for a faked session class (see
    :class:`zhmcclient_mock.FakedSession`) that replaces the
    normal :class:`zhmcclient.Session` class.

    Objects of this class should not be created by the user. Instead,
    access the :attr:`zhmcclient_mock.FakedSession.hmc` attribute.
    """

    def __init__(self, hmc_name, hmc_version, api_version):
        self.hmc_name = hmc_name
        self.hmc_version = hmc_version
        self.api_version = api_version
        self.special_operations = {}  # user-provided operations
        self.cpcs = FakedCpcManager(client=self)

    def add_resources(self, resources):
        """
        Add faked resources to the faked HMC, from the provided resource
        definitions.

        Duplicate resource names in the same scope are not permitted.

        Although this method is typically used to initially load the faked
        HMC with resource state just once, it can be invoked multiple times.

        Parameters:

          resources (dict):
            Definitions of faked resources to be added, see example below.

        Example for 'resources' parameter::

            resources = {
                'cpcs': [  # name of manager attribute for this resource
                    {
                        'properties': {
                            # object-id is not provided -> auto-generated
                            # object-uri is not provided -> auto-generated
                            'name': 'cpc_1',
                            . . .  # more properties
                        },
                        'adapters': [  # name of manager attribute for this
                                       # resource
                            {
                                'properties': {
                                    'object-id': '123',
                                    'object-uri': '/api/cpcs/../adapters/123',
                                    'name': 'ad_1',
                                    . . .  # more properties
                                },
                                'ports': [
                                    {
                                        'properties': {
                                            # element-id is auto-generated
                                            # element-uri is auto-generated
                                            'name': 'port_1',
                                            . . .  # more properties
                                        }
                                    },
                                    . . .  # more Ports
                                ],
                            },
                            . . .  # more Adapters
                        ],
                        . . .  # more CPC child resources of other types
                    },
                    . . .  # more CPCs
                ]
            }
        """
        for child_attr in resources:
            child_list = resources[child_attr]
            self._process_child_list(self, child_attr, child_list)

    def _process_child_list(self, parent_resource, child_attr, child_list):
        child_manager = getattr(parent_resource, child_attr, None)
        if child_manager is None:
            raise ValueError("Invalid child resource type specified in "
                             "resource dictionary: {}".format(child_attr))
        for child_dict in child_list:
            # child_dict is a dict of 'properties' and grand child resources
            properties = child_dict.get('properties', None)
            if properties is None:
                raise ValueError("A resource for resource type {} has no"
                                 "properties specified.".format(child_attr))
            child_resource = child_manager.add(properties)
            for grandchild_attr in child_dict:
                if grandchild_attr == 'properties':
                    continue
                grandchild_list = child_dict[grandchild_attr]
                self._process_child_list(child_resource, grandchild_attr,
                                         grandchild_list)

    @staticmethod
    def _assert_op_key(i, op, key):
        if key not in op:
            raise ValueError("Missing '{}' key in operations item #{}".
                             format(key, i))

    def get(self, uri, logon_required):
        raise NotImplemented("TODO: Implement his method via the faked HMC.")

    def post(self, uri, body, logon_required, wait_for_completion):
        raise NotImplemented("TODO: Implement his method via the faked HMC.")

    def delete(self, uri, logon_required):
        raise NotImplemented("TODO: Implement his method via the faked HMC.")


class FakedActivationProfileManager(FakedBaseManager):
    """
    A manager for faked Activation Profile resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, cpc, profile_type):
        activation_profiles = profile_type + '-activation-profiles'
        super(FakedActivationProfileManager, self).__init__(
            parent=cpc,
            resource_class=FakedActivationProfile,
            base_uri=cpc.uri + '/' + activation_profiles,
            oid_prop='object-id',
            uri_prop='object-uri')
        self._profile_type = profile_type

    @property
    def profile_type(self):
        """
        Type of the activation profile ('reset', 'image', 'load').
        """
        return self._profile_type


class FakedActivationProfile(FakedBaseResource):
    """
    A faked Activation Profile resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedActivationProfile, self).__init__(
            manager=manager,
            properties=properties)


class FakedAdapterManager(FakedBaseManager):
    """
    A manager for faked Adapter resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, cpc):
        super(FakedAdapterManager, self).__init__(
            parent=cpc,
            resource_class=FakedAdapter,
            base_uri=self.api_root + '/adapters',
            oid_prop='object-id',
            uri_prop='object-uri')


class FakedAdapter(FakedBaseResource):
    """
    A faked Adapter resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedAdapter, self).__init__(
            manager=manager,
            properties=properties)
        self._ports = FakedPortManager(adapter=self)

    @property
    def ports(self):
        """
        The Port resources of this Adapter
        (:class:`~zhmcclient_mock.FakedPort`).
        """
        return self._ports


class FakedCpcManager(FakedBaseManager):
    """
    A manager for faked CPC resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, client):
        super(FakedCpcManager, self).__init__(
            parent=client,
            resource_class=FakedCpc,
            base_uri=self.api_root + '/cpcs',
            oid_prop='object-id',
            uri_prop='object-uri')


class FakedCpc(FakedBaseResource):
    """
    A faked CPC resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedCpc, self).__init__(
            manager=manager,
            properties=properties)
        self._lpars = FakedLparManager(cpc=self)
        self._partitions = FakedPartitionManager(cpc=self)
        self._adapters = FakedAdapterManager(cpc=self)
        self._virtual_switches = FakedVirtualSwitchManager(cpc=self)
        self._reset_activation_profiles = FakedActivationProfileManager(
            cpc=self, profile_type='reset')
        self._image_activation_profiles = FakedActivationProfileManager(
            cpc=self, profile_type='image')
        self._load_activation_profiles = FakedActivationProfileManager(
            cpc=self, profile_type='load')

    @property
    def lpars(self):
        """
        :class:`~zhmcclient_mock.FakedLparManager`: Access to the faked LPAR
        resources of this CPC.
        """
        return self._lpars

    @property
    def partitions(self):
        """
        :class:`~zhmcclient_mock.FakedPartitionManager`: Access to the faked
        Partition resources of this CPC.
        """
        return self._partitions

    @property
    def adapters(self):
        """
        :class:`~zhmcclient_mock.FakedAdapterManager`: Access to the faked
        Adapter resources of this CPC.
        """
        return self._adapters

    @property
    def virtual_switches(self):
        """
        :class:`~zhmcclient_mock.FakedVirtualSwitchManager`: Access to the
        faked Virtual Switch resources of this CPC.
        """
        return self._virtual_switches

    @property
    def reset_activation_profiles(self):
        """
        :class:`~zhmcclient_mock.FakedActivationProfileManager`: Access to the
        faked Reset Activation Profile resources of this CPC.
        """
        return self._reset_activation_profiles

    @property
    def image_activation_profiles(self):
        """
        :class:`~zhmcclient_mock.FakedActivationProfileManager`: Access to the
        faked Image Activation Profile resources of this CPC.
        """
        return self._image_activation_profiles

    @property
    def load_activation_profiles(self):
        """
        :class:`~zhmcclient_mock.FakedActivationProfileManager`: Access to the
        faked Load Activation Profile resources of this CPC.
        """
        return self._load_activation_profiles


class FakedHbaManager(FakedBaseManager):
    """
    A manager for faked HBA resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, partition):
        super(FakedHbaManager, self).__init__(
            parent=partition,
            resource_class=FakedHba,
            base_uri=partition.uri + '/hbas',
            oid_prop='element-id',
            uri_prop='element-uri')

    def add(self, properties):
        """
        Add a faked HBA resource to this manager.

        This method also updates the 'hba-uris' property in the parent
        Partition resource (if it exists).

        Parameters:

          properties (dict):
            Resource properties. If the URI property ('element-uri') or the
            object ID property ('element-id') are not specified, they
            will be auto-generated.

        Returns:
          :class:`zhmcclient_mock.FakedHba`: The faked resource object.
        """
        new_hba = super(FakedHbaManager, self).add(properties)
        partition = self.parent
        if 'hba-uris' in partition.properties:
            partition.properties['hba-uris'].append(new_hba.uri)
        return new_hba

    def remove(self, oid):
        """
        Remove a faked HBA resource from this manager.

        This method also updates the 'hba-uris' property in the parent
        Partition resource (if it exists).

        Parameters:

          oid (string):
            The object ID of the faked HBA resource.
        """
        hba = self.lookup_by_oid(oid)
        partition = self.parent
        if 'hba-uris' in partition.properties:
            del partition.properties['hba-uris'][hba.uri]
        super(FakedHbaManager, self).remove(oid)  # deletes the resource


class FakedHba(FakedBaseResource):
    """
    A faked HBA resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedHba, self).__init__(
            manager=manager,
            properties=properties)


class FakedLparManager(FakedBaseManager):
    """
    A manager for faked LPAR resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, cpc):
        super(FakedLparManager, self).__init__(
            parent=cpc,
            resource_class=FakedLpar,
            base_uri=self.api_root + '/logical-partitions',
            oid_prop='object-id',
            uri_prop='object-uri')


class FakedLpar(FakedBaseResource):
    """
    A faked LPAR resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedLpar, self).__init__(
            manager=manager,
            properties=properties)


class FakedNicManager(FakedBaseManager):
    """
    A manager for faked NIC resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, partition):
        super(FakedNicManager, self).__init__(
            parent=partition,
            resource_class=FakedNic,
            base_uri=partition.uri + '/nics',
            oid_prop='element-id',
            uri_prop='element-uri')

    def add(self, properties):
        """
        Add a faked NIC resource to this manager.

        This method also updates the 'nic-uris' property in the parent
        Partition resource (if it exists).

        Parameters:

          properties (dict):
            Resource properties. If the URI property ('element-uri') or the
            object ID property ('element-id') are not specified, they
            will be auto-generated.

        Returns:
          :class:`zhmcclient_mock.FakedNic`: The faked resource object.
        """
        new_nic = super(FakedNicManager, self).add(properties)
        partition = self.parent
        if 'nic-uris' in partition.properties:
            partition.properties['nic-uris'].append(new_nic.uri)
        return new_nic

    def remove(self, oid):
        """
        Remove a faked NIC resource from this manager.

        This method also updates the 'nic-uris' property in the parent
        Partition resource (if it exists).

        Parameters:

          oid (string):
            The object ID of the faked NIC resource.
        """
        nic = self.lookup_by_oid(oid)
        partition = self.parent
        if 'nic-uris' in partition.properties:
            del partition.properties['nic-uris'][nic.uri]
        super(FakedNicManager, self).remove(oid)  # deletes the resource


class FakedNic(FakedBaseResource):
    """
    A faked NIC resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedNic, self).__init__(
            manager=manager,
            properties=properties)


class FakedPartitionManager(FakedBaseManager):
    """
    A manager for faked Partition resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, cpc):
        super(FakedPartitionManager, self).__init__(
            parent=cpc,
            resource_class=FakedPartition,
            base_uri=self.api_root + '/partitions',
            oid_prop='object-id',
            uri_prop='object-uri')


class FakedPartition(FakedBaseResource):
    """
    A faked Partition resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedPartition, self).__init__(
            manager=manager,
            properties=properties)
        self._nics = FakedNicManager(partition=self)
        self._hbas = FakedHbaManager(partition=self)
        self._virtual_functions = FakedVirtualFunctionManager(partition=self)

    @property
    def nics(self):
        """
        :class:`~zhmcclient_mock.FakedNicManager`: Access to the faked NIC
        resources of this Partition.
        """
        return self._nics

    @property
    def hbas(self):
        """
        :class:`~zhmcclient_mock.FakedHbaManager`: Access to the faked HBA
        resources of this Partition.
        """
        return self._hbas

    @property
    def virtual_functions(self):
        """
        :class:`~zhmcclient_mock.FakedVirtualFunctionManager`: Access to the
        faked Virtual Function resources of this Partition.
        """
        return self._virtual_functions


class FakedPortManager(FakedBaseManager):
    """
    A manager for faked Adapter Port resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, adapter):
        super(FakedPortManager, self).__init__(
            parent=adapter,
            resource_class=FakedPort,
            base_uri=adapter.uri + '/ports',
            oid_prop='element-id',
            uri_prop='element-uri')

    def add(self, properties):
        """
        Add a faked Port resource to this manager.

        This method also updates the 'network-port-uris' or 'storage-port-uris'
        property in the parent Adapter resource (whichever exists, gets
        updated).

        Parameters:

          properties (dict):
            Resource properties. If the URI property ('element-uri') or the
            object ID property ('element-id') are not specified, they
            will be auto-generated.

        Returns:
          :class:`zhmcclient_mock.FakedPort`: The resource object.
        """
        new_port = super(FakedPortManager, self).add(properties)
        adapter = self.parent
        if 'network-port-uris' in adapter.properties:
            adapter.properties['network-port-uris'].append(new_port.uri)
        elif 'storage-port-uris' in adapter.properties:
            adapter.properties['storage-port-uris'].append(new_port.uri)
        return new_port

    def remove(self, oid):
        """
        Remove a faked Port resource from this manager.

        This method also updates the 'network-port-uris' or 'storage-port-uris'
        property in the parent Adapter resource (whichever exists, gets
        updated).

        Parameters:

          oid (string):
            The object ID of the Port resource.
        """
        port = self.lookup_by_oid(oid)
        adapter = self.parent
        if 'network-port-uris' in adapter.properties:
            del adapter.properties['network-port-uris'][port.uri]
        elif 'storage-port-uris' in adapter.properties:
            del adapter.properties['storage-port-uris'][port.uri]
        super(FakedPortManager, self).remove(oid)  # deletes the resource


class FakedPort(FakedBaseResource):
    """
    A faked Adapter Port resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedPort, self).__init__(
            manager=manager,
            properties=properties)


class FakedVirtualFunctionManager(FakedBaseManager):
    """
    A manager for faked Virtual Function resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, partition):
        super(FakedVirtualFunctionManager, self).__init__(
            parent=partition,
            resource_class=FakedVirtualFunction,
            base_uri=partition.uri + '/virtual-functions',
            oid_prop='element-id',
            uri_prop='element-uri')

    def add(self, properties):
        """
        Add a faked Virtual Function resource to this manager.

        This method also updates the 'virtual-function-uris' property in the
        parent Partition resource (if it exists).

        Parameters:

          properties (dict):
            Resource properties. If the URI property ('element-uri') or the
            object ID property ('element-id') are not specified, they
            will be auto-generated.

        Returns:
          :class:`zhmcclient_mock.FakedVirtualFunction`: The faked resource
            object.
        """
        new_virtual_function = super(FakedVirtualFunctionManager,
                                     self).add(properties)
        partition = self.parent
        if 'virtual-function-uris' in partition.properties:
            partition.properties['virtual-function-uris'].append(
                new_virtual_function.uri)
        return new_virtual_function

    def remove(self, oid):
        """
        Remove a faked Virtual Function resource from this manager.

        This method also updates the 'virtual-function-uris' property in the
        parent Partition resource (if it exists).

        Parameters:

          oid (string):
            The object ID of the faked Virtual Function resource.
        """
        virtual_function = self.lookup_by_oid(oid)
        partition = self.parent
        if 'virtual-function-uris' in partition.properties:
            vf_uris = partition.properties['virtual-function-uris']
            del vf_uris[virtual_function.uri]
        super(FakedVirtualFunctionManager, self).remove(oid)  # deletes res.


class FakedVirtualFunction(FakedBaseResource):
    """
    A faked Virtual Function resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedVirtualFunction, self).__init__(
            manager=manager,
            properties=properties)


class FakedVirtualSwitchManager(FakedBaseManager):
    """
    A manager for faked Virtual Switch resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, cpc):
        super(FakedVirtualSwitchManager, self).__init__(
            parent=cpc,
            resource_class=FakedVirtualSwitch,
            base_uri=self.api_root + '/virtual-switches',
            oid_prop='object-id',
            uri_prop='object-uri')


class FakedVirtualSwitch(FakedBaseResource):
    """
    A faked Virtual Switch resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedVirtualSwitch, self).__init__(
            manager=manager,
            properties=properties)


URLS = (

    # In all modes:
    '/api/cpcs', 'CpcsHandler',
    '/api/cpcs/(.*)', 'CpcHandler',
    '/api/version', 'VersionHandler',

    # Only in DPM mode:
    '/api/cpcs/(.*)/operations/start', 'CpcStartHandler',
    '/api/cpcs', 'CpcsHandler',
    '/api/cpcs/(.*)', 'CpcHandler',
    '/api/version', 'VersionHandler',

    # Only in DPM mode:
    '/api/cpcs/(.*)/operations/start', 'CpcStartHandler',
    '/api/cpcs/(.*)/operations/stop', 'CpcStopHandler',
    '/api/cpcs/(.*)/operations/export-port-names-list',
    'CpcExportPortNamesListHandler',
    '/api/cpcs/(.*)/adapters', 'AdaptersHandler',
    '/api/adapters/(.*)', 'AdapterHandler',
    '/api/adapters/(.*)/network-ports/(.*)', 'NetworkPortHandler',
    '/api/adapters/(.*)/storage-ports/(.*)', 'StoragePortHandler',
    '/api/cpcs/(.*)/partitions', 'PartitionsHandler',
    '/api/partitions/(.*)', 'PartitionHandler',
    '/api/partitions/(.*)/operations/start', 'PartitionStartHandler',
    '/api/partitions/(.*)/operations/stop', 'PartitionStopHandler',
    '/api/partitions/(.*)/operations/scsi-dump', 'PartitionScsiDumpHandler',
    '/api/partitions/(.*)/operations/psw-restart',
    'PartitionPswRestartHandler',
    '/api/partitions/(.*)/operations/mount-iso-image',
    'PartitionMountIsoImageHandler',
    '/api/partitions/(.*)/operations/unmount-iso-image',
    'PartitionUnmountIsoImageHandler',
    '/api/partitions/(.*)/hbas', 'HbasHandler',
    '/api/partitions/(.*)/hbas/(.*)', 'HbaHandler',
    '/api/partitions/(.*)/hbas/(.*)/operations/reassign-storage-adapter-port',
    'HbaReassignPortHandler',
    '/api/partitions/(.*)/nics', 'NicsHandler',
    '/api/partitions/(.*)/nics/(.*)', 'NicHandler',
    '/api/partitions/(.*)/virtual-functions', 'VirtualFunctionsHandler',
    '/api/partitions/(.*)/virtual-functions/(.*)', 'VirtualFunctionHandler',
    '/api/cpcs/(.*)/virtual-switches', 'VirtualSwitchesHandler',
    '/api/virtual-switches/(.*)', 'VirtualSwitchHandler',
    '/api/virtual-switches/(.*)/operations/get-connected-vnics',
    'VirtualSwitchGetVnicsHandler',

    # Only in classic (or ensemble) mode:
    # '/api/cpcs/(.*)/operations/activate', 'CpcActivateHandler',
    # '/api/cpcs/(.*)/operations/deactivate', 'CpcDeactivateHandler',
    '/api/cpcs/(.*)/operations/import-profiles', 'CpcImportProfilesHandler',
    '/api/cpcs/(.*)/operations/export-profiles', 'CpcExportProfilesHandler',
    '/api/cpcs/(.*)/logical-partitions', 'LparsHandler',
    '/api/logical-partitions/(.*)', 'LparHandler',
    '/api/logical-partitions/(.*)/operations/activate', 'LparActivateHandler',
    '/api/logical-partitions/(.*)/operations/deactivate',
    'LparDeactivateHandler',
    '/api/logical-partitions/(.*)/operations/load', 'LparLoadHandler',
    '/api/cpcs/(.*)/reset-activation-profiles', 'ResetActProfilesHandler',
    '/api/cpcs/(.*)/reset-activation-profiles/(.*)', 'ResetActProfileHandler',
    '/api/cpcs/(.*)/image-activation-profiles', 'ImageActProfilesHandler',
    '/api/cpcs/(.*)/image-activation-profiles/(.*)', 'ImageActProfileHandler',
    '/api/cpcs/(.*)/load-activation-profiles', 'LoadActProfilesHandler',
    '/api/cpcs/(.*)/load-activation-profiles/(.*)', 'LoadActProfileHandler',
)
