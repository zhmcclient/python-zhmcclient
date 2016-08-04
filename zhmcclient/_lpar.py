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
A **Logical Partition (LPAR)** is a subset of a physical z Systems or LinuxONE
computer that is not in DPM mode (Dynamic Partition Manager mode).
Objects of this class are not provided when the CPC is in DPM mode.

An LPAR is always contained in a CPC.

LPARs cannot be created or deleted by the user; they can only be listed.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['LparManager', 'Lpar']


class LparManager(BaseManager):
    """
    Manager object for LPARs. This manager object is scoped to the LPARs of a
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
        super(LparManager, self).__init__(cpc)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: Parent object (CPC) defining the scope for
        this manager object.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the LPARs in scope of this manager object.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          : A list of :class:`~zhmcclient.Lpar` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc_uri = self.cpc.get_property('object-uri')
        lpars_res = self.session.get(cpc_uri + '/logical-partitions')
        lpar_list = []
        if lpars_res:
            lpar_items = lpars_res['logical-partitions']
            for lpar_props in lpar_items:
                lpar = Lpar(self, lpar_props)
                if full_properties:
                    lpar.pull_full_properties()
                lpar_list.append(lpar)
        return lpar_list


class Lpar(BaseResource):
    """
    Representation of an LPAR.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.
    """

    def __init__(self, manager, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.LparManager`):
            Manager object for this resource.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, LparManager)
        super(Lpar, self).__init__(manager, properties)

    def activate(self, wait_for_completion=True):
        """
        Activate (start) this LPAR.

        Parameters:

          wait_for_completion (bool):
            Boolean indicating whether the method should wait until
            the operation/job has completed.
            If wait_for_completion is 'False' the status of the operation/job
            has to be retrieved via the method 'query_job_status' method.

        Returns:

          :term:`json object` with the operation result.

            In the default case of a synchronous operation
            (wait_for_completion=True) the return value is a JSON object with
            members like status, job-status-code and job-reason-code.
            See the respective sections in :term:`HMC API` for a description
            of the response body contents of the Query Job Status operation.

            In case of an asynchronous operation (wait_for_completion=False),
            the return value is a JSON object with a member job-id whose value
            needs to be used for query_job_status().

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        lpar_uri = self.get_property('object-uri')
        result = self.manager.session.post(lpar_uri + '/operations/activate',
            wait_for_completion=wait_for_completion)
        return result

    def deactivate(self, wait_for_completion=True):
        """
        De-activate (stop) this LPAR.

        Parameters:

          wait_for_completion (bool):
            Boolean indicating whether the method should wait until
            the operation/job has completed.
            If wait_for_completion is 'False' the status of the operation/job
            has to be retrieved via the method 'query_job_status' method.

        Returns:

          :term:`json object` with the operation result.

            In the default case of a synchronous operation
            (wait_for_completion=True) the return value is a JSON object with
            members like status, job-status-code and job-reason-code.
            See the respective sections in :term:`HMC API` for a description
            of the response body contents of the Query Job Status operation.

            In case of an asynchronous operation (wait_for_completion=False),
            the return value is a JSON object with a member job-id whose value
            needs to be used for query_job_status().

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        lpar_uri = self.get_property('object-uri')
        body = {'force': True}
        result = self.manager.session.post(lpar_uri + '/operations/deactivate',
            body, wait_for_completion=wait_for_completion)
        return result

    def load(self, load_address, wait_for_completion=True):
        """
        Load (boot) this LPAR from a load address (boot device).

        Parameters:

          load_address (:term:`string`): Device number of the boot device.

          wait_for_completion (bool):
            Boolean indicating whether the method should wait until
            the operation/job has completed.
            If wait_for_completion is 'False' the status of the operation/job
            has to be retrieved via the method 'query_job_status' method.

        Returns:

          :term:`json object` with the operation result.

            In the default case of a synchronous operation
            (wait_for_completion=True) the return value is a JSON object with
            members like status, job-status-code and job-reason-code.
            See the respective sections in :term:`HMC API` for a description
            of the response body contents of the Query Job Status operation.

            In case of an asynchronous operation (wait_for_completion=False),
            the return value is a JSON object with a member job-id whose value
            needs to be used for query_job_status().

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        lpar_uri = self.get_property('object-uri')
        body = {'load-address': load_address}
        result = self.manager.session.post(lpar_uri + '/operations/load',
            body, wait_for_completion=wait_for_completion)
        return result
