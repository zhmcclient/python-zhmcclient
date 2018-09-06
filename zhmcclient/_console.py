# Copyright 2017 IBM Corp. All Rights Reserved.
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
A :term:`Console` resource represents an HMC.

In a paired setup with primary and alternate HMC, each HMC is represented as
a separate :term:`Console` resource.
"""

from __future__ import absolute_import

import time

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import get_logger, logged_api_call
from ._utils import timestamp_from_datetime
from ._user import UserManager
from ._user_role import UserRoleManager
from ._user_pattern import UserPatternManager
from ._password_rule import PasswordRuleManager
from ._task import TaskManager
from ._ldap_server_definition import LdapServerDefinitionManager
from ._unmanaged_cpc import UnmanagedCpcManager


__all__ = ['ConsoleManager', 'Console']

LOG = get_logger(__name__)


class ConsoleManager(BaseManager):
    """
    Manager providing access to the :term:`Console` representing the HMC this
    client is connected to.

    In a paired setup with primary and alternate HMC, each HMC is represented
    as a separate :term:`Console` resource.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Client` object:

    * :attr:`zhmcclient.Client.consoles`
    """

    def __init__(self, client):
        # This function should not go into the docs.
        # Parameters:
        #   client (:class:`~zhmcclient.Client`):
        #      Client object for the HMC to be used.

        super(ConsoleManager, self).__init__(
            resource_class=Console,
            class_name='console',
            session=client.session,
            parent=None,
            base_uri='/api/console',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=None,
            list_has_name=False)
        self._client = client
        self._console = None

    @property
    def client(self):
        """
        :class:`~zhmcclient.Client`:
          The client defining the scope for this manager.
        """
        return self._client

    @property
    def console(self):
        """
        :class:`~zhmcclient.Console`:
          The :term:`Console` representing the HMC this client is connected to.

          The returned object is cached, so it is looked up only upon first
          access to this property.

          The returned object has only the following properties set:

          * 'object-uri'

          Use :meth:`~zhmcclient.BaseResource.get_property` or
          :meth:`~zhmcclient.BaseResource.prop` to access any properties
          regardless of whether they are already set or first need to be
          retrieved.
        """
        if self._console is None:
            self._console = self.list()[0]
        return self._console

    @logged_api_call
    def list(self, full_properties=True, filter_args=None):
        """
        List the (one) :term:`Console` representing the HMC this client is
        connected to.

        Authorization requirements:

        * None

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only a short set consisting of 'object-uri'.

          filter_args (dict):
            This parameter exists for consistency with other list() methods
            and will be ignored.

        Returns:

          : A list of :class:`~zhmcclient.Console` objects, containing the one
          :term:`Console` representing the HMC this client is connected to.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        uri = self._base_uri  # There is only one console object.
        if full_properties:
            props = self.session.get(uri)
        else:
            # Note: The Console resource's Object ID is not part of its URI.
            props = {
                self._uri_prop: uri,
            }
        resource_obj = self.resource_class(
            manager=self,
            uri=props[self._uri_prop],
            name=props.get(self._name_prop, None),
            properties=props)
        return [resource_obj]


class Console(BaseResource):
    """
    Representation of a :term:`Console`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.ConsoleManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.ConsoleManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, ConsoleManager), \
            "Console init: Expected manager type %s, got %s" % \
            (ConsoleManager, type(manager))
        super(Console, self).__init__(manager, uri, name, properties)

        # The manager objects for child resources (with lazy initialization):
        self._users = None
        self._user_roles = None
        self._user_patterns = None
        self._password_rules = None
        self._tasks = None
        self._ldap_server_definitions = None
        self._unmanaged_cpcs = None

    @property
    def users(self):
        """
        :class:`~zhmcclient.UserManager`: Access to the :term:`Users <User>` in
        this Console.
        """
        # We do here some lazy loading.
        if not self._users:
            self._users = UserManager(self)
        return self._users

    @property
    def user_roles(self):
        """
        :class:`~zhmcclient.UserRoleManager`: Access to the
        :term:`User Roles <User Role>` in this Console.
        """
        # We do here some lazy loading.
        if not self._user_roles:
            self._user_roles = UserRoleManager(self)
        return self._user_roles

    @property
    def user_patterns(self):
        """
        :class:`~zhmcclient.UserPatternManager`: Access to the
        :term:`User Patterns <User Pattern>` in this Console.
        """
        # We do here some lazy loading.
        if not self._user_patterns:
            self._user_patterns = UserPatternManager(self)
        return self._user_patterns

    @property
    def password_rules(self):
        """
        :class:`~zhmcclient.PasswordRuleManager`: Access to the
        :term:`Password Rules <Password Rule>` in this Console.
        """
        # We do here some lazy loading.
        if not self._password_rules:
            self._password_rules = PasswordRuleManager(self)
        return self._password_rules

    @property
    def tasks(self):
        """
        :class:`~zhmcclient.TaskManager`: Access to the :term:`Tasks <Task>` in
        this Console.
        """
        # We do here some lazy loading.
        if not self._tasks:
            self._tasks = TaskManager(self)
        return self._tasks

    @property
    def ldap_server_definitions(self):
        """
        :class:`~zhmcclient.LdapServerDefinitionManager`: Access to the
        :term:`LDAP Server Definitions <LDAP Server Definition>` in this
        Console.
        """
        # We do here some lazy loading.
        if not self._ldap_server_definitions:
            self._ldap_server_definitions = LdapServerDefinitionManager(self)
        return self._ldap_server_definitions

    @property
    def unmanaged_cpcs(self):
        """
        :class:`~zhmcclient.UnmanagedCpcManager`: Access to the unmanaged
        :term:`CPCs <CPC>` in this Console.
        """
        # We do here some lazy loading.
        if not self._unmanaged_cpcs:
            self._unmanaged_cpcs = UnmanagedCpcManager(self)
        return self._unmanaged_cpcs

    @logged_api_call
    def restart(self, force=False, wait_for_available=True,
                operation_timeout=None):
        """
        Restart the HMC represented by this Console object.

        Once the HMC is online again, this Console object, as well as any other
        resource objects accessed through this HMC, can continue to be used.
        An automatic re-logon will be performed under the covers, because the
        HMC restart invalidates the currently used HMC session.

        Authorization requirements:

        * Task permission for the "Shutdown/Restart" task.
        * "Remote Restart" must be enabled on the HMC.

        Parameters:

          force (bool):
            Boolean controlling whether the restart operation is processed when
            users are connected (`True`) or not (`False`). Users in this sense
            are local or remote GUI users. HMC WS API clients do not count as
            users for this purpose.

          wait_for_available (bool):
            Boolean controlling whether this method should wait for the HMC to
            become available again after the restart, as follows:

            * If `True`, this method will wait until the HMC has restarted and
              is available again. The
              :meth:`~zhmcclient.Client.query_api_version` method will be used
              to check for availability of the HMC.

            * If `False`, this method will return immediately once the HMC
              has accepted the request to be restarted.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for HMC availability after the
            restart. The special value 0 means that no timeout is set. `None`
            means that the default async operation timeout of the session is
            used. If the timeout expires when `wait_for_available=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for the HMC to become available again after the restart.
        """
        body = {'force': force}
        self.manager.session.post(self.uri + '/operations/restart', body=body)
        if wait_for_available:
            time.sleep(10)
            self.manager.client.wait_for_available(
                operation_timeout=operation_timeout)

    @logged_api_call
    def shutdown(self, force=False):
        """
        Shut down and power off the HMC represented by this Console object.

        While the HMC is powered off, any Python resource objects retrieved
        from this HMC may raise exceptions upon further use.

        In order to continue using Python resource objects retrieved from this
        HMC, the HMC needs to be started again (e.g. by powering it on
        locally). Once the HMC is available again, Python resource objects
        retrieved from that HMC can continue to be used.
        An automatic re-logon will be performed under the covers, because the
        HMC startup invalidates the currently used HMC session.

        Authorization requirements:

        * Task permission for the "Shutdown/Restart" task.
        * "Remote Shutdown" must be enabled on the HMC.

        Parameters:

          force (bool):
            Boolean controlling whether the shutdown operation is processed
            when users are connected (`True`) or not (`False`). Users in this
            sense are local or remote GUI users. HMC WS API clients do not
            count as users for this purpose.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'force': force}
        self.manager.session.post(self.uri + '/operations/shutdown', body=body)

    @logged_api_call
    def make_primary(self):
        """
        Change the role of the alternate HMC represented by this Console object
        to become the primary HMC.

        If that HMC is already the primary HMC, this method does not change its
        rols and succeeds.

        The HMC represented by this Console object must participate in a
        {primary, alternate} pairing.

        Authorization requirements:

        * Task permission for the "Manage Alternate HMC" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self.uri + '/operations/make-primary')

    @staticmethod
    def _time_query_parms(begin_time, end_time):
        """Return the URI query paramterer string for the specified begin time
        and end time."""
        query_parms = []
        if begin_time is not None:
            begin_ts = timestamp_from_datetime(begin_time)
            qp = 'begin-time={}'.format(begin_ts)
            query_parms.append(qp)
        if end_time is not None:
            end_ts = timestamp_from_datetime(end_time)
            qp = 'end-time={}'.format(end_ts)
            query_parms.append(qp)
        query_parms_str = '&'.join(query_parms)
        if query_parms_str:
            query_parms_str = '?' + query_parms_str
        return query_parms_str

    @logged_api_call
    def get_audit_log(self, begin_time=None, end_time=None):
        """
        Return the console audit log entries, optionally filtered by their
        creation time.

        Authorization requirements:

        * Task permission to the "Audit and Log Management" task.

        Parameters:

          begin_time (:class:`~py:datetime.datetime`):
            Begin time for filtering. Log entries with a creation time older
            than the begin time will be omitted from the results.

            If `None`, no such filtering is performed (and the oldest available
            log entries will be included).

          end_time (:class:`~py:datetime.datetime`):
            End time for filtering. Log entries with a creation time newer
            than the end time will be omitted from the results.

            If `None`, no such filtering is performed (and the newest available
            log entries will be included).

        Returns:

          :term:`json object`:
            A JSON object with the log entries, as described in section
            'Response body contents' of operation 'Get Console Audit Log' in
            the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        query_parms = self._time_query_parms(begin_time, end_time)
        uri = self.uri + '/operations/get-audit-log' + query_parms
        result = self.manager.session.post(uri)
        return result

    @logged_api_call
    def get_security_log(self, begin_time=None, end_time=None):
        """
        Return the console security log entries, optionally filtered by their
        creation time.

        Authorization requirements:

        * Task permission to the "View Security Logs" task.

        Parameters:

          begin_time (:class:`~py:datetime.datetime`):
            Begin time for filtering. Log entries with a creation time older
            than the begin time will be omitted from the results.

            If `None`, no such filtering is performed (and the oldest available
            log entries will be included).

          end_time (:class:`~py:datetime.datetime`):
            End time for filtering. Log entries with a creation time newer
            than the end time will be omitted from the results.

            If `None`, no such filtering is performed (and the newest available
            log entries will be included).

        Returns:

          :term:`json object`:
            A JSON object with the log entries, as described in section
            'Response body contents' of operation 'Get Console Security Log' in
            the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        query_parms = self._time_query_parms(begin_time, end_time)
        uri = self.uri + '/operations/get-security-log' + query_parms
        result = self.manager.session.post(uri)
        return result

    @logged_api_call
    def list_unmanaged_cpcs(self, name=None):
        """
        List the unmanaged CPCs of this HMC.

        For details, see :meth:`~zhmcclient.UnmanagedCpc.list`.

        Authorization requirements:

        * None

        Parameters:

          name (:term:`string`):
            Regular expression pattern for the CPC name, as a filter that
            narrows the list of returned CPCs to those whose name property
            matches the specified pattern.

            `None` causes no filtering to happen, i.e. all unmanaged CPCs
            discovered by the HMC are returned.

        Returns:

          : A list of :class:`~zhmcclient.UnmanagedCpc` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        filter_args = dict()
        if name is not None:
            filter_args['name'] = name
        cpcs = self.unmanaged_cpcs.list(filter_args=filter_args)
        return cpcs
