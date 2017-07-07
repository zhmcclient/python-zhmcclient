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
The HMC supports the retrieval of metrics values for resources of a z Systems
or LinuxONE computer. This section describes the zhmcclient API for retrieving
such metrics from the HMC.

A resource termed :term:`Metrics Context` is associated with any metrics
retrieval. These resources are user-created definitions of the kinds of metrics
that are intended to be retrieved. A metrics context mostly defines the names
of the metric groups to be retrieved. The available metric groups are described
in section 'Metric Groups' in the :term:`HMC API` book.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import get_logger, logged_api_call
from ._exceptions import NotFound

__all__ = ['MetricsContextManager', 'MetricsContext', 'Metrics',
           'CollectedMetrics']

LOG = get_logger(__name__)


class MetricsContextManager(BaseManager):
    """
    Manager providing access to the :term:`Metrics Context` resources that
    were created through this manager object.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the :attr:`~zhmcclient.Client.metrics_contexts` attribute
    of the :class:`~zhmcclient.Client` object connected to the HMC.
    """

    def __init__(self, client):
        # This function should not go into the docs.
        # Parameters:
        #   client (:class:`~zhmcclient.Client`):
        #      Client object for the HMC to be used.

        super(MetricsContextManager, self).__init__(
            resource_class=MetricsContext,
            session=client.session,
            parent=None,
            base_uri='/api/services/metrics/context',
            oid_prop='',
            uri_prop='',
            name_prop='',
            query_props=[])

        self._client = client
        self._metrics_contexts = []

    @logged_api_call
    def list(self, full_properties=False):
        """
        List the :term:`Metrics Context` resources that were created through
        this manager object.

        Note that the HMC does not provide a way to enumerate the existing
        :term:`Metrics Context` resources. Therefore, this method will only
        list the :term:`Metrics Context` resources that were created through
        this manager object. For example, :term:`Metrics Context` resources
        created through a second :class:`~zhmcclient.Client` object will not be
        listed.

        Parameters:

          full_properties (bool):
            This parameter exists for compatibility with other resource
            classes, but for this class, it has no effect on the result.

        Returns:

          : A list of :class:`~zhmcclient.MetricsContext` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        return self._metrics_contexts

    def create(self, properties):
        """
        Create a :term:`Metrics Context` resource in the HMC this client is
        connected to.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Metrics Context' in the :term:`HMC API` book.

            TODO: Turn the specific (two) properties into method parameters?

        Returns:

          :class:`~zhmcclient.MetricsContext`:
            The resource object for the new :term:`Metrics Context` resource.

            TODO: What about the metrics info structure that is also returned
            by the HMC?

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post('/api/services/metrics/context',
                                   body=properties)
        new_metrics_context = MetricsContext(self,
                                             result['metrics-context-uri'],
                                             None,
                                             result)
        self._metrics_contexts.append(new_metrics_context)
        return new_metrics_context

    @property
    def client(self):
        """
        :class:`~zhmcclient.Client`:
          The client defining the scope for this manager.
        """
        return self._client


