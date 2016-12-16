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
A :term:`Partition` is a subset of the hardware resources of a :term:`CPC`
in DPM mode, virtualized as a separate computer.

Partitions can be created and deleted dynamically, and their resources such
as CPU, memory or I/O devices can be configured dynamically.
You can create as many partition definitions as you want, but only a specific
number of partitions can be active at any given time.

TODO: How can a user find out what the maximum is, before it is reached?

Partition resources are contained in CPC resources.

Partition resources only exist in CPCs that are in DPM mode. CPCs in classic
mode (or ensemble mode) have :term:`LPAR` resources, instead.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource
from ._nic import NicManager
from ._hba import HbaManager
from ._virtual_function import VirtualFunctionManager
from ._logging import _log_call

__all__ = ['PartitionManager', 'Partition']


class PartitionManager(BaseManager):
    """
    Manager providing access to the :term:`Partitions <Partition>` in a
    particular :term:`CPC`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible as properties in higher level resources (in this case, the
    :class:`~zhmcclient.Cpc` object).
    """

    def __init__(self, cpc):
        # This function should not go into the docs.
        # Parameters:
        #   cpc (:class:`~zhmcclient.Cpc`):
        #     CPC defining the scope for this manager.
        super(PartitionManager, self).__init__(Partition, cpc)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: :term:`CPC` defining the scope for this
        manager.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the Partitions in this CPC.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          : A list of :class:`~zhmcclient.Partition` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        partitions_res = self.session.get(self.cpc.uri + '/partitions')
        partition_list = []
        if partitions_res:
            partition_items = partitions_res['partitions']
            for partition_props in partition_items:
                partition = Partition(self, partition_props['object-uri'],
                                      partition_props)
                if full_properties:
                    partition.pull_full_properties()
                partition_list.append(partition)
        return partition_list

    def create(self, properties):
        """
        Create and configure a Partition in this CPC.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Partition' in the :term:`HMC API` book.

        Returns:

          Partition:
            The resource object for the new Partition.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(self.cpc.uri + '/partitions',
                                   body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = properties.copy()
        props.update(result)
        return Partition(self, props['object-uri'], props)

    def partition_object(self, part_id):
        """
        Return a minimalistic :class:`~zhmcclient.Partition` object for a
        Partition in this CPC.

        This method is an internal helper function and is not normally called
        by users.

        This object will be connected in the Python object tree representing
        the resources (i.e. it has this CPC as a parent), and will have the
        following properties set:

          * `object-uri`
          * `object-id`
          * `parent`
          * `class`

        Parameters:

            part_id (string): `object-id` of the Partition

        Returns:

            :class:`~zhmcclient.Partition`: A Python object representing the
            Partition.
        """
        part_uri = "/api/partitions/" + part_id
        part_props = {
            'object-id': part_id,
            'parent': self.parent.uri,
            'class': 'partition',
        }
        return Partition(self, part_uri, part_props)


class Partition(BaseResource):
    """
    Representation of a :term:`Partition`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.PartitionManager`).
    """

    def __init__(self, manager, uri, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.PartitionManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        if not isinstance(manager, PartitionManager):
            raise AssertionError("Partition init: Expected manager type %s, "
                                 "got %s" %
                                 (PartitionManager, type(manager)))
        super(Partition, self).__init__(manager, uri, properties,
                                        uri_prop='object-uri',
                                        name_prop='name')
        # The manager objects for child resources (with lazy initialization):
        self._nics = None
        self._hbas = None
        self._virtual_functions = None

    @property
    @_log_call
    def nics(self):
        """
        :class:`~zhmcclient.NicManager`: Access to the :term:`NICs <NIC>` in
        this Partition.
        """
        # We do here some lazy loading.
        if not self._nics:
            self._nics = NicManager(self)
        return self._nics

    @property
    @_log_call
    def hbas(self):
        """
        :class:`~zhmcclient.HbaManager`: Access to the :term:`HBAs <HBA>` in
        this Partition.
        """
        # We do here some lazy loading.
        if not self._hbas:
            self._hbas = HbaManager(self)
        return self._hbas

    @property
    @_log_call
    def virtual_functions(self):
        """
        :class:`~zhmcclient.VirtualFunctionManager`: Access to the
        :term:`Virtual Functions <Virtual Function>` in this Partition.
        """
        # We do here some lazy loading.
        if not self._virtual_functions:
            self._virtual_functions = VirtualFunctionManager(self)
        return self._virtual_functions

    def start(self, wait_for_completion=True):
        """
        Start (activate) this Partition, using the HMC operation "Start
        Partition".

        TODO: Describe what happens if the maximum number of active partitions
        is exceeded.

        Parameters:

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

        Returns:

          :term:`json object`:

            If `wait_for_completion` is `True`, returns None.

            If `wait_for_completion` is `False`, returns a JSON object with a
            member named ``job-uri``. The value of ``job-uri`` identifies the
            job that was started, and can be used with the
            :meth:`~zhmcclient.Session.query_job_status` method to determine
            the status of the job and the result of the asynchronous HMC
            operation, once the job has completed.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.manager.session.post(
            self.uri + '/operations/start',
            wait_for_completion=wait_for_completion)
        return result

    def stop(self, wait_for_completion=True):
        """
        Stop (deactivate) this Partition, using the HMC operation "Stop
        Partition".

        Parameters:

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

        Returns:

          :term:`json object`:

            If `wait_for_completion` is `True`, returns None.

            If `wait_for_completion` is `False`, returns a JSON object with a
            member named ``job-uri``. The value of ``job-uri`` identifies the
            job that was started, and can be used with the
            :meth:`~zhmcclient.Session.query_job_status` method to determine
            the status of the job and the result of the asynchronous HMC
            operation, once the job has completed.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.manager.session.post(
            self.uri + '/operations/stop',
            wait_for_completion=wait_for_completion)
        return result

    def delete(self):
        """
        Delete this Partition.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self.uri)

    def update_properties(self, properties):
        """
        Update writeable properties of this Partition.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'Partition object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self.uri, body=properties)

    def dump_partition(self, parameters, wait_for_completion=True):
        """
        Dump this Partition, by loading a standalone dump program from a SCSI
        device and starting its execution, using the HMC operation
        'Dump Partition'.

        Parameters:

          parameters (dict): Input parameters for the operation.
            Allowable input parameters are defined in section
            'Request body contents' in section 'Dump Partition' in the
            :term:`HMC API` book.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

        Returns:

          :term:`json object`:

            If `wait_for_completion` is `True`, returns None.

            If `wait_for_completion` is `False`, returns a JSON object with a
            member named ``job-uri``. The value of ``job-uri`` identifies the
            job that was started, and can be used with the
            :meth:`~zhmcclient.Session.query_job_status` method to determine
            the status of the job and the result of the asynchronous HMC
            operation, once the job has completed.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.manager.session.post(
            self.uri + '/operations/scsi-dump',
            wait_for_completion=wait_for_completion, body=parameters)
        return result

    def psw_restart(self, wait_for_completion=True):
        """
        Initiates a PSW restart for this Partition, using the HMC operation
        'Perform PSW Restart'.

        Parameters:

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

        Returns:

          :term:`json object`:

            If `wait_for_completion` is `True`, returns None.

            If `wait_for_completion` is `False`, returns a JSON object with a
            member named ``job-uri``. The value of ``job-uri`` identifies the
            job that was started, and can be used with the
            :meth:`~zhmcclient.Session.query_job_status` method to determine
            the status of the job and the result of the asynchronous HMC
            operation, once the job has completed.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.manager.session.post(
            self.uri + '/operations/psw-restart',
            wait_for_completion=wait_for_completion)
        return result

    def mount_iso_image(self, properties):
        """
        Upload an ISO image and associate it to this Partition
        using the HMC operation 'Mount ISO Image'.

        When the partition already has an ISO image associated,
        the newly uploaded image replaces the current one.

        TODO: The interface of this method has issues, see issue #57.

        Parameters:

          properties (dict): Properties for the dump operation.
            See the section in the :term:`HMC API` about the specific HMC
            operation and about the 'Mount ISO Image' description of the
            members of the passed properties dict.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(
            self.uri + '/operations/mount-iso-image',
            wait_for_completion=True, body=properties)

    def unmount_iso_image(self):
        """
        Unmount the currently mounted ISO from this Partition using the HMC
        operation 'Unmount ISO Image'.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(
            self.uri + '/operations/unmount-iso-image')
