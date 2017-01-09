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
A fake Session class for the zhmcclient package.
"""

from __future__ import absolute_import

from zhmcclient import Session as ZhmcclientSession

from ._hmc import Hmc

__all__ = ['Session']


class Session(ZhmcclientSession):
    """
    A fake Session class for the zhmcclient package, that can be used as a
    replacement for the :class:`zhmcclient.Session` class.
    This class is derived from :class:`zhmcclient.Session`.

    This class can be used by projects using the zhmcclient package for their
    unit testing. It can also be used by unit tests of the zhmcclient package
    itself.

    This class provides faked HMC with all of its resources that are relevant
    for the zhmcclient.

    The faked HMC provided by this class maintains its resource state in memory
    as Python objects, and no communication happens to any real HMC. The
    faked HMC implements all HMC operations that are relevant for the
    zhmcclient package in a successful manner.

    It is possible to populate the faked HMC with an initial resource state
    (see :meth:`~zhmcclient_mock.Session.add_resources`).

    For testing error scenarios, or to simulate changes on the HMC resources
    that are performed through other channels than the zhmcclient, it is
    possible to override the default implementations of the operations against
    the faked HMC with operations that show specific user-defined behavior (see
    :meth:`~zhmcclient_mock.Session.add_operations`).
    """

    def __init__(self, host, api_version):
        """
        Parameters:

          host (:term:`string`):
            HMC host. For valid formats, see the
            :attr:`~zhmcclient.Session.host` property.

            May be `None`.

            This parameter is used only for descriptiove purposes. No
            communication will happen to that host.

          api_version (:term:`string`):
            Version string for the HMC API version (e.g. '2.13.1').
        """
        super(Session, self).__init__(host)
        self._hmc = Hmc(host, api_version)

    @property
    def hmc(self):
        """
        :class:`~zhmcclient_mock.Hmc`: The faked HMC provided by this session.

        This faked HMC supports being populated with initial resource state,
        for example using its :meth:`zhmcclient_mock.Hmc.add_resources` method,
        or the more fine grained methods such as
        :meth:`zhmcclient_mock.Hmc.add` and :meth:`zhmcclient_mock.Hmc.remove`
        (or the corresponding methods on its child resource classes).
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
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self._hmc.get(uri, logon_required)

    def post(self, uri, body=None, logon_required=True,
             wait_for_completion=True):
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
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self._hmc.post(uri, body, logon_required, wait_for_completion)

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
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self._hmc.delete(uri, logon_required)
