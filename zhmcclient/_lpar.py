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
A :term:`LPAR` (Logical Partition) is a subset of the hardware resources of a
:term:`CPC` in classic mode (or ensemble mode), virtualized as a separate
computer.

LPARs cannot be created or deleted by the user; they can only be listed.

LPAR resources are contained in CPC resources.

LPAR resources only exist in CPCs that are in classic mode (or ensemble mode).
CPCs in DPM mode have :term:`Partition` resources, instead.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import _log_call

__all__ = ['LparManager', 'Lpar']


class LparManager(BaseManager):
    """
    Manager providing access to the :term:`LPARs <LPAR>` in a particular
    :term:`CPC`.

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
        super(LparManager, self).__init__(Lpar, cpc)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: :term:`CPC` defining the scope for this
        manager.
        """
        return self._parent

    @_log_call
    def list(self, full_properties=False):
        """
        List the LPARs in this CPC.

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
        lpars_res = self.session.get(self.cpc.uri + '/logical-partitions')
        lpar_list = []
        if lpars_res:
            lpar_items = lpars_res['logical-partitions']
            for lpar_props in lpar_items:
                lpar = Lpar(self, lpar_props['object-uri'], lpar_props)
                if full_properties:
                    lpar.pull_full_properties()
                lpar_list.append(lpar)
        return lpar_list


class Lpar(BaseResource):
    """
    Representation of an :term:`LPAR`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.LparManager`).
    """

    def __init__(self, manager, uri, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.LparManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        if not isinstance(manager, LparManager):
            raise AssertionError("Lpar init: Expected manager type %s, "
                                 "got %s" %
                                 (LparManager, type(manager)))
        super(Lpar, self).__init__(manager, uri, properties,
                                   uri_prop='object-uri',
                                   name_prop='name')

    @_log_call
    def activate(self, wait_for_completion=True):
        """
        Activate (start) this LPAR, using the HMC operation "Activate Logical
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
        body = {}
        result = self.manager.session.post(
            self.uri + '/operations/activate', body,
            wait_for_completion=wait_for_completion)
        return result

    @_log_call
    def deactivate(self, wait_for_completion=True):
        """
        De-activate (stop) this LPAR, using the HMC operation "Deactivate
        Logical Partition".

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
        body = {'force': True}
        result = self.manager.session.post(
            self.uri + '/operations/deactivate', body,
            wait_for_completion=wait_for_completion)
        return result

    @_log_call
    def load(self, load_address, wait_for_completion=True):
        """
        Load (boot) this LPAR from a load address (boot device), using the HMC
        operation "Load Logical Partition".

        Parameters:

          load_address (:term:`string`): Device number of the boot device.

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
        body = {'load-address': load_address}
        result = self.manager.session.post(
            self.uri + '/operations/load', body,
            wait_for_completion=wait_for_completion)
        return result
