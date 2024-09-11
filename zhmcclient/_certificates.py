# Copyright 2016,2023 IBM Corp. All Rights Reserved.
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
A :term:`Certificate` represents an X.509 certificate.

Certificates are top level resources, but at this point, only certificates of
type "secure-boot" are supported. Such certificates are always associated to a
specific :term:`CPC`. They can only be used if the
:ref:`API feature <API features>` "secure-boot-with-certificates" is available
on both, :term:`HMC` and :term:`CPC`.

They can be assigned to one or more :term:`LPAR`, :term:`Partition`, or
:term:`Image Activation Profile` to be used during the load/start of the
corresponding entities when doing a "secure boot" load for an LPAR, respectively
a Partition start.
"""


import copy

from ._logging import logged_api_call
from ._manager import BaseManager
from ._resource import BaseResource
from ._utils import RC_CERTIFICATE

__all__ = ['CertificateManager', 'Certificate']


class CertificateManager(BaseManager):
    """
    Manager providing access to the :term:`Certificates <Certificate>` of an
    :term:`HMC`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable:

    * :attr:`~zhmcclient.Console.certificates` of a :class:`~zhmcclient.Console`
      object.

    HMC/SE version requirements:

    * :ref:`API feature <API features>` "secure-boot-with-certificates"
    """

    def __init__(self, console):
        # This function should not go into the docs.
        # Parameters:
        #   console (:class:`~zhmcclient.Console`):
        #     HMC defining the scope for this manager.

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        query_props = [
            'name', 'parent-name', 'type'
        ]

        super().__init__(
            resource_class=Certificate,
            class_name=RC_CERTIFICATE,
            session=console.manager.session,
            parent=console,
            base_uri='/api/certificates',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=query_props)

    @property
    def console(self):
        """
        :class:`~zhmcclient.Console`: The Console object representing the HMC.
        """
        return self._parent

    @logged_api_call
    # pylint: disable=arguments-differ
    def list(self, full_properties=False, filter_args=None,
             additional_properties=None):
        """
        List the certificates defined in the HMC.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "secure-boot-with-certificates"

        Authorization requirements:

        * Object-access permission to any Certificate to be included in the
          result.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

          additional_properties (list of string):
            List of property names that are to be returned in addition to the
            default properties.

        Returns:

          : A list of :class:`~zhmcclient.Certificate` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result_prop = 'certificates'
        list_uri = '/api/certificates'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args,
            additional_properties)

    @logged_api_call
    def import_certificate(self, cpc, properties):
        """
        Imports a certificate to a CPC.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "secure-boot-with-certificates"

        Authorization requirements:

        * Object-access permission to the given CPC.
        * Task permission for the "Import Secure Boot Certificates" task.

        Parameters:

          cpc (:class:`~zhmcclient.Cpc`): the CPC the certificate will be
          imported to.

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Import CPC Certificate' in the :term:`HMC API` book.

        Returns:

          :class:`~zhmcclient.Certificate`:
            The resource object for the new Certificate.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(
            cpc.uri + '/operations/import-certificate', body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        # import result uses a different key to identify the uri
        uri = props['certificate-uri']
        cert = Certificate(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return cert


class Certificate(BaseResource):
    """
    Representation of a :term:`Certificate`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.CertificateManager`).

    HMC/SE version requirements:

    * :ref:`API feature <API features>` "secure-boot-with-certificates"
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.CertificateManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, CertificateManager), (
            f"Certificate init: Expected manager type {CertificateManager}, "
            f"got {type(manager)}")
        super().__init__(manager, uri, name, properties)
        self._cpc = None

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: The :term:`CPC` to which this storage group
        is associated.

        The returned :class:`~zhmcclient.Cpc` has only a minimal set of
        properties populated.
        """
        # We do here some lazy loading.
        if not self._cpc:
            cpc_uri = self.get_property('parent')
            cpc_mgr = self.manager.console.manager.client.cpcs
            self._cpc = cpc_mgr.resource_object(cpc_uri)
        return self._cpc

    @logged_api_call
    def delete(self):
        """
        Delete this Certificate.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "secure-boot-with-certificates"

        Authorization requirements:

        * Object-access permission to this Certificate.
        * Task permission to the "Import Secure Boot Certificates" task.

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
    def update_properties(self, properties):
        """
        Update writeable properties of this Certificate.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "secure-boot-with-certificates"

        Authorization requirements:

        * Object-access permission to this Certificate.
        * Task permission to the "Certificate Details" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'Certificate object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.post(self.uri, resource=self, body=properties)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.update_properties_local(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)

    @logged_api_call
    def get_encoded(self):
        """
        Gets the Base64 encoded string and the file format of this certificate.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "secure-boot-with-certificates"

        Authorization requirements:

        * Object-access permission to this Certificate.

        Returns:

            dict: The encoded certificate in conjunction with its format:

            * key "certificate": The Base64 encoded string of the certificate.
            * key "format": The format of the certificate ("der" or "pem").

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        return self.manager.session.get(
            f'{self.uri}/operations/get-encoded', resource=self)

    def dump(self):
        """
        Dump this Certificate resource with its properties as a resource
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
