# Copyright 2017,2021 IBM Corp. All Rights Reserved.
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
A :term:`Task` resource represents an action that an HMC user with appropriate
authority can perform. These actions could be available via the HMC's graphical
user interface, the Web Services APIs or both.

Tasks are predefined by the HMC and cannot be created, modified or deleted.
"""


from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_TASK

__all__ = ['TaskManager', 'Task']


class TaskManager(BaseManager):
    """
    Manager providing access to the :term:`Task` resources of a HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Console` object:

    * :attr:`zhmcclient.Console.tasks`

    HMC/SE version requirements:

    * HMC version >= 2.13.0
    """

    def __init__(self, console):
        # This function should not go into the docs.
        # Parameters:
        #   console (:class:`~zhmcclient.Console`):
        #      Console object representing the HMC.

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        query_props = [
            'name',
        ]

        super().__init__(
            resource_class=Task,
            class_name=RC_TASK,
            session=console.manager.session,
            parent=console,
            base_uri='/api/console/tasks',
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='name',
            query_props=query_props)

    @property
    def console(self):
        """
        :class:`~zhmcclient.Console`: :term:`Console` defining the scope for
        this manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=False, filter_args=None,
             additional_properties=None):
        """
        List the :term:`Task` resources representing the tasks defined in this
        HMC.

        The properties in the returned resource objects are by default those
        returned by the
        "List Tasks"
        HMC operation defined in the :term:`HMC API` book and can be expanded
        with the "full_properties" and "additional_properties" parameters of
        this method.

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        The listing of resources is handled by performing an HMC list operation
        in context of the parent resource, in an optimized way. For details,
        see :ref:`Listing resources`.

        HMC/SE version requirements:

        * HMC version >= 2.13.0

        Authorization requirements: None

        Parameters:

          full_properties (bool):
            If `True`, the set of properties in the returned resource objects
            will be expanded to the full set of readable properties defined in
            the data model for
            Task objects
            in the :term:`HMC API` book.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

          additional_properties (list of string):
            A list of property names.
            If specified, the set of properties in the returned resource objects
            will be expanded with the specified properties.
            `None` is treated the same as an empty list.

        Returns:

          : A list of :class:`~zhmcclient.Task` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
          :exc:`~zhmcclient.FilterPropertyNotFound`
        """
        result_prop = 'tasks'
        list_uri = f'{self.console.uri}/tasks'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args,
            additional_properties)


class Task(BaseResource):
    """
    Representation of a :term:`Task`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.TaskManager`).

    HMC/SE version requirements:

    * HMC version >= 2.13.0
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.TaskManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, TaskManager), (
            f"Console init: Expected manager type {TaskManager}, "
            f"got {type(manager)}")
        super().__init__(manager, uri, name, properties)
