# Copyright 2016,2021 IBM Corp. All Rights Reserved.
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
An :term:`Adapter` is a physical adapter card (e.g. OSA-Express adapter,
Crypto adapter) or a logical adapter (e.g. HiperSockets switch).

Adapter resources are contained in :term:`CPC` resources.

Adapter resources originally were supported only for CPCs in DPM mode. Since
z16, Adapter resources are in addition supported for CPCs in classic mode, but
in a quite limited fashion: The only HMC operations supported with classic mode
CPCs are "List Permitted Adapters" and "Update Adapter Firmware".

Each method description of adapter related zhmcclient classes details on which
types of CPCs it is supported.

A CPC in DPM mode automatically discovers the physical adapter cards that are
plugged into the system. A CPC in classic mode shows only the adapters that
have been defined in the active IOCDS.
"""


import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._port import PortManager
from ._logging import logged_api_call
from ._exceptions import CeasedExistence, ConsistencyError

from ._utils import repr_dict, repr_manager, repr_timestamp, matches_filters, \
    divide_filter_args, make_query_str, RC_ADAPTER, repr_obj_id

__all__ = ['AdapterManager', 'Adapter']


class AdapterManager(BaseManager):
    """
    Manager providing access to the :term:`Adapters <Adapter>` in a particular
    :term:`CPC`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Cpc` object:

    * :attr:`~zhmcclient.Cpc.adapters`

    HMC/SE version requirements:

    * SE version >= 2.13.1
    """

    def __init__(self, cpc):
        # This function should not go into the docs.
        # Parameters:
        #   cpc (:class:`~zhmcclient.Cpc`):
        #     CPC defining the scope for this manager.

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        query_props = [
            'name',

            # The adapter-id property is supported for filtering, but due to
            # a firmware defect, adapters with a hex digit in their adapter-id
            # property are not found. Disabling the property causes it to
            # be handled via client-side filtering, so that mitigates the
            # defect.
            # TODO: Re-enable the property once the defect is fixed and the fix
            # is rolled out broadly enough.
            # 'adapter-id',

            'adapter-family',
            'type',
            'status',
        ]

        super().__init__(
            resource_class=Adapter,
            class_name=RC_ADAPTER,
            session=cpc.manager.session,
            parent=cpc,
            base_uri='/api/adapters',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=query_props)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: :term:`CPC` defining the scope for this
        manager.
        """
        return self._parent

    @logged_api_call
    # pylint: disable=arguments-differ
    def list(self, full_properties=False, filter_args=None,
             additional_properties=None):
        """
        List the Adapters in this CPC.

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        The listing of resources is handled in an optimized way:

        * If this manager is enabled for :ref:`auto-updating`, a locally
          maintained resource list is used (which is automatically updated via
          inventory notifications from the HMC) and the provided filter
          arguments are applied.

        * Otherwise, if the filter arguments specify the resource name as a
          single filter argument with a straight match string (i.e. without
          regular expressions), an optimized lookup is performed based on a
          locally maintained name-URI cache.

        * Otherwise, the HMC List operation is performed with the subset of the
          provided filter arguments that can be handled on the HMC side and the
          remaining filter arguments are applied on the client side on the list
          result.

        HMC/SE version requirements:

        * SE version >= 2.13.1
        * The CPC must be in DPM mode.

        Authorization requirements:

        * Object-access permission to this CPC.
        * Object-access permission to any Adapter to be included in the result.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

          additional_properties (list of string):
            List of property names that are to be returned in addition to the
            default properties.

            This parameter requires HMC 2.16.0 or higher.

        Returns:

          : A list of :class:`~zhmcclient.Adapter` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
        """
        result_prop = 'adapters'
        list_uri = f'{self.cpc.uri}/adapters'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args,
            additional_properties)

    @logged_api_call
    def create_hipersocket(self, properties):
        """
        Create and configure a HiperSockets Adapter in this CPC.

        z17 CPCs removed the "Create Hipersocket" operation. This method uses
        the "Create Partition Link" operation when the API feature
        "dpm-hipersockets-partition-link-management" is enabled, and otherwise
        the earlier "Create Hipersocket" operation. As a result, this method
        supports all generations of CPCs.

        HMC/SE version requirements:

        * SE version >= 2.13.1
        * The CPC must be in DPM mode.

        Authorization requirements:

        * Object-access permission to the scoping CPC.
        * When the "dpm-hipersockets-partition-link-management" API feature is
          enabled, task permission to the "Create Partition Link" task;
          otherwise task permission to the "Create HiperSockets Adapter" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are the following:

            * "name" (str): Required: The adapter's 'name' property. When
              the Hipersocket adapter is created via a Partition Link, this
              also becomes the name of the Partition Link.

            * "description" (str): Optional: The adapter's 'description'
              property. Default: An empty string.

            * "maximum-transmission-unit-size" (int): Optional: The adapter's
              'maximum-transmission-unit-size' property. Default: 8

            * "port-description" (str): Optional: The adapter port's
              'description' property. Default: An empty string. This property
              is ignored on CPCs of z16 and later.

            These properties are defined in section 'Request body contents'
            in section 'Create Hipersocket' in the :term:`HMC API` book, but
            they are valid also when the Hipersocket adapter is created via
            a Partition Link.

        Returns:

          :class:`~zhmcclient.Adapter`:
            The resource object for the new HiperSockets Adapter.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc = self.cpc
        pl_feature = cpc.api_feature_enabled(
            "dpm-hipersockets-partition-link-management")
        if pl_feature:
            name = properties['name']
            console = cpc.manager.console
            part_link = console.partition_links.create({
                "name": name,
                "type": "hipersockets",
                "cpc-uri": cpc.uri,
            })
            props = {
                "name": name
            }
            description = properties.get("description")
            if description:
                props["description"] = description
            mtu_size = properties.get("maximum-transmission-unit-size")
            if mtu_size:
                props["maximum-transmission-unit-size"] = mtu_size
            # TODO: Use "port-description" to set port description
            uri = part_link.get_property('adapter-uri')
            adapter = Adapter(self, uri, name, props)
            adapter.update_properties(props)
        else:
            result = self.session.post(self.cpc.uri + '/adapters',
                                       body=properties)
            # There should not be overlaps, but just in case there are, the
            # returned props should overwrite the input props:
            props = copy.deepcopy(properties)
            props.update(result)
            name = props.get(self._name_prop, None)
            uri = props[self._uri_prop]
            adapter = Adapter(self, uri, name, props)

        self._name_uri_cache.update(name, uri)
        return adapter


class Adapter(BaseResource):
    """
    Representation of an :term:`Adapter`.

    Note that adapter objects do not correspond 1:1 with the physical adapter
    cards. Adapter objects do correspond 1:1 with PCHIDs, though.
    On classic mode CPCs, there are additional adapter objects that correspond
    1:1 with the VCHIDs of Network Express adapters.

    Some examples:

    * OSA Express cards with 2 ports have a single PCHID for the physical card
      and thus a single Adapter object.
    * Network Express cards with 2 ports have one PCHID for each port, and thus
      2 Adapter objects. On classic mode CPCs, each port has two additional
      VCHIDs for the 'osh' and 'neth' support of the adapter, so a 2-port card
      has 4 additional Adapter objects.
    * FICON Express cards with 2 ports have one PCHID for each port, and thus
      2 Adapter objects.
    * Crypto Express cards with 2 HSMs (= "ports") have one PCHID for each HSM,
      and thus 2 Adapter objects.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    For the properties of an Adapter, see section 'Data model' in section
    'Adapter object' in the :term:`HMC API` book.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.AdapterManager`).

    HMC/SE version requirements:

    * SE version >= 2.13.1
    """

    # Name of property for port URIs, dependent on adapter family
    port_uris_prop_by_family = {
        'ficon': 'storage-port-uris',
        'osa': 'network-port-uris',
        'roce': 'network-port-uris',
        'hipersockets': 'network-port-uris',
        'cna': 'network-port-uris',
        'cloud-network': 'network-port-uris',  # for preliminary driver
        'network-express': 'network-port-uris',
        'networking': 'network-port-uris',
    }

    # URI segment for port URIs, dependent on adapter family
    port_uri_segment_by_family = {
        'ficon': 'storage-ports',
        'osa': 'network-ports',
        'roce': 'network-ports',
        'hipersockets': 'network-ports',
        'cna': 'network-ports',
        'cloud-network': 'network-ports',  # for preliminary driver
        'network-express': 'network-ports',
        'networking': 'network-ports',
    }

    # Port type, dependent on adapter family
    port_type_by_family = {
        'ficon': 'storage',
        'osa': 'network',
        'roce': 'network',
        'hipersockets': 'network',
        'cna': 'network',
        'cloud-network': 'network',  # for preliminary driver
        'network-express': 'network',
        'networking': 'network',
    }

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.AdapterManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, AdapterManager), (
            f"Adapter init: Expected manager type {AdapterManager}, got "
            f"{type(manager)}")
        super().__init__(manager, uri, name, properties)
        # The manager objects for child resources (with lazy initialization):
        self._ports = None
        self._port_uris_prop = None
        self._port_uri_segment = None

    @property
    def ports(self):
        """
        :class:`~zhmcclient.PortManager`: Access to the :term:`Ports <Port>` of
        this Adapter.
        """
        # We do here some lazy loading.
        if not self._ports:
            family = self.get_property('adapter-family')
            try:
                port_type = self.port_type_by_family[family]
            except KeyError:
                port_type = None
            self._ports = PortManager(self, port_type)
        return self._ports

    @property
    def port_uris_prop(self):
        """
        :term:`string`: Name of adapter property that specifies the adapter
        port URIs, or the empty string ('') for adapters without ports.

        For example, 'network-port-uris' for a network adapter.
        """
        if self._port_uris_prop is None:
            family = self.get_property('adapter-family')
            try:
                self._port_uris_prop = self.port_uris_prop_by_family[family]
            except KeyError:
                self._port_uris_prop = ''
        return self._port_uris_prop

    @property
    def port_uri_segment(self):
        """
        :term:`string`: Adapter type specific URI segment for adapter port
        URIs, or the empty string ('') for adapters without ports.

        For example, 'network-ports' for a network adapter.
        """
        if self._port_uri_segment is None:
            family = self.get_property('adapter-family')
            try:
                self._port_uri_segment = self.port_uri_segment_by_family[
                    family]
            except KeyError:
                self._port_uri_segment = ''
        return self._port_uri_segment

    @property
    @logged_api_call
    def maximum_crypto_domains(self):
        """
        Integer: The maximum number of crypto domains on this crypto adapter.

        HMC/SE version requirements:

        * The parent CPC of the adapter must be in DPM mode.

        The maximum number of crypto domains on any crypto adapter (= HSM)
        is always equal to the maximum number of active partitions / LPARs
        on the CPC.

        For example, high-end systems support a maximum number of 85 crypto
        domains per HSM, and mid-range systems support a maximum number of 40
        crypto domains per HSM.

        If this adapter is not a crypto adapter, `None` is returned.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`ValueError`: Unknown crypto card type
        """
        if self.get_property('adapter-family') != 'crypto':
            return None
        card_type = self.get_property('detected-card-type')
        if card_type.startswith('crypto-express-'):
            max_domains = self.manager.cpc.maximum_active_partitions
        else:
            raise ValueError(f"Unknown crypto card type: {card_type!r}")
        return max_domains

    @logged_api_call
    def delete(self):
        """
        Delete this Hipersocket Adapter.

        The Adapter must be a HiperSockets Adapter and must not currently be
        the backing adapter of any partition NICs.

        z17 CPCs removed the "Delete Hipersocket" operation. This method uses
        the "Delete Partition Link" operation when the API feature
        "dpm-hipersockets-partition-link-management" is enabled, and otherwise
        the earlier "Delete Hipersocket" operation. As a result, this method
        supports all generations of CPCs.

        HMC/SE version requirements:

        * SE version >= 2.13.1
        * The parent CPC of the adapter must be in DPM mode.

        Authorization requirements:

        * Object-access permission to the HiperSockets Adapter to be deleted.
        * When the "dpm-hipersockets-partition-link-management" API feature is
          enabled, task permission to the "Delete Partition Link" task;
          otherwise task permission to the "Delete HiperSockets Adapter" task.

        Raises:

          :exc:`~zhmcclient.CeasedExistence`: The Partition Link for the
            adapter no longer exists (on CPCs of z16 and later)
          :exc:`~zhmcclient.ConsistencyError`: Found more than one Partition
            Link for the adapter (on CPCs of z16 and later)
          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc = self.manager.cpc
        pl_feature = cpc.api_feature_enabled(
            "dpm-hipersockets-partition-link-management")
        if pl_feature:
            console = cpc.manager.console
            filter_args = {"cpc-uri": cpc.uri}
            part_links = console.partition_links.list(
                filter_args=filter_args,
                additional_properties=['adapter-uri'],
            )
            part_links_for_adapter = []
            for part_link in part_links:
                if part_link.get_property('adapter-uri') == self.uri:
                    part_links_for_adapter.append(part_link)
            num_pl = len(part_links_for_adapter)
            # On z16 or later CPCs, the HMC ensures that Hipersocket Adapter
            # object and its Partition Link object always exist either both
            # or none, and that each HiperSocket Adapter can have only one
            # Partition Link.
            if num_pl == 0:
                # The Partition Link is gone, so the HS Adapter is also gone.
                self.cease_existence_local()
                raise CeasedExistence(self._uri)
            if num_pl > 1:
                # The HMC ensures that this does not happen, so if it happens
                # it is an inconsistency.
                pl_names = [pl.name for pl in part_links_for_adapter]
                raise ConsistencyError(
                    message=f"Found {num_pl} partition links "
                    f"({', '.join(pl_names)}) for adapter {self.name} on CPC "
                    f"{cpc.name} - please report this as a zhmcclient issue")
            part_link = part_links_for_adapter[0]
            part_link.delete()
            # That also deletes the Hipersocket adapter
        else:
            self.manager.session.delete(self.uri, resource=self)

        # pylint: disable=protected-access
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None))
        self.cease_existence_local()

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this Adapter.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * SE version >= 2.13.1
        * The parent CPC of the adapter must be in DPM mode.

        Authorization requirements:

        * Object-access permission to the Adapter.
        * Task permission for the "Adapter Details" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'Adapter object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.post(self.uri, resource=self, body=properties)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.update_properties_local(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)

    def __repr__(self):
        """
        Return a string with the state of this Adapter, for debug purposes.
        """
        ret = (
            f"{repr_obj_id(self)} (\n"
            f"  _manager={repr_obj_id(self._manager)},\n"
            f"  _uri={self._uri!r},\n"
            f"  _full_properties={self._full_properties!r},\n"
            "  _properties_timestamp="
            f"{repr_timestamp(self._properties_timestamp)},\n"
            f"  _properties={repr_dict(self._properties, indent=4)},\n"
            f"  _ports(lazy)={repr_manager(self._ports, indent=2)}\n"
            ")")
        return ret

    @logged_api_call
    def change_crypto_type(self, crypto_type, zeroize=None):
        """
        Reconfigures a cryptographic adapter to a different crypto type.
        This operation is only supported for cryptographic adapters.

        The cryptographic adapter must be varied offline before its crypto
        type can be reconfigured.

        HMC/SE version requirements:

        * SE version >= 2.13.1
        * The parent CPC of the adapter must be in DPM mode.

        Authorization requirements:

        * Object-access permission to this Adapter.
        * Task permission to the "Adapter Details" task.

        Parameters:

          crypto_type (:term:`string`):
            - ``"accelerator"``: Crypto Express5S Accelerator
            - ``"cca-coprocessor"``: Crypto Express5S CCA Coprocessor
            - ``"ep11-coprocessor"``: Crypto Express5S EP11 Coprocessor

          zeroize (bool):
            Specifies whether the cryptographic adapter will be zeroized when
            it is reconfigured to a crypto type of ``"accelerator"``.
            `None` means that the HMC-implemented default of `True` will be
            used.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'crypto-type': crypto_type}
        if zeroize is not None:
            body['zeroize'] = zeroize
        self.manager.session.post(
            self.uri + '/operations/change-crypto-type', resource=self,
            body=body)

    @logged_api_call
    def change_adapter_type(self, adapter_type):
        """
        Reconfigures an adapter from one type to another, or to ungonfigured.
        Currently, only storage adapters can be reconfigured, and their adapter
        type is the supported storage protocol (FCP vs. FICON).

        Storage adapter instances (i.e. :class:`~zhmcclient.Adapter` objects)
        represent daughter cards on a physical storage card. Current storage
        cards require both daughter cards to be configured to the same
        protocol, so changing the type of the targeted adapter will also change
        the type of the adapter instance that represents the other daughter
        card on the same physical card. Zhmcclient users that need to determine
        the related adapter instance can do so by finding the storage adapter
        with a matching first 9 characters (card ID and slot ID) of their
        `card-location` property values.

        The targeted adapter and its related adapter on the same storage card
        must not already have the desired adapter type, they must not be
        attached to any partition, and they must not have an adapter status
        of 'exceptions'.

        HMC/SE version requirements:

        * SE version >= 2.13.1
        * The parent CPC of the adapter must be in DPM mode.

        Authorization requirements:

        * Object-access permission to this Adapter.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          adapter_type (:term:`string`):
            - ``"fcp"``: FCP (Fibre Channel Protocol)
            - ``"fc"``: FICON (Fibre Connection) protocol
            - ``"not-configured"``: No adapter type configured

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'type': adapter_type}
        self.manager.session.post(
            self.uri + '/operations/change-adapter-type', resource=self,
            body=body)

    def dump(self):
        """
        Dump this Adapter resource with its properties and child resources
        (recursively) as a resource definition.

        The returned resource definition has the following format::

            {
                # Resource properties:
                "properties": {...},

                # Child resources:
                "ports": [...],
            }

        Returns:

          dict: Resource definition of this resource.
        """

        # Dump the resource properties
        resource_dict = super().dump()

        # Dump the child resources
        ports = self.ports.dump()
        if ports:
            resource_dict['ports'] = ports

        return resource_dict

    @logged_api_call
    def list_assigned_partitions(self, full_properties=False, filter_args=None):
        """
        List the partitions assigned to this adapter.

        This method is not supported for OSA adapters configured as OSM
        (because those cannot be assigned to partitions).

        HMC/SE version requirements:

        * SE version >= 2.13.1
        * The parent CPC of the adapter must be in DPM mode.

        Authorization requirements:

        * Object-access permission to this Adapter.

        Parameters:

          full_properties (bool):
            Controls whether the full set of partition properties should be
            retrieved, vs. only a short set (uri, name, status).

          filter_args (dict):
            Filter arguments that narrow the list of returned partitions to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all assigned partitions
            are returned.

        Returns:

          : A list of :class:`~zhmcclient.Partition` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        query_props = ['name', 'status']
        query_parms, client_filters = divide_filter_args(
            query_props, filter_args)
        query_parms_str = make_query_str(query_parms)
        uri = (f'{self.uri}/operations/get-partitions-assigned-to-adapter'
               f'{query_parms_str}')

        result = self.manager.session.get(uri, resource=self)

        partition_mgr = self.manager.parent.partitions
        resource_obj_list = []
        for props in result['partitions-assigned-to-adapter']:

            # pylint: disable=protected-access
            resource_obj = partition_mgr.resource_class(
                manager=partition_mgr,
                uri=props[partition_mgr._uri_prop],
                name=props.get(partition_mgr._name_prop, None),
                properties=props)

            if matches_filters(resource_obj, client_filters):
                resource_obj_list.append(resource_obj)
                if full_properties:
                    resource_obj.pull_full_properties()

        return resource_obj_list

    @logged_api_call
    def list_sibling_adapters(self, full_properties=False):
        """
        List the other Adapters on the same adapter card as this Adapter.

        Some adapter cards are represented as multiple Adapter objects
        (for example, 2-port FICON Express cards, or 2-port CNA cards).
        This method lists the other Adapter objects that are on the same
        adapter card as this Adapter object.

        This is useful for example to determine the affected Adapter objects
        when replacing the adapter card, or when changing the type of a FICON
        Express adepter (see :meth:`~zhmcclient.Adapter.change_adapter_type`).

        HMC/SE version requirements:

        * SE version >= 2.13.1
        * The parent CPC of the adapter must be in DPM mode.

        Authorization requirements:

        * Object-access permission to this CPC.
        * Object-access permission to any Adapter to be included in the result.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          : A list of :class:`~zhmcclient.Adapter` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # This algorithm is based on the fact that physical adapter cards
        # have their PCHIDs always within a range of 4 adjacent PCHIDs that
        # start at a multiple of 4.

        self_pchid = int(self.prop('adapter-id'), 16)
        if self_pchid >= int('7c0', 16):
            # A virtual adapter with a single PCHID -> no siblings
            return []

        # A physical adapter with a total of 4 PCHIDs reserved for the slot
        pchid_base = self_pchid // 4 * 4
        sibling_pchids = list(range(pchid_base, pchid_base + 4))
        sibling_pchids.remove(self_pchid)
        sibling_adapter_ids = [f'{p:03x}' for p in sibling_pchids]
        filter_args = {'adapter-id': sibling_adapter_ids}
        sibling_adapters = self.manager.cpc.adapters.list(
            full_properties, filter_args)
        return sibling_adapters
