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
A Metrics Service provides a mechanism to retrieve performance
metric data for resources of a physical z Systems or LinuxONE computer.
A structure called a :term:`Metrics Context` is associated with
any metrics retrieval, and that structure includes metric group names,
individual metric field names, and the associated individual
metric data types.
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
    Manager providing access to the :term:`Metric sContexts <Metrics Context>`
    exposed by the HMC this client is connected to.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible as properties in higher level resources (in this case,
    the :class:`~zhmcclient.Client` object connecting to the HMC).
    """

    def __init__(self, client):
        # This function should not go into the docs.
        # Parameters:
        #   client (:class:`~zhmcclient.Client`):
        #      Client object for the HMC to be used.

        # Resource properties that are supported as filter query parameters
        # (for server-side filtering).
        query_props = [
        ]

        super(MetricsContextManager, self).__init__(
            resource_class=MetricsContext,
            parent=None,
            uri_prop='object-uri',
            name_prop='',
            query_props=query_props)

        self._session = client.session
        self._metrics_contexts = []
        self._client = client

    @logged_api_call
    def list(self, full_properties=False):
        """
        List the MetricsContext exposed by the HMC this client is connected to.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

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
        Create and configure a Metrics Context in this Session.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Metrics Context' in the :term:`HMC API` book.

        Returns:

          MetricsContext:
            The resource object for the new MetricsContext.
            The object will have its 'metrics-context-uri'
            property set as returned by the HMC,
            and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post('/api/services/metrics/context',
                                   body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
#        print(result)
#        props = properties.copy()
#        props.update(result)
        new_metrics_context = MetricsContext(self,
                                             result['metrics-context-uri'],
                                             None,
                                             result)
        self._metrics_contexts.append(new_metrics_context)
        return new_metrics_context

    @property
    def client(self):
        return self._client


class MetricsContext(BaseResource):
    """
    Representation of a :term:`Metrics Context`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are directly created by the user.
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.CpcManager`):
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
        Start this CPC, using the HMC operation "Start CPC".

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
        result = self.manager.session.get(self.uri)
        return result

    def delete(self):
        """
        Delete this MetricsContext.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.list().remove(self)
        self.manager.session.delete(self.uri)


class CollectedMetrics(object):

    def __init__(self, metrics_context, rawdata):
        """
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

    def __init__(self, client, metrics_group, uri, timestamp, metrics):
        """
        """
        self._client = client
        self._metrics_group = metrics_group
        self._uri = uri
        self._timestamp = timestamp
        self._metrics = metrics

    @property
    def properties(self):
        """
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
        """
        return self._metrics_group

    @property
    def timestamp(self):
        """
        """
        return self._timestamp

    @logged_api_call
    def get_property(self, name):
        return self._metrics[name]

    @logged_api_call
    def prop(self, name, default=None):
        return self._metrics[name]

    @property
    def managed_object(self):
        """
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
