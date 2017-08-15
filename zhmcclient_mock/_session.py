# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
A faked Session class for the zhmcclient package.
"""

from __future__ import absolute_import

import zhmcclient

from ._hmc import FakedHmc
from ._urihandler import UriHandler, HTTPError, ConnectionError, URIS

__all__ = ['FakedSession']


class FakedSession(zhmcclient.Session):
    """
    A faked Session class for the zhmcclient package, that can be used as a
    replacement for the :class:`zhmcclient.Session` class.

    This class is derived from :class:`zhmcclient.Session`.

    This class can be used by projects using the zhmcclient package for their
    unit testing. It can also be used by unit tests of the zhmcclient package
    itself.

    This class provides a faked HMC with all of its resources that are relevant
    for the zhmcclient.

    The faked HMC provided by this class maintains its resource state in memory
    as Python objects, and no communication happens to any real HMC. The
    faked HMC implements all HMC operations that are relevant for the
    zhmcclient package in a successful manner.

    It is possible to populate the faked HMC with an initial resource state
    (see :meth:`~zhmcclient_mock.FakedHmc.add_resources`).
    """

    def __init__(self, host, hmc_name, hmc_version, api_version):
        """
        Parameters:

          host (:term:`string`):
            HMC host.

          hmc_name (:term:`string`):
            HMC name. Used for result of Query Version Info operation.

          hmc_version (:term:`string`):
            HMC version string (e.g. '2.13.1'). Used for result of
            Query Version Info operation.

          api_version (:term:`string`):
            HMC API version string (e.g. '1.8'). Used for result of
            Query Version Info operation.
        """
        super(FakedSession, self).__init__(host)
        self._hmc = FakedHmc(hmc_name, hmc_version, api_version)
        self._urihandler = UriHandler(URIS)

    def __repr__(self):
        """
        Return a string with the state of this faked session, for debug
        purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  _host = {s._host!r}\n"
            "  _userid = {s._userid!r}\n"
            "  _password = '...'\n"
            "  _get_password = {s._get_password!r}\n"
            "  _retry_timeout_config = {s._retry_timeout_config!r}\n"
            "  _base_url = {s._base_url!r}\n"
            "  _headers = {s._headers!r}\n"
            "  _session_id = {s._session_id!r}\n"
            "  _session = {s._session!r}\n"
            "  _hmc = {hmc_classname} at 0x{hmc_id:08x}\n"
            "  _urihandler = {s._urihandler!r}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                hmc_classname=self._hmc.__class__.__name__,
                hmc_id=id(self._hmc),
                s=self))
        return ret

    @property
    def hmc(self):
        """
        :class:`~zhmcclient_mock.FakedHmc`: The faked HMC provided by this
        faked session.

        The faked HMC supports being populated with initial resource state,
        for example using its :meth:`zhmcclient_mock.FakedHmc.add_resources`
        method.

        As an alternative to providing an entire resource tree, the resources
        can also be added one by one, from top to bottom, using the
        :meth:`zhmcclient_mock.FakedBaseManager.add` methods of the
        respective managers (the top-level manager for CPCs can be accessed
        via ``hmc.cpcs``).
        """
        return self._hmc

    def get(self, uri, logon_required=True):
        """
        Perform the HTTP GET method against the resource identified by a URI,
        on the faked HMC.

        Parameters:

          uri (:term:`string`):
            Relative URI path of the resource, e.g. "/api/session".
            This URI is relative to the base URL of the session (see
            the :attr:`~zhmcclient.Session.base_url` property).
            Must not be `None`.

          logon_required (bool):
            Boolean indicating whether the operation requires that the session
            is logged on to the HMC.

            Because this is a faked HMC, this does not perform a real logon,
            but it is still used to update the state in the faked HMC.

        Returns:

          :term:`json object` with the operation result.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError` (not implemented)
          :exc:`~zhmcclient.AuthError` (not implemented)
          :exc:`~zhmcclient.ConnectionError`
        """
        try:
            return self._urihandler.get(self._hmc, uri, logon_required)
        except HTTPError as exc:
            raise zhmcclient.HTTPError(exc.response())
        except ConnectionError as exc:
            raise zhmcclient.ConnectionError(exc.message, None)

    def post(self, uri, body=None, logon_required=True,
             wait_for_completion=True, operation_timeout=None):
        """
        Perform the HTTP POST method against the resource identified by a URI,
        using a provided request body, on the faked HMC.

        HMC operations using HTTP POST are either synchronous or asynchronous.
        Asynchronous operations return the URI of an asynchronously executing
        job that can be queried for status and result.

        Examples for synchronous operations:

        * With no response body: "Logon", "Update CPC Properties"
        * With a response body: "Create Partition"

        Examples for asynchronous operations:

        * With no ``job-results`` field in the completed job status response:
          "Start Partition"
        * With a ``job-results`` field in the completed job status response
          (under certain conditions): "Activate a Blade", or "Set CPC Power
          Save"

        The `wait_for_completion` parameter of this method can be used to deal
        with asynchronous HMC operations in a synchronous way.

        Parameters:

          uri (:term:`string`):
            Relative URI path of the resource, e.g. "/api/session".
            This URI is relative to the base URL of the session (see the
            :attr:`~zhmcclient.Session.base_url` property).
            Must not be `None`.

          body (:term:`json object`):
            JSON object to be used as the HTTP request body (payload).
            `None` means the same as an empty dictionary, namely that no HTTP
            body is included in the request.

          logon_required (bool):
            Boolean indicating whether the operation requires that the session
            is logged on to the HMC. For example, the "Logon" operation does
            not require that.

            Because this is a faked HMC, this does not perform a real logon,
            but it is still used to update the state in the faked HMC.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested HMC operation, as follows:

            * If `True`, this method will wait for completion of the requested
              operation, regardless of whether the operation is synchronous or
              asynchronous.

              This will cause an additional entry in the time statistics to be
              created for the asynchronous operation and waiting for its
              completion. This entry will have a URI that is the targeted URI,
              appended with "+completion".

            * If `False`, this method will immediately return the result of the
              HTTP POST method, regardless of whether the operation is
              synchronous or asynchronous.

          operation_timeout (:term:`number`):
            Timeout in seconds, when waiting for completion of an asynchronous
            operation. The special value 0 means that no timeout is set. `None`
            means that the default async operation timeout of the session is
            used.

            For `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised when the timeout
            expires.

            For `wait_for_completion=False`, this parameter has no effect.

        Returns:

          :term:`json object`:

            If `wait_for_completion` is `True`, returns a JSON object
            representing the response body of the synchronous operation, or the
            response body of the completed job that performed the asynchronous
            operation. If a synchronous operation has no response body, `None`
            is returned.

            If `wait_for_completion` is `False`, returns a JSON object
            representing the response body of the synchronous or asynchronous
            operation. In case of an asynchronous operation, the JSON object
            will have a member named ``job-uri``, whose value can be used with
            the :meth:`~zhmcclient.Session.query_job_status` method to
            determine the status of the job and the result of the original
            operation, once the job has completed.

            See the section in the :term:`HMC API` book about the specific HMC
            operation and about the 'Query Job Status' operation, for a
            description of the members of the returned JSON objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError` (not implemented)
          :exc:`~zhmcclient.AuthError` (not implemented)
          :exc:`~zhmcclient.ConnectionError`
        """
        try:
            return self._urihandler.post(self._hmc, uri, body, logon_required,
                                         wait_for_completion)
        except HTTPError as exc:
            raise zhmcclient.HTTPError(exc.response())
        except ConnectionError as exc:
            raise zhmcclient.ConnectionError(exc.message, None)

    def delete(self, uri, logon_required=True):
        """
        Perform the HTTP DELETE method against the resource identified by a
        URI, on the faked HMC.

        Parameters:

          uri (:term:`string`):
            Relative URI path of the resource, e.g.
            "/api/session/{session-id}".
            This URI is relative to the base URL of the session (see
            the :attr:`~zhmcclient.Session.base_url` property).
            Must not be `None`.

          logon_required (bool):
            Boolean indicating whether the operation requires that the session
            is logged on to the HMC. For example, for the logoff operation, it
            does not make sense to first log on.

            Because this is a faked HMC, this does not perform a real logon,
            but it is still used to update the state in the faked HMC.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError` (not implemented)
          :exc:`~zhmcclient.AuthError` (not implemented)
          :exc:`~zhmcclient.ConnectionError`
        """
        try:
            self._urihandler.delete(self._hmc, uri, logon_required)
        except HTTPError as exc:
            raise zhmcclient.HTTPError(exc.response())
        except ConnectionError as exc:
            raise zhmcclient.ConnectionError(exc.message, None)
