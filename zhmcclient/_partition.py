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
A **partitions** is a subset of a physical z Systems computer or
LinuxONE system, certain aspects of which are virtualized and on which
Dynamic Partition Manager (DPM) is enabled. Partitions can be created
and deleted dynamically, and their resources such as CPU, memory or
I/O devices can be configured.
You can create as many partition definitions as you want,
but only a specific number of partitions can be active at any given time.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['PartitionManager', 'Partition']


class PartitionManager(BaseManager):
    """
    Manager object for Partitions. This manager object is scoped to the Partitions of a
    particular CPC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.
    """

    def __init__(self, cpc):
        """
        Parameters:

          cpc (:class:`~zhmcclient.Cpc`):
            CPC defining the scope for this manager object.
        """
        super(PartitionManager, self).__init__(cpc)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: Parent object (CPC) defining the scope for
        this manager object.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the Partitions in scope of this manager object.

        Returns:

          : A list of :class:`~zhmcclient.Lpar` objects.
        """
        cpc_uri = self.cpc.properties["object-uri"]
        partitions_res = self.session.get(cpc_uri + '/partitions')
        partition_list = []
        if partitions_res:
            partition_items = partitions_res['partitions']
            for partition_props in partition_items:
                partition = Partition(self, partition_props)
                if full_properties:
                    partition.pull_full_properties()
                partition_list.append(partition)
        return partition_list

    def create(self, partition_properties):
        """
        The Create Partition operation creates a partition with
        the given properties on the identified CPC.

        TODO: Review return value, and idea of immediately retrieving status.

        Parameters:

           partition_properties (:term:`dict`): Properties for partition.
        """
        pass


class Partition(BaseResource):
    """
    Representation of a Partition.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.
    """

    def __init__(self, manager, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.PartitionManager`):
            Manager object for this resource.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, PartitionManager)
        super(Partition, self).__init__(manager, properties)

    def start(self):
        """
        Start this Partition.

        TODO: Review return value, and idea of immediately retrieving status.
        """
        if self.properties["status"] in ["stopped", "paused"]:
            partition_object_uri = self.properties["object-uri"]
            body = {}
            result = self.manager.session.post(
                partition_object_uri + '/operations/start', body)
            return True
        else:
            return False

    def stop(self):
        """
        Stop this Partition.

        TODO: Review return value, and idea of immediately retrieving status.
        """
        if self.properties["status"] in ["active", "paused"]:
            partition_object_uri = self.properties["object-uri"]
            body = {}
            result = self.manager.session.post(
                partition_object_uri + '/operations/stop', body)
            return True
        else:
            return False

