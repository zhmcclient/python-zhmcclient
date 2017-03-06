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

from ._idpool import IdPool

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

    def update(self, properties):
        """
        update the properties of this resource.

        Parameters:

          properties (dict):
            Resource properties to be updated. Any other properties remain
            unchanged.
        """
        self.properties.update(properties)


class FakedBaseManager(object):
    """
    A base class for manager classes for faked resources in the faked HMC.
    """

    api_root = '/api'  # root of all resource URIs
    next_oid = 1  # next object ID, for auto-generating them

    def __init__(self, hmc, parent, resource_class, base_uri, oid_prop,
                 uri_prop):
        self._hmc = hmc
        self._parent = parent
        self._resource_class = resource_class
        self._base_uri = base_uri  # Base URI for resources of this type
        self._oid_prop = oid_prop
        self._uri_prop = uri_prop
        self._resources = OrderedDict()  # Resource objects, by object ID

    @property
    def hmc(self):
        """
        The faked HMC this manager is part of (an object of
        :class:`~zhmcclient_mock.FakedHmc`).
        """
        return self._hmc

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

        For URI-based lookup, the resource is also added to the faked HMC.

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
        self._hmc._resources[resource.uri] = resource
        return resource

    def remove(self, oid):
        """
        Remove a faked resource from this manager.

        Parameters:

          oid (string):
            The object ID of the resource (e.g. value of the 'object-uri'
            property).
        """
        uri = self._resources[oid].uri
        del self._resources[oid]
        del self._hmc._resources[uri]

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
        Look up a faked resource by its object ID, in the scope of this
        manager.

        Parameters:

          oid (string):
            The object ID of the faked resource (e.g. value of the 'object-id'
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
        self.cpcs = FakedCpcManager(hmc=self, client=self)
        self._resources = {}  # by URI

    def add_resources(self, resources):
        """
        Add faked resources to the faked HMC, from the provided resource
        definitions.

        Duplicate resource names in the same scope are not permitted.

        Although this method is typically used to initially load the faked
        HMC with resource state just once, it can be invoked multiple times.

        Parameters:

          resources (dict):
            resource dictionary with definitions of faked resources to be
            added. For an explanation of how the resource dictionary is set up,
            see the example below.

            For requirements on and auto-generation of certain resource
            properties, see the ``add()`` methods of the various faked resource
            managers (e.g. :meth:`zhmcclient_mock.FakedCpcManager.add`).

        Example for resource dictionary::

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

        The resource dictionary specifies a tree of resource managers and
        resources, in an alternating manner. It starts with the top-level
        resource managers (``cpcs`` key), which contains a list of CPC
        resources.

        Each resource specifies its own properties (``properties`` key)
        and the resource managers for its child resources. For example, the
        CPC resource specifies its adapter child resources using the
        ``adapters`` key. The keys for the child resource managers are the
        attribute names of these resource managers in the parent resource. For
        example, the ``adapters`` key is named after the
        :attr:`zhmcclient.Cpc.adapters` attribute (which has the same name
        as in its corresponding faked CPC resource:
        :attr:`zhmcclient_mock.FakedCpc.adapters`).
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

    def lookup_by_uri(self, uri):
        """
        Look up a faked resource by its object URI, within this faked HMC.

        Parameters:

          uri (string):
            The object URI of the faked resource (e.g. value of the
            'object-uri' property).

        Returns:
          :class:`~zhmcclient_mock.FakedBaseResource`: The faked resource.

        Raises:
          KeyError: No resource found for this object ID.
        """
        return self._resources[uri]


class FakedActivationProfileManager(FakedBaseManager):
    """
    A manager for faked Activation Profile resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, cpc, profile_type):
        activation_profiles = profile_type + '-activation-profiles'
        super(FakedActivationProfileManager, self).__init__(
            hmc=hmc,
            parent=cpc,
            resource_class=FakedActivationProfile,
            base_uri=cpc.uri + '/' + activation_profiles,
            oid_prop='element-id',
            uri_prop='element-uri')
        self._profile_type = profile_type

    def add(self, properties):
        """
        Add a faked Activation Profile resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedActivationProfile`: The faked
            Activation Profile resource.
        """
        return super(FakedActivationProfileManager, self).add(properties)

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

    def __init__(self, hmc, cpc):
        super(FakedAdapterManager, self).__init__(
            hmc=hmc,
            parent=cpc,
            resource_class=FakedAdapter,
            base_uri=self.api_root + '/adapters',
            oid_prop='object-id',
            uri_prop='object-uri')

    def add(self, properties):
        """
        Add a faked Adapter resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.
            * 'adapter-family' or 'type' is required to be specified, in order
              to determine whether the adapter is a network or storage adapter.
            * 'adapter-family' is auto-set based upon 'type', if not specified.
            * 'network-port-uris' is auto-set to an empty list, if not set,
              for network adapters.
            * 'storage-port-uris' is auto-set to an empty list, if not set,
              for storage adapters.

        Returns:
          :class:`~zhmcclient_mock.FakedAdapter`: The faked Adapter resource.
        """
        return super(FakedAdapterManager, self).add(properties)


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
        if 'adapter-family' in properties:
            family = properties['adapter-family']
            if family in ('osa', 'roce', 'hipersockets'):
                self._adapter_kind = 'network'
            elif family in ('ficon',):
                self._adapter_kind = 'storage'
            else:
                self._adapter_kind = 'other'
        elif 'type' in properties:
            # because 'type' is more specific than 'adapter-family', we can
            # auto-set 'adapter-family' from 'type'.
            type_ = properties['type']
            if type_ in ('osd', 'osm'):
                self._properties['adapter-family'] = 'osa'
                self._adapter_kind = 'network'
            elif type_ == 'roce':
                self._properties['adapter-family'] = 'roce'
                self._adapter_kind = 'network'
            elif type_ == 'hipersockets':
                self._properties['adapter-family'] = 'hipersockets'
                self._adapter_kind = 'network'
            elif type_ == 'fcp':
                self._properties['adapter-family'] = 'ficon'
                self._adapter_kind = 'storage'
            elif type_ == 'crypto':
                self._properties['adapter-family'] = 'crypto'
                self._adapter_kind = 'other'
            elif type_ == 'zedc':
                self._properties['adapter-family'] = 'accelerator'
                self._adapter_kind = 'other'
            else:
                raise ValueError("FakedAdapter with object-id=%s has an "
                                 "unknown value in its 'type' property: %s." %
                                 (self.oid, type_))
        else:
            raise ValueError("FakedAdapter with object-id=%s must have "
                             "'adapter-family' or 'type' property specified." %
                             self.oid)
        if self.adapter_kind == 'network':
            if 'network-port-uris' not in self.properties:
                self._properties['network-port-uris'] = []
            self._ports = FakedPortManager(hmc=manager.hmc, adapter=self)
        elif self.adapter_kind == 'storage':
            if 'storage-port-uris' not in self.properties:
                self._properties['storage-port-uris'] = []
            self._ports = FakedPortManager(hmc=manager.hmc, adapter=self)
        else:
            self._ports = None

    @property
    def ports(self):
        """
        :class:`~zhmcclient_mock.FakedPort`: The Port resources of this
        Adapter.

        If the kind of adapter does not have ports, this is `None`.
        """
        return self._ports

    @property
    def adapter_kind(self):
        """
        string: The kind of adapter, determined from the 'adapter-family' or
        'type' properties. This is currently used to distinguish storage and
        network adapters.

        Possible values are:
        * 'network' - A network adapter (OSA, ROCE, Hipersockets)
        * 'storage' - A storage adapter (FICON, FCP)
        * 'other' - Another adapter (zEDC, Crypto)
        """
        return self._adapter_kind


