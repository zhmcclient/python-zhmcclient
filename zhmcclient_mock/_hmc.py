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
A faked (local, simulated, in-memory) HMC with all resources that are relevant
for the zhmcclient package.
"""

from __future__ import absolute_import

import os
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import six

# TODO: Move the resources into their own files.

__all__ = ['LocalResource', 'LocalResourceManager', 'Hmc', 'CpcManager',
           'Cpc', 'AdapterManager', 'Adapter', 'PortManager', 'Port']


class LocalResource(object):
    """
    A base class for local resources that are implemented in-memory and that
    act like resources in the HMC.
    """

    def __init__(self, manager, properties):
        self.manager = manager
        self.properties = properties

        if self.manager.oid_prop not in self.properties:
            new_oid = self.manager.new_oid()
            self.properties[self.manager.oid_prop] = new_oid
        self.oid = self.properties[self.manager.oid_prop]

        if self.manager.uri_prop not in self.properties:
            new_uri = os.path.join(self.manager.base_uri, self.oid)
            self.properties[self.manager.uri_prop] = new_uri
        self.uri = self.properties[self.manager.uri_prop]


class LocalResourceManager(object):
    """
    A base class for manager classes for
    :class:`zhmcclient_mock.LocalResource`, with similar responsibility as the
    zhmcclient manager classes.
    """

    next_oid = 1  # next object ID, for auto-generating them

    def __init__(self, parent, resource_class, base_uri, oid_prop, uri_prop):
        self.parent = parent
        self.resource_class = resource_class
        self.base_uri = base_uri
        self.oid_prop = oid_prop
        self.uri_prop = uri_prop
        self.resources = OrderedDict()  # Resource objects, by object ID

    def new_oid(self):
        new_oid = self.next_oid
        self.next_oid += 1
        return str(new_oid)

    def add(self, properties):
        """
        Add a resource to this manager.

        Parameters:

          properties (dict):
            Resource properties. If the URI property (e.g. 'object-uri') or the
            object ID property (e.g. 'object-id') are not specified, they
            will be auto-generated.

        Returns:
          LocalResource: The resource object.
        """
        resource = self.resource_class(self, properties)
        self.resources[resource.oid] = resource
        return resource

    def remove(self, oid):
        """
        Remove a resource from this manager.

        Parameters:

          oid (string):
            The object ID of the resource (e.g. value of the 'object-uri'
            property).
        """
        del self.resources[oid]

    def list(self):
        """
        List the resources of this manager.

        Returns:
          list of LocalResource: The resource objects of this manager.
        """
        return list(six.itervalues(self.resources))

    def lookup_by_oid(self, oid):
        """
        Look up a resource by its object ID.

        Parameters:

          oid (string):
            The object ID of the resource (e.g. value of the 'object-uri'
            property).

        Returns:
          LocalResource: The resource object.
        """
        del self.resources[oid]


class Hmc(LocalResource):
    """
    A local (faked) HMC.

    An object of this class represents a local, faked, in-memory HMC
    that can have all resources that are relevant for the zhmcclient.

    The Python API to this class and its child resource classes is not
    compatible with the zhmcclient API. Instead, these classes serve
    as an in-memory backend for a mocking layer for the zhmcclient package,
    that replaces access to a real HMC and directs that to the local, in-memory
    "HMC".

    Objects of this class should not be created by the user. Instead,
    access the :attr:`~zhmcclient_mock.Session.hmc` attribute of the
    fake session object (see :class:`~zhmcclient_mock.Session`).
    """

    def __init__(self, host, api_version):
        self.host = host
        self.api_version = api_version
        self.special_operations = {}  # user-provided operations
        self.cpcs = CpcManager(client=self)

    def add_resources(self, resources):
        """
        Add resources to the faked HMC, from the provided resource definitions.

        Duplicate resource names in the same scope are not permitted.

        Although this method is typically used to initially load the faked
        HMC with resource state just once, it can be invoked multiple times.

        Parameters:

          resources (dict):
            Definitions of resources to be added, see example below.

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

    def add_operations(self, operations):
        """
        Add operations with a specific, non-standard, behavior to the faked
        HMC, from operation definitions in an operation dictionary.

        Operations are matched by all of:
        * HTTP method (get, post, delete)
        * Canonical target URI (e.g. '/api/cpcs/1234')
        * Request body (as JSON object)

        Duplicate operation matches are not permitted.

        Although this method is typically used to initially load the faked
        HMC with operation behavior, it can be invoked multiple times.

        Parameters:

          operations (list):
            List of operation behavior definitions to be added, see example
            below.

        Example for 'operations' parameter::

            operations = [
                {
                    'method': 'get',           # used for matching the request
                    'uri': '/api/version',     # used for matching the request
                    'request_body': None,      # used for matching the request
                    'response_status': 200,    # desired HTTP status code
                    'response_body': {         # desired response body
                        'api-minor-version': '1'
                    }
                },
                {
                    'method': 'get',           # used for matching the request
                    'uri': '/api/cpcs',        # used for matching the request
                    'request_body': None,      # used for matching the request
                    'response_status': 400,    # desired HTTP status code
                    'response_error': {        # desired error info
                        'reason': 25,          # desired HMC reason code
                        'message': 'bla',      # desired HMC message text
                }
            ]
        """
        for _op, i in enumerate(operations):
            op = _op.copy()
            self._assert_op_key(i, op, 'method')
            op['method'] = op['method'].lower()
            self._assert_op_key(i, op, 'uri')
            if 'request_body' not in op:
                op['request_body'] = None
            self._assert_op_key(i, op, 'response_status')
            if 'response_body' not in op and 'response_error' not in op:
                raise ValueError("One of 'response_body' or 'response_error' "
                                 "is missing in operations item #{}".
                                 format(i))
            if 'response_body' in new_op and 'response_error' in op:
                raise ValueError("'response_body' and 'response_error' are "
                                 "both specified in operations item #{}".
                                 format(i))
            op_key = '{} {}'.format(op['method'], op['uri'])
            if op_key in self.special_operations:
                raise ValueError("Operaiton '{}' specified in operations "
                                 "item #{} was already defined.".
                                 format(i))
            self.special_operations[op_key] = op

    @staticmethod
    def _assert_op_key(i, op, key):
        if key not in op:
            raise ValueError("Missing '{}' key in operations item #{}".
                             format(key, i))

    def get(self, uri, logon_required):
        # TODO: Implement
        pass

    def post(self, uri, body, logon_required, wait_for_completion):
        # TODO: Implement
        pass

    def delete(self, uri, logon_required):
        # TODO: Implement
        pass


