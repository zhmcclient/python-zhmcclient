# Copyright 2025 IBM Corp. All Rights Reserved.
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
The hardware messages that belong to the parent resource object (Console or
CPC).
"""


from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_HW_MESSAGE, make_query_str, timestamp_from_datetime


__all__ = ['HwMessageManager', 'HwMessage']


class HwMessageManager(BaseManager):
    """
    Manager providing access to the :term:`Hardware Messages <Hardware Message>`
    of the parent object (Console or CPC), that are exposed by the HMC this
    client is connected to.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    HMC/SE version requirements: None
    """

    def __init__(self, parent):
        # This function should not go into the docs.
        # Parameters:
        #   parent (:class:`~zhmcclient.BaseResource`):
        #      The parent object (Console or CPC).

        # Resource properties that are supported as filter query parameters
        # (for server-side filtering).
        query_props = []

        super().__init__(
            resource_class=HwMessage,
            class_name=RC_HW_MESSAGE,
            session=parent.manager.session,
            parent=parent,
            base_uri=f'{parent.uri}/hardware-messages',
            # Console: /api/console/hardware-messages/{hardware-message-id}
            # CPC: /api/cpcs/{cpc-id}/hardware-messages/{hardware-message-id}
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='element-id',
            query_props=query_props)

    @logged_api_call
    def list(
            self, full_properties=False, filter_args=None, begin_time=None,
            end_time=None):
        """
        List the hardware messages for the parent object (Console or CPC).

        HMC/SE version requirements: None

        Authorization requirements:

        * For hardware messages of the CPC: Object-access permission to the CPC.
        * Task permission to the "Hardware Messages" task at least in view-only
          mode.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

          filter_args (dict):
            Filter arguments that narrow the list of returned messages to those
            whose properties match the specified filter arguments. For details,
            see :ref:`Filtering`.

            `None` causes no such filtering to happen.

          begin_time (:class:`~py:datetime.datetime`):
            Filter that narrows the list of returned messages to those created
            on or after the specified point in time.
            The datetime object may be timezone-aware or timezone-naive. If
            timezone-naive, the UTC timezone is assumed.

            `None` causes no such filtering to happen.

          end_time (:class:`~py:datetime.datetime`):
            Filter that narrows the list of returned messages to those created
            on or before the specified point in time.
            The datetime object may be timezone-aware or timezone-naive. If
            timezone-naive, the UTC timezone is assumed.

            `None` causes no such filtering to happen.

        Returns:

          list: A list of :class:`~zhmcclient.HwMessage` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result_prop = 'hardware-messages'
        if filter_args and 'element-id' in filter_args:
            # Filter with filter-uri instead, because faster
            element_id = filter_args['element-id']
            element_uri = f'{self._base_uri}/{element_id}'
            filter_args = dict(filter_args)
            del filter_args['element-id']
            filter_args['element-uri'] = element_uri
        query_parms = []
        if begin_time is not None:
            begin_time = timestamp_from_datetime(begin_time)
            query_parms.append(f'begin-time={begin_time}')
        if end_time is not None:
            end_time = timestamp_from_datetime(end_time)
            query_parms.append(f'end-time={end_time}')
        msg_list = self._list_with_operation(
            self._base_uri, result_prop, full_properties,
            filter_args=filter_args, query_parms=query_parms)
        if not full_properties:
            # Add the element-id property since that is used as the 'name'.
            for msg in msg_list:
                element_id = msg.uri.split('/')[-1]
                msg.update_properties_local({'element-id': element_id})
        return msg_list


class HwMessage(BaseResource):
    """
    Representation of a :term:`Hardware Message`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from list functions on their manager object
    (in this case, :class:`~zhmcclient.HwMessageManager`).

    Note that HwMessage objects do not have any writeable properties, so they
    do not have an ``update_properties()`` method.

    HMC/SE version requirements: None
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.HwMessageManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, HwMessageManager), (
            f"HwMessage init: Expected manager type {HwMessageManager}, "
            f"got {type(manager)}")
        super().__init__(manager, uri, name, properties)

    def dump(self):
        """
        Dump this HwMessage resource with its properties as a resource
        definition.

        The returned resource definition has the following format::

            {
                # Resource properties:
                "properties": {...},
            }

        Returns:

          dict: Resource definition of this resource.
        """

        # Dump the resource properties
        resource_dict = super().dump()

        return resource_dict

    # Note: HwMessage resources cannot have their properties updated,
    #       hence there is no update_properties() method.

    @logged_api_call
    def delete(self):
        """
        Delete this hardware message.

        HMC/SE version requirements: None

        Authorization requirements:

        * For hardware messages of the CPC: Object-access permission to the CPC.
        * Task permission to the "Hardware Messages" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.delete(self.uri, resource=self)
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None))
        self.cease_existence_local()

    @logged_api_call
    def request_service(self, customer_name=None, customer_phone=None):
        """
        Request service from IBM for this hardware message and delete the
        hardware message.

        The hardware message's ``service-supported`` property must be True.

        HMC/SE version requirements: None

        Authorization requirements:

        * For hardware messages of the CPC: Object-access permission to the CPC.
        * Task permission to the "Hardware Messages" task.

        Parameters:

          customer_name (:term:`string`): Name of the person that can be
            contacted about the problem. Optional, default is the customer name
            registered with IBM for the machine.

          customer_phone (:term:`string`): Telephone number of the person that
            can be contacted about the problem. Optional, default is the
            customer telephone number registered with IBM for the machine.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {}
        if customer_name:
            body['customer-name'] = customer_name
        if customer_phone:
            body['customer-phone'] = customer_phone
        ops_uri = self.uri + '/operations/request-service'
        self.manager.session.post(ops_uri, resource=self, body=body)

    @logged_api_call
    def get_service_information(self, delete=False):
        """
        Get problem information and a telephone number for requesting service
        from IBM for this hardware message and optionally delete the hardware
        message.

        The hardware message's ``service-supported`` property must be True.

        HMC/SE version requirements: None

        Authorization requirements:

        * For hardware messages of the CPC: Object-access permission to the CPC.
        * Task permission to the "Hardware Messages" task.

        Parameters:

          delete (bool): Boolean indicating whether the hardware message should
            be deleted upon successful completion of the operation.

        Returns:

          dict: Response body of the "Get Console Service Request Information"
          or "Get CPC Service Request Information" operation, as described in
          the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        query_parms = [f'delete={delete}']
        query_str = make_query_str(query_parms)
        ops_uri = f'{self.uri}/operations/get-service-information{query_str}'
        result = self.manager.session.get(ops_uri, resource=self)
        return result

    @logged_api_call
    def decline_service(self):
        """
        Decline service from IBM for this hardware message and delete the
        hardware message.

        The hardware message's ``service-supported`` property must be True.

        HMC/SE version requirements: None

        Authorization requirements:

        * For hardware messages of the CPC: Object-access permission to the CPC.
        * Task permission to the "Hardware Messages" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        ops_uri = self.uri + '/operations/request-service'
        self.manager.session.post(ops_uri, resource=self)