class FakedCpcManager(FakedBaseManager):
    """
    A manager for faked CPC resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, client):
        super(FakedCpcManager, self).__init__(
            hmc=hmc,
            parent=client,
            resource_class=FakedCpc,
            base_uri=self.api_root + '/cpcs',
            oid_prop='object-id',
            uri_prop='object-uri')

    def add(self, properties):
        """
        Add a faked CPC resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedCpc`: The faked CPC resource.
        """
        return super(FakedCpcManager, self).add(properties)


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
        self._lpars = FakedLparManager(hmc=manager.hmc, cpc=self)
        self._partitions = FakedPartitionManager(hmc=manager.hmc, cpc=self)
        self._adapters = FakedAdapterManager(hmc=manager.hmc, cpc=self)
        self._virtual_switches = FakedVirtualSwitchManager(
            hmc=manager.hmc, cpc=self)
        self._reset_activation_profiles = FakedActivationProfileManager(
            hmc=manager.hmc, cpc=self, profile_type='reset')
        self._image_activation_profiles = FakedActivationProfileManager(
            hmc=manager.hmc, cpc=self, profile_type='image')
        self._load_activation_profiles = FakedActivationProfileManager(
            hmc=manager.hmc, cpc=self, profile_type='load')

    @property
    def dpm_enabled(self):
        """
        bool: Indicates whether this CPC is in DPM mode.

        This is based upon the 'dpm-enabled' property and defaults to `False`.
        """
        return self.properties.get('dpm-enabled', False)

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

    def __init__(self, hmc, partition):
        super(FakedHbaManager, self).__init__(
            hmc=hmc,
            parent=partition,
            resource_class=FakedHba,
            base_uri=partition.uri + '/hbas',
            oid_prop='element-id',
            uri_prop='element-uri')

    def add(self, properties):
        """
        Add a faked HBA resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.
            * 'adapter-port-uri' identifies the backing FCP port for this HBA
              and is required to be specified.
            * 'device-number' will be auto-generated with a unique value
              within the partition in the range 0x8000 to 0xFFFF, if not
              specified.

            This method also updates the 'hba-uris' property in the parent
            faked Partition resource, by adding the URI for the faked HBA
            resource.

        Returns:
          :class:`~zhmcclient_mock.FakedHba`: The faked HBA resource.
        """
        new_hba = super(FakedHbaManager, self).add(properties)
        if 'adapter-port-uri' not in new_hba.properties:
            raise ValueError("FakedHba with object-id=%s must have "
                             "'adapter-port-uri' property." %
                             new_hba.oid)
        # We don't verify that the specified URI actually exists, because
        # it might not have been added yet, and we don't want to impose too
        # much of an ordering requirement on the resources that are added.
        partition = self.parent
        assert 'hba-uris' in partition.properties
        partition.properties['hba-uris'].append(new_hba.uri)
        if 'device-number' not in new_hba.properties:
            devno = partition.devno_alloc()
            new_hba.properties['device-number'] = devno
        return new_hba

    def remove(self, oid):
        """
        Remove a faked HBA resource.

        This method also updates the 'hba-uris' property in the parent
        Partition resource, by removing the URI for the faked HBA resource.

        Parameters:

          oid (string):
            The object ID of the faked HBA resource.
        """
        hba = self.lookup_by_oid(oid)
        partition = self.parent
        devno = hba.properties.get('device-number', None)
        if devno:
            partition.devno_free_if_allocated(devno)
        assert 'hba-uris' in partition.properties
        hba_uris = partition.properties['hba-uris']
        hba_uris.remove(hba.uri)
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

    def __init__(self, hmc, cpc):
        super(FakedLparManager, self).__init__(
            hmc=hmc,
            parent=cpc,
            resource_class=FakedLpar,
            base_uri=self.api_root + '/logical-partitions',
            oid_prop='object-id',
            uri_prop='object-uri')

    def add(self, properties):
        """
        Add a faked LPAR resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedLpar`: The faked LPAR resource.
        """
        return super(FakedLparManager, self).add(properties)


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

    def __init__(self, hmc, partition):
        super(FakedNicManager, self).__init__(
            hmc=hmc,
            parent=partition,
            resource_class=FakedNic,
            base_uri=partition.uri + '/nics',
            oid_prop='element-id',
            uri_prop='element-uri')

    def add(self, properties):
        """
        Add a faked NIC resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.
            * Either 'network-adapter-port-uri' (for backing ROCE adapters) or
              'virtual-switch-uri'(for backing OSA or Hipersockets adapters) is
              required to be specified.
            * 'device-number' will be auto-generated with a unique value
              within the partition in the range 0x8000 to 0xFFFF, if not
              specified.

            This method also updates the 'nic-uris' property in the parent
            faked Partition resource, by adding the URI for the faked NIC
            resource.

        Returns:
          :class:`zhmcclient_mock.FakedNic`: The faked NIC resource.
        """
        new_nic = super(FakedNicManager, self).add(properties)
        if 'network-adapter-port-uri' not in new_nic.properties and \
                'virtual-switch-uri' not in new_nic.properties:
            raise ValueError("FakedNic with object ID %s must specify "
                             "either a 'network-adapter-port-uri' property "
                             "(for backing ROCE adapters) or a "
                             "'virtual-switch-uri' property (for backing OSA "
                             "and Hipersocket adapters)." % new_nic.oid)
        # We don't verify that the specified URI actually exists, because
        # it might not have been added yet, and we don't want to impose too
        # much of an ordering requirement on the resources that are added.
        partition = self.parent
        assert 'nic-uris' in partition.properties
        partition.properties['nic-uris'].append(new_nic.uri)
        if 'device-number' not in new_nic.properties:
            devno = partition.devno_alloc()
            new_nic.properties['device-number'] = devno
        return new_nic

    def remove(self, oid):
        """
        Remove a faked NIC resource.

        This method also updates the 'nic-uris' property in the parent
        Partition resource, by removing the URI for the faked NIC resource.

        Parameters:

          oid (string):
            The object ID of the faked NIC resource.
        """
        nic = self.lookup_by_oid(oid)
        partition = self.parent
        devno = nic.properties.get('device-number', None)
        if devno:
            partition.devno_free_if_allocated(devno)
        assert 'nic-uris' in partition.properties
        nic_uris = partition.properties['nic-uris']
        nic_uris.remove(nic.uri)
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

    def __init__(self, hmc, cpc):
        super(FakedPartitionManager, self).__init__(
            hmc=hmc,
            parent=cpc,
            resource_class=FakedPartition,
            base_uri=self.api_root + '/partitions',
            oid_prop='object-id',
            uri_prop='object-uri')

    def add(self, properties):
        """
        Add a faked Partition resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.
            * 'hba-uris' will be auto-generated as an empty array, if not
              specified.
            * 'nic-uris' will be auto-generated as an empty array, if not
              specified.
            * 'virtual-function-uris' will be auto-generated as an empty array,
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedPartition`: The faked Partition
            resource.
        """
        return super(FakedPartitionManager, self).add(properties)


class FakedPartition(FakedBaseResource):
    """
    A faked Partition resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.

    Each partition uses the device number range of 0x8000 to 0xFFFF for
    automatically assigned device numbers of HBAs, NICs and virtual functions.
    Users of the mock support should not use device numbers in that range
    (unless all of them are user-assigned for a particular partition).
    """

    def __init__(self, manager, properties):
        super(FakedPartition, self).__init__(
            manager=manager,
            properties=properties)
        if 'hba-uris' not in self.properties:
            self.properties['hba-uris'] = []
        if 'nic-uris' not in self.properties:
            self.properties['nic-uris'] = []
        if 'virtual-function-uris' not in self.properties:
            self.properties['virtual-function-uris'] = []
        self._nics = FakedNicManager(hmc=manager.hmc, partition=self)
        self._hbas = FakedHbaManager(hmc=manager.hmc, partition=self)
        self._virtual_functions = FakedVirtualFunctionManager(
            hmc=manager.hmc, partition=self)
        self._devno_pool = IdPool(0x8000, 0xFFFF)

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

    def devno_alloc(self):
        """
        Allocates a device number unique to this partition, in the range of
        0x8000 to 0xFFFF.

        Returns:
          string: The device number as four hexadecimal digits in upper case.

        Raises:
          ValueError: No more device numbers available in that range.
        """
        devno_int = self._devno_pool.alloc()
        devno = "{:04X}".format(devno_int)
        return devno

    def devno_free(self, devno):
        """
        Free a device number allocated with :meth:`devno_alloc`.

        The device number must be allocated.

        Parameters:
          devno (string): The device number as four hexadecimal digits.

        Raises:
          ValueError: Device number not in pool range or not currently
            allocated.
        """
        devno_int = int(devno, 16)
        self._devno_pool.free(devno_int)

    def devno_free_if_allocated(self, devno):
        """
        Free a device number allocated with :meth:`devno_alloc`.

        If the device number is not currently allocated or not in the pool
        range, nothing happens.

        Parameters:
          devno (string): The device number as four hexadecimal digits.
        """
        devno_int = int(devno, 16)
        self._devno_pool.free_if_allocated(devno_int)


class FakedPortManager(FakedBaseManager):
    """
    A manager for faked Adapter Port resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, adapter):
        if adapter.adapter_kind == 'network':
            port_segment = 'network-ports'
        elif adapter.adapter_kind == 'storage':
            port_segment = 'storage-ports'
        else:
            raise ValueError("FakedAdapter with object-id=%s must be a "
                             "storage or network adapter to have ports." %
                             adapter.oid)
        super(FakedPortManager, self).__init__(
            hmc=hmc,
            parent=adapter,
            resource_class=FakedPort,
            base_uri=adapter.uri + '/' + port_segment,
            oid_prop='element-id',
            uri_prop='element-uri')

    def add(self, properties):
        """
        Add a faked Port resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.

            This method also updates the 'network-port-uris' or
            'storage-port-uris' property in the parent Adapter resource, by
            adding the URI for the faked Port resource.

        Returns:
          :class:`zhmcclient_mock.FakedPort`: The faked Port resource.
        """
        new_port = super(FakedPortManager, self).add(properties)
        adapter = self.parent
        if 'network-port-uris' in adapter.properties:
            adapter.properties['network-port-uris'].append(new_port.uri)
        if 'storage-port-uris' in adapter.properties:
            adapter.properties['storage-port-uris'].append(new_port.uri)
        return new_port

    def remove(self, oid):
        """
        Remove a faked Port resource.

        This method also updates the 'network-port-uris' or 'storage-port-uris'
        property in the parent Adapter resource, by removing the URI for the
        faked Port resource.

        Parameters:

          oid (string):
            The object ID of the faked Port resource.
        """
        port = self.lookup_by_oid(oid)
        adapter = self.parent
        if 'network-port-uris' in adapter.properties:
            port_uris = adapter.properties['network-port-uris']
            port_uris.remove(port.uri)
        if 'storage-port-uris' in adapter.properties:
            port_uris = adapter.properties['storage-port-uris']
            port_uris.remove(port.uri)
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

    def __init__(self, hmc, partition):
        super(FakedVirtualFunctionManager, self).__init__(
            hmc=hmc,
            parent=partition,
            resource_class=FakedVirtualFunction,
            base_uri=partition.uri + '/virtual-functions',
            oid_prop='element-id',
            uri_prop='element-uri')

    def add(self, properties):
        """
        Add a faked Virtual Function resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.
            * 'device-number' will be auto-generated with a unique value
              within the partition in the range 0x8000 to 0xFFFF, if not
              specified.

            This method also updates the 'virtual-function-uris' property in
            the parent Partition resource, by adding the URI for the faked
            Virtual Function resource.

        Returns:
          :class:`zhmcclient_mock.FakedVirtualFunction`: The faked Virtual
            Function resource.
        """
        new_vf = super(FakedVirtualFunctionManager, self).add(properties)
        partition = self.parent
        assert 'virtual-function-uris' in partition.properties
        partition.properties['virtual-function-uris'].append(new_vf.uri)
        if 'device-number' not in new_vf.properties:
            devno = partition.devno_alloc()
            new_vf.properties['device-number'] = devno
        return new_vf

    def remove(self, oid):
        """
        Remove a faked Virtual Function resource.

        This method also updates the 'virtual-function-uris' property in the
        parent Partition resource, by removing the URI for the faked Virtual
        Function resource.

        Parameters:

          oid (string):
            The object ID of the faked Virtual Function resource.
        """
        virtual_function = self.lookup_by_oid(oid)
        partition = self.parent
        devno = virtual_function.properties.get('device-number', None)
        if devno:
            partition.devno_free_if_allocated(devno)
        assert 'virtual-function-uris' in partition.properties
        vf_uris = partition.properties['virtual-function-uris']
        vf_uris.remove(virtual_function.uri)
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

    def __init__(self, hmc, cpc):
        super(FakedVirtualSwitchManager, self).__init__(
            hmc=hmc,
            parent=cpc,
            resource_class=FakedVirtualSwitch,
            base_uri=self.api_root + '/virtual-switches',
            oid_prop='object-id',
            uri_prop='object-uri')

    def add(self, properties):
        """
        Add a faked Virtual Switch resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedVirtualSwitch`: The faked Virtual
            Switch resource.
        """
        return super(FakedVirtualSwitchManager, self).add(properties)


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