class MetricsContext(BaseResource):
    """
    Representation of a :term:`Metrics Context` resource.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class can be created by the user with the
    :meth:`zhmcclient.MetricsContextManager.create` method.
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.MetricsContextManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        if not isinstance(manager, MetricsContextManager):
            raise AssertionError(
                "MetricsContext init: Expected manager type %s, got %s" %
                (MetricsContextManager, type(manager)))
        super(MetricsContext, self).__init__(manager, uri, name, properties)

    @logged_api_call
    def get_metrics(self):
        """
        Retrieve the metrics data for this :term:`Metrics Context` resource.

        Returns:

          :term:`string` in MetricsResponse format:
            The metrics response, in the `MetricsResponse` format described in
            section 'Response body contents' in section 'Get Metrics' in the
            :term:`HMC API` book.

            TODO: Change return value to a list of MetricsGroup objects?

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.manager.session.get(self.uri)
        return result

    def delete(self):
        """
        Delete this :term:`Metrics Context` resource.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self.uri)
        self.manager._metrics_contexts.remove(self)


class CollectedMetrics(object):
    """
    TODO: Describe this class.
    """

    def __init__(self, metrics_context, rawdata):
        """
        TODO: Describe this method.
        """
        self._metrics_context = metrics_context
        self._client = self._metrics_context.manager.client
        self._rawdata = rawdata
        self._metrics_groups = None
        self._metrics = None

        metric_groups = dict()
        metric_group_infos = metrics_context.properties['metric-group-infos']
        for metric_group_info in metric_group_infos:
            metric_infos = metric_group_info['metric-infos']
            metric_names = list()
            for metric_info in metric_infos:
                metric_names.append(metric_info['metric-name'])
            metric_groups[metric_group_info['group-name']] = metric_names
        self._metrics_groups = metric_groups

    @property
    def metrics(self):
        """
        TODO: Describe this method.
        """
        if self._metrics:
            return self._metrics
        else:
            metrics_list = list()
            metrics_group = None
            uri = None
            epoch_timestamp = None
#    print(metric_groups.keys())
            state = 0
            for rawdata_line in self._rawdata.splitlines():
                if state == 0:
                    if rawdata_line.replace('"', '') in \
                            self._metrics_groups.keys():
                        metrics_group = rawdata_line.replace('"', '')
                        state = 1
                elif state == 1:
                    if not rawdata_line:
                        state = 0
                    else:
                        uri = rawdata_line.replace('"', '')
#                print(uri)
                        state = 2
                elif state == 2:
                    epoch_timestamp = rawdata_line
#            print(time.strftime("%a, %d %b %Y %H:%M:%S +0000",
#                 time.localtime(float(epoch_timestamp[:-3]))))
                    state = 3
                elif state == 3:
                    metrics_values = rawdata_line.split(',')
                    metrics = dict(zip(self._metrics_groups[metrics_group],
                                       metrics_values))
                    m = Metrics(self._client, metrics_group, uri,
                                epoch_timestamp, metrics)
                    metrics_list.append(m)
                    state = 4
                elif state == 4:
                    if not rawdata_line:
                        state = 1
                    else:
                        metrics_values = rawdata_line.split(',')
                        metrics = dict(zip(self._metrics_groups[metrics_group],
                                           metrics_values))
                        m = Metrics(self._client, metrics_group, uri,
                                    epoch_timestamp, metrics)
                        metrics_list.append(m)
                        state = 4
            self._metrics = metrics_list
            return self._metrics


class Metrics(object):
    """
    TODO: Describe this class.
    """

    def __init__(self, client, metrics_group, uri, timestamp, metrics):
        """
        TODO: Describe this method.
        """
        self._client = client
        self._metrics_group = metrics_group
        self._uri = uri
        self._timestamp = timestamp
        self._metrics = metrics

    @property
    def properties(self):
        """
        TODO: Describe this property.
        """
        return self._metrics

    @property
    def uri(self):
        """
        string: The canonical URI path of the resource. Will not be `None`.

        Example: ``/api/cpcs/12345``
        """
        return self._uri

    @property
    def metrics_group(self):
        """
        TODO: Describe this property.
        """
        return self._metrics_group

    @property
    def timestamp(self):
        """
        TODO: Describe this property.
        """
        return self._timestamp

    @logged_api_call
    def get_property(self, name):
        """
        TODO: Describe this method.
        """
        return self._metrics[name]

    @logged_api_call
    def prop(self, name, default=None):
        """
        TODO: Describe this method.
        """
        return self._metrics[name]

    @property
    def managed_object(self):
        """
        TODO: Describe this property.
        """
        metrics_group_to_managed_object = {
            'channel-usage': 'cpc',
            'cpc-usage-overview': 'cpc',
            'dpm-system-usage-overview': 'cpc',
            'logical-partition-usage': 'logical-partition',
            'partition-usage': 'partition',
            'zcpc-environmentals-and-power': 'cpc',
            'zcpc-processor-usage': 'cpc',
            'crypto-usage': 'cpc',
            'adapter-usage': 'adapter',
            'flash-memory-usage': 'cpc',
            'roce-usage': 'cpc'
        }
        managed_object = metrics_group_to_managed_object[self._metrics_group]
        if managed_object == 'cpc':
            # print("Finding CPC by uri=%s ..." % self._uri)
            try:
                filter_args = {'object-uri': self._uri}
                cpc = self._client.cpcs.find(**filter_args)
                # print(cpc)
                # print("Found CPC %s at: %s" % (cpc.name, cpc.uri))
                return cpc
            except NotFound:
                print("Could not find CPC on HMC %s" %
                      self._client.session.host)

        elif managed_object == 'logical-partition':
            # print("Finding LPAR by uri=%s ..." % self._uri)
            lpar = None
            for cpc in self._client.cpcs.list():
                try:
                    filter_args = {'object-uri': self._uri}
                    lpar = cpc.lpars.find(**filter_args)
                    # print (lpar)
                    # print("Found LPAR %s at: %s" % (lpar.name, lpar.uri))
                    return lpar
                except NotFound:
                    pass
            print("Could not find LPAR on HMC %s" % self._client.session.host)
        elif managed_object == 'partition':
            # print("Finding Partition by uri=%s ..." % self._uri)
            partition = None
            for cpc in self._client.cpcs.list():
                try:
                    filter_args = {'object-uri': self._uri}
                    partition = cpc.partitions.find(**filter_args)
                    # print(partition)
                    # print("Found Partition %s at: %s" % (partition.name,
                    #      partition.uri))
                    return partition
                except NotFound:
                    pass
            print("Could not find Partition on HMC %s" %
                  self._client.session.host)
        else:
            print("Unsupported metrics_group: " + self._metrics_group)
        return None