class CpcManager(LocalResourceManager):
    """
    A manager for CPC resources within a local HMC (see
    :class:`zhmcclient_mock.Hmc`).
    """

    def __init__(self, client):
        super(CpcManager, self).__init__(
            parent=client,
            resource_class=Cpc,
            base_uri='/api/cpcs/',
            oid_prop='object-id',
            uri_prop='object-uri')


class Cpc(LocalResource):
    """
    A CPC resource within a local HMC (see :class:`zhmcclient_mock.Hmc`).
    """

    def __init__(self, manager, properties):
        super(Cpc, self).__init__(
            manager=manager,
            properties=properties)
        self.adapters = AdapterManager(cpc=self)


class AdapterManager(LocalResourceManager):
    """
    A manager for Adapter resources within a local HMC (see
    :class:`zhmcclient_mock.Hmc`).
    """

    def __init__(self, cpc):
        super(AdapterManager, self).__init__(
            parent=cpc,
            resource_class=Adapter,
            base_uri=cpc.uri + '/adapters',
            oid_prop='object-id',
            uri_prop='object-uri')


class Adapter(LocalResource):
    """
    An Adapter resource within a local HMC (see :class:`zhmcclient_mock.Hmc`).
    """

    def __init__(self, manager, properties):
        super(Adapter, self).__init__(
            manager=manager,
            properties=properties)
        self.ports = PortManager(adapter=self)


class PortManager(LocalResourceManager):
    """
    A manager for Adapter Port resources within a local HMC (see
    :class:`zhmcclient_mock.Hmc`).
    """

    def __init__(self, adapter):
        super(PortManager, self).__init__(
            parent=adapter,
            resource_class=Port,
            base_uri=adapter.uri + '/ports',
            oid_prop='element-id',
            uri_prop='element-uri')

    def add(self, properties):
        """
        Add a Port resource to this manager.

        This method also updates the 'network-port-uris' or 'storage-port-uris'
        property in the parent Adapter resource (whichever exists, gets
        updated).

        Parameters:

          properties (dict):
            Resource properties. If the URI property ('element-uri') or the
            object ID property ('element-id') are not specified, they
            will be auto-generated.

        Returns:
          Port: The resource object.
        """
        adapter = self.parent
        if 'network-port-uris' in adapter.properties:
            adapter.properties['network-port-uris'].append(resource.uri)
        elif 'storage-port-uris' in adapter.properties:
            adapter.properties['storage-port-uris'].append(resource.uri)
        return super(PortManager, self).add(properties)

    def remove(self, oid):
        """
        Remove a Port resource from this manager.

        This method also updates the 'network-port-uris' or 'storage-port-uris'
        property in the parent Adapter resource (whichever exists, gets
        updated).

        Parameters:

          oid (string):
            The object ID of the Port resource.
        """
        resource = self.lookup_by_oid(oid)
        adapter = resource.parent
        if 'network-port-uris' in adapter.properties:
            del adapter.properties['network-port-uris'][resource.uri]
        elif 'storage-port-uris' in adapter.properties:
            del adapter.properties['storage-port-uris'][resource.uri]
        super(PortManager, self).remove(oid)  # last, because it deletes res


class Port(LocalResource):
    """
    An Adapter Port resource within a local HMC (see
    :class:`zhmcclient_mock.Hmc`).
    """

    def __init__(self, manager, properties):
        super(Port, self).__init__(
            manager=manager,
            properties=properties)
