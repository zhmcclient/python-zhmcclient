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
The HMC supports the retrieval of metrics values for resources of a IBM Z
or LinuxONE computer. This section describes the zhmcclient API for retrieving
such metrics from the HMC.

A resource termed :term:`Metrics Context` is associated with any metrics
retrieval. These resources are user-created definitions of the kinds of metrics
that are intended to be retrieved. A metrics context mostly defines the names
of the metric groups to be retrieved. The available metric groups are described
in section 'Metric Groups' in the :term:`HMC API` book.

The zhmcclient API for metrics provides access to the metric values and to
their definitions, so that clients using the metric values do not need to have
intimate knowledge about the specific metric values when just displaying them.

The basic usage of the metrics API is shown in this example:

.. code-block:: python

    # Create a Metrics Context for the desired metric groups:
    metric_groups = ['dpm-system-usage-overview', 'partition-usage']
    mc = client.metrics_contexts.create(
        {'anticipated-frequency-seconds': 15,
         'metric-groups': metric_groups})

    # Retrieve the current metric values:
    mr_str = mc.get_metrics()

    # Display the metric values:
    print("Current metric values:")
    mr = zhmcclient.MetricsResponse(mc, mr_str)
    for mg in mr.metric_group_values:
        mg_name = mg.name
        mg_def = mc.metric_group_definitions[mg_name]
        print(f"  Metric group: {mg_name}")
        for ov in mg.object_values:
            print(f"    Resource: {ov.resource_uri}")
            print(f"    Timestamp: {ov.timestamp}")
            print("    Metric values:")
            for m_name in ov.metrics:
                m_value = ov.metrics[m_name]
                m_def = mg_def.metric_definitions[m_name]
                m_unit = m_def.unit or ''
                print(f"      {m_name:30}  {m_value} {m_unit}")
        if not mg.object_values:
            print("    No resources")

    # Delete the Metrics Context:
    mc.delete()
"""


from collections import namedtuple
import re
from datetime import datetime
import pytz

from ._manager import BaseManager
from ._resource import BaseResource
from ._cpc import Cpc
from ._lpar import Lpar
from ._partition import Partition
from ._adapter import Adapter
from ._nic import Nic
from ._logging import logged_api_call
from ._exceptions import NotFound, MetricsResourceNotFound
from ._utils import datetime_from_timestamp, repr_list, datetime_to_isoformat, \
    repr_obj_id

__all__ = ['MetricsContextManager', 'MetricsContext', 'MetricGroupDefinition',
           'MetricDefinition', 'MetricsResponse', 'MetricGroupValues',
           'MetricObjectValues']

# Initial HMC API version for certain HMC versions
API_VERSION_HMC_2_14_0 = (2, 20)

# List of API features we check for (since HMC 2.16 and API version 4.10)
API_FEATURE_ADAPTER_NETWORK_INFORMATION = 'adapter-network-information'


class MetricsContextManager(BaseManager):
    """
    Manager providing access to the :term:`Metrics Context` resources that
    were created through this manager object.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the :attr:`~zhmcclient.Client.metrics_contexts` attribute
    of the :class:`~zhmcclient.Client` object connected to the HMC.

    HMC/SE version requirements: None
    """

    def __init__(self, client):
        # This function should not go into the docs.
        # Parameters:
        #   client (:class:`~zhmcclient.Client`):
        #      Client object for the HMC to be used.
        super().__init__(
            resource_class=MetricsContext,
            class_name='',
            session=client.session,
            parent=None,
            base_uri='/api/services/metrics/context',
            oid_prop='',
            uri_prop='metrics-context-uri',
            name_prop='',
            query_props=[])

        self._client = client
        self._metrics_contexts = []

    def __repr__(self):
        """
        Return a string with the state of this manager object, for debug
        purposes.
        """
        ret = (
            f"{repr_obj_id(self)} (\n"
            f"  _resource_class={self._resource_class!r},\n"
            f"  _class_name={self._class_name!r},\n"
            f"  _session={repr_obj_id(self._session)},\n"
            f"  _parent={repr_obj_id(self._parent)},\n"
            f"  _base_uri={self._base_uri!r},\n"
            f"  _oid_prop={self._oid_prop!r},\n"
            f"  _uri_prop={self._uri_prop!r},\n"
            f"  _name_prop={self._name_prop!r},\n"
            f"  _query_props={repr_list(self._query_props, indent=2)},\n"
            f"  _list_has_name={self._list_has_name!r},\n"
            f"  _name_uri_cache={self._name_uri_cache!r},\n"
            f"  _client={repr_obj_id(self._client)},\n"
            "  _metrics_contexts="
            f"{repr_list(self._metrics_contexts, indent=2)},\n"
            ")")
        return ret

    @property
    def client(self):
        """
        :class:`~zhmcclient.Client`:
          The client defining the scope for this manager.
        """
        return self._client

    @logged_api_call
    def list(self, full_properties=False):
        # pylint: disable=arguments-differ
        """
        List the :term:`Metrics Context` resources that were created through
        this manager object.

        Note that the HMC does not provide a way to enumerate the existing
        :term:`Metrics Context` resources. Therefore, this method will only
        list the :term:`Metrics Context` resources that were created through
        this manager object. For example, :term:`Metrics Context` resources
        created through a second :class:`~zhmcclient.Client` object will not be
        listed.

        HMC/SE version requirements: None

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

    @logged_api_call
    def create(self, properties):
        """
        Create a :term:`Metrics Context` resource in the HMC this client is
        connected to.

        HMC/SE version requirements: None

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Metrics Context' in the :term:`HMC API` book.

        Returns:

          :class:`~zhmcclient.MetricsContext`:
            The resource object for the new :term:`Metrics Context` resource.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post('/api/services/metrics/context',
                                   body=properties)
        mc_properties = properties.copy()
        mc_properties.update(result)
        new_metrics_context = MetricsContext(self,
                                             result['metrics-context-uri'],
                                             None,
                                             mc_properties)
        self._metrics_contexts.append(new_metrics_context)
        return new_metrics_context


class MetricsContext(BaseResource):
    """
    Representation of a :term:`Metrics Context` resource.

    A :term:`Metrics Context` resource specifies a list of metrics groups for
    which the current metric values can be retrieved using the
    :meth:`~zhmcclient.MetricsContext.get_metrics` method.

    The properties of this resource are the response fields described for the
    'Create Metrics Context' operation in the :term:`HMC API` book.

    This class is derived from :class:`~zhmcclient.BaseResource`; see there
    for common methods and attributes.

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
                "MetricsContext init: Expected manager type "
                f"{MetricsContextManager}, got {type(manager)}")
        super().__init__(manager, uri, name, properties)

        self._metric_group_definitions = self._setup_metric_group_definitions()

    def _setup_metric_group_definitions(self):
        """
        Return the dict of MetricGroupDefinition objects for this metrics
        context, by processing its 'metric-group-infos' property.
        """
        # Dictionary of MetricGroupDefinition objects, by metric group name
        metric_group_definitions = {}
        for mg_info in self._properties['metric-group-infos']:
            mg_name = mg_info['group-name']
            mg_def = MetricGroupDefinition(
                name=mg_name,
                resource_class=_resource_class_from_group(mg_name),
                metric_definitions={})
            for i, m_info in enumerate(mg_info['metric-infos']):
                m_name = m_info['metric-name']
                m_def = MetricDefinition(
                    index=i,
                    name=m_name,
                    type=_metric_type(m_info['metric-type']),
                    unit=_metric_unit_from_name(m_name))
                mg_def.metric_definitions[m_name] = m_def
            metric_group_definitions[mg_name] = mg_def
        return metric_group_definitions

    @property
    def metric_group_definitions(self):
        """
        dict: The metric definitions for the metric groups of this
          :term:`Metrics Context` resource, as a dictionary of
          :class:`~zhmcclient.MetricGroupDefinition` objects, by metric group
          name.
        """
        return self._metric_group_definitions

    @logged_api_call
    def get_metrics(self):
        """
        Retrieve the current metric values for this :term:`Metrics Context`
        resource from the HMC.

        The metric values are returned by this method as a string in the
        `MetricsResponse` format described with the 'Get Metrics' operation in
        the :term:`HMC API` book.

        The :class:`~zhmcclient.MetricsResponse` class can be used to process
        the `MetricsResponse` string returned by this method, and provides
        structured access to the metrics values.

        HMC/SE version requirements: None

        Returns:

          :term:`string`:
            The current metric values, in the `MetricsResponse` string format.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        metrics_response = self.manager.session.get(self.uri, resource=self)
        return metrics_response

    @logged_api_call
    def delete(self):
        """
        Delete this :term:`Metrics Context` resource.

        HMC/SE version requirements: None

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.delete(self.uri, resource=self)
        self.manager._metrics_contexts.remove(self)


_MetricGroupDefinitionTuple = namedtuple(
    '_MetricGroupDefinitionTuple',
    ['name', 'resource_class', 'metric_definitions']
)


class MetricGroupDefinition(_MetricGroupDefinitionTuple):
    """
    A :func:`namedtuple <py:collections.namedtuple>` representing definitional
    information for a metric group.

    HMC/SE version requirements: None
    """

    def __new__(cls, name, resource_class, metric_definitions):
        """
        Parameters:

          name (:term:`string`):
            Metric group name, as defined in section 'Metric groups' in the
            :term:`HMC API` book.

          resource_class (:term:`string`):
            A string identifying the resource class to which this metric group
            belongs, using the values from the 'class' property of resource
            objects.

          metric_definitions (dict):
            Metric definitions for the metrics in this metric group, as a
            dictionary where the key is the metric name and the value is the
            :class:`~zhmcclient.MetricDefinition` object for the metric.

        All these parameters are also available as same-named attributes.
        """
        self = super().__new__(
            cls, name, resource_class, metric_definitions)
        return self

    __slots__ = ()

    def __repr__(self):
        repr_str = (
            "MetricGroupDefinition("
            f"name={self.name!r}, "
            f"resource_class={self.resource_class!r}, "
            f"metric_definitions={self.metric_definitions!r})")
        return repr_str


_MetricDefinitionTuple = namedtuple(
    '_MetricDefinitionTuple',
    ['index', 'name', 'type', 'unit']
)


class MetricDefinition(_MetricDefinitionTuple):
    """
    A :func:`namedtuple <py:collections.namedtuple>` representing definitional
    information for a single metric.

    HMC/SE version requirements: None
    """

    def __new__(cls, index, name, type, unit):
        # pylint: disable=redefined-builtin
        """
        Parameters:

          index (:term:`integer`):
            0-based index (=position) of the metric in a MetricsResponse value
            row.

          name (:term:`string`):
            Metric field name, as shown in the tables defining the metric
            groups in section 'Metric groups' in the :term:`HMC API` book.

          type (:term:`callable`):
            Python type for the metric value. The type must be a constructor
            (callable) that takes the metrics value from the `MetricsResponse`
            string as its only argument, using the following Python types
            for the metric group description types shown in the :term:`HMC API`
            book:

            =============================  ======================
            Description type               Python type
            =============================  ======================
            Boolean                        :class:`py:bool`
            Byte                           :term:`integer`
            Short                          :term:`integer`
            Integer                        :term:`integer`
            Long                           :term:`integer`
            Double                         :class:`py:float`
            String, String Enum            :term:`unicode string`
            =============================  ======================

          unit (:term:`string`):
            Unit of the metric value.

        All these parameters are also available as same-named attributes.
        """
        self = super().__new__(
            cls, index, name, type, unit)
        return self

    __slots__ = ()

    def __repr__(self):
        repr_str = (
            "MetricDefinition("
            f"index={self.index!r}, "
            f"name={self.name!r}, "
            f"type={self.type!r}, "
            f"unit={self.unit!r})")
        return repr_str


def _metric_type(metric_type_name):
    """
    Return a constructor callable for the given metric type name.

    The returned callable takes the metric value as a string as its only
    argument and returns a Python object representing that metric value using
    the correct Python type.
    """
    return _METRIC_TYPES_BY_NAME[metric_type_name]


_METRIC_TYPES_BY_NAME = {
    'boolean-metric': bool,
    'byte-metric': int,
    'short-metric': int,
    'integer-metric': int,
    'long-metric': int,
    'double-metric': float,
    'string-metric': str,
}


def _metric_value(value_str, metric_type):
    """
    Return a Python-typed metric value from a metric value string.
    """
    if metric_type in (int, float):
        try:
            return metric_type(value_str)
        except ValueError:
            new_exc = ValueError(
                f"Invalid {metric_type.__class__.__name__} metric value: "
                f"{value_str!r}")
            new_exc.__cause__ = None
            raise new_exc  # ValueError
    elif metric_type is str:
        # In Python 3, decode('unicode_escape) requires bytes, so we need
        # to encode to bytes. This also works in Python 2.
        return value_str.strip('"').encode('utf-8').decode('unicode_escape')
    else:
        assert metric_type is bool
        lower_str = value_str.lower()
        if lower_str == 'true':
            return True
        if lower_str == 'false':
            return False
        raise ValueError(f"Invalid boolean metric value: {value_str!r}")


def _metric_unit_from_name(metric_name):
    """
    Return a metric unit string for human consumption, that is inferred from
    the metric name.

    If a unit cannot be inferred, `None` is returned.
    """
    for item in _PATTERN_UNIT_LIST:
        pattern, unit = item
        if pattern.match(metric_name):
            return unit
    return None


_USE_UNICODE = True
if _USE_UNICODE:
    MICROSECONDS = "\u00b5s"  # U+00B5 = Micro Sign
    CELSIUS = "\u00B0C"  # U+00B0 = Degree Sign
    # Note: Use of U+2103 (Degree Celsius) is discouraged by Unicode standard
else:
    MICROSECONDS = "us"
    CELSIUS = "degree Celsius"  # Official SI unit when not using degree sign


_PATTERN_UNIT_LIST = {
    # End patterns:
    (re.compile(r".+-usage$"), "%"),
    (re.compile(r".+-time$"), MICROSECONDS),
    (re.compile(r".+-time-used$"), MICROSECONDS),
    (re.compile(r".+-celsius$"), CELSIUS),
    (re.compile(r".+-watts$"), "W"),
    (re.compile(r".+-paging-rate$"), "pages/s"),
    (re.compile(r".+-sampling-rate$"), "samples/s"),
    # Begin patterns:
    (re.compile(r"^bytes-.+"), "B"),
    (re.compile(r"^heat-load.+"), "BTU/h"),  # Note: No trailing hyphen
    (re.compile(r"^interval-bytes-.+"), "B"),
    (re.compile(r"^bytes-per-second-.+"), "B/s"),
    # Special cases:
    (re.compile(r"^storage-rate$"), "kB/s"),
    (re.compile(r"^humidity$"), "%"),
    (re.compile(r"^memory-used$"), "MiB"),
    (re.compile(r"^policy-activation-time$"), ""),  # timestamp
    (re.compile(r"^velocity-numerator$"), MICROSECONDS),
    (re.compile(r"^velocity-denominator$"), MICROSECONDS),
    (re.compile(r"^utilization$"), "%"),
}


def _resource_class_from_group(metric_group_name):
    """
    Return the resource class string from the metric group name.

    Metric groups for resources that are specific to ensemble mode are not
    supported.

    Returns an empty string if a metric group name is unknown.
    """
    return CLASS_FROM_GROUP.get(metric_group_name, '')


CLASS_FROM_GROUP = {
    # DPM mode only:
    'dpm-system-usage-overview': 'cpc',
    'partition-usage': 'partition',
    'adapter-usage': 'adapter',
    'network-physical-adapter-port': 'adapter',
    'partition-attached-network-interface': 'nic',
    # Classic mode only:
    'cpc-usage-overview': 'cpc',
    'logical-partition-usage': 'logical-partition',
    'channel-usage': 'cpc',
    'crypto-usage': 'cpc',
    'flash-memory-usage': 'cpc',  # TODO: verify CPC mode dependency
    'roce-usage': 'cpc',  # TODO: verify CPC mode dependency
    # DPM mode or classic mode:
    'zcpc-environmentals-and-power': 'cpc',
    'zcpc-processor-usage': 'cpc',
}


class MetricsResponse:
    """
    Represents the metric values returned by one call to the
    :meth:`~zhmcclient.MetricsContext.get_metrics` method, and provides
    structured access to the data.

    HMC/SE version requirements: None
    """

    def __init__(self, metrics_context, metrics_response_str):
        """
        Parameters:

          metrics_context (:class:`~zhmcclient.MetricsContext`):
            The :class:`~zhmcclient.MetricsContext` object that was used to
            retrieve the metrics response string. It defines the structure of
            the metric values in the metrics response string.

          metrics_response_str (:term:`string`):
            The metrics response string, as returned by the
            :meth:`~zhmcclient.MetricsContext.get_metrics` method.
        """
        self._metrics_context = metrics_context
        self._metrics_response_str = metrics_response_str
        self._client = self._metrics_context.manager.client

        self._metric_group_values = self._setup_metric_group_values()

    def _setup_metric_group_values(self):
        """
        Return the list of MetricGroupValues objects for this metrics response,
        by processing its metrics response string.

        The lines in the metrics response string are::

            MetricsResponse: MetricsGroup{0,*}
                             <emptyline>      a third empty line at the end

            MetricsGroup:    MetricsGroupName
                             ObjectValues{0,*}
                             <emptyline>      a second empty line after each MG

            ObjectValues:    ObjectURI
                             Timestamp
                             ValueRow{1,*}
                             <emptyline>      a first empty line after this blk
        """

        mg_defs = self._metrics_context.metric_group_definitions

        metric_group_name = None
        resource_uri = None
        dt_timestamp = None

        object_values = None
        metric_group_values = []
        state = 0
        for mr_line in self._metrics_response_str.splitlines():
            if state == 0:
                if object_values is not None:
                    # Store the result from the previous metric group
                    mgv = MetricGroupValues(metric_group_name, object_values)
                    metric_group_values.append(mgv)
                    object_values = None
                if mr_line == '':
                    # Skip initial (or trailing) empty lines
                    pass
                else:
                    # Process the next metrics group
                    metric_group_name = mr_line.strip('"')  # No " or \ inside
                    assert metric_group_name in mg_defs
                    m_defs = mg_defs[metric_group_name].metric_definitions
                    object_values = []
                    state = 1
            elif state == 1:
                if mr_line == '':
                    # There are no (or no more) ObjectValues items in this
                    # metrics group
                    state = 0
                else:
                    # There are ObjectValues items
                    resource_uri = mr_line.strip('"')  # No " or \ inside
                    state = 2
            elif state == 2:
                # Process the timestamp
                assert mr_line != ''
                try:
                    dt_timestamp = datetime_from_timestamp(int(mr_line))
                except ValueError:
                    # Sometimes, the returned epoch timestamp values are way
                    # too large, e.g. 3651584404810066 (which would translate
                    # to the year 115791 A.D.). Python datetime supports
                    # up to the year 9999. We circumvent this issue by
                    # simply using the current date&time.
                    # TODO: Remove the circumvention for too large timestamps.
                    dt_timestamp = datetime.now(pytz.utc)
                state = 3
            elif state == 3:
                if mr_line != '':
                    # Process the metric values in the ValueRow line
                    str_values = mr_line.split(',')
                    metrics = {}
                    # pylint: disable=possibly-used-before-assignment
                    for m_name in m_defs:
                        m_def = m_defs[m_name]
                        m_type = m_def.type
                        m_value_str = str_values[m_def.index]
                        m_value = _metric_value(m_value_str, m_type)
                        metrics[m_name] = m_value
                    ov = MetricObjectValues(
                        self._client, mg_defs[metric_group_name], resource_uri,
                        dt_timestamp, metrics)
                    object_values.append(ov)
                    # stay in this state, for more ValueRow lines
                else:
                    # On the empty line after the last ValueRow line
                    state = 1

        return metric_group_values

    @property
    def metrics_context(self):
        """
        :class:`~zhmcclient.MetricsContext` object for this metric response.
        This can be used to access the metric definitions for this response.
        """
        return self._metrics_context

    @property
    def metric_group_values(self):
        """
        :class:`py:list`: The list of :class:`~zhmcclient.MetricGroupValues`
          objects representing the metric groups in this metric response.

          Each :class:`~zhmcclient.MetricGroupValues` object contains a list of
          :class:`~zhmcclient.MetricObjectValues` objects representing the
          metric values in this group (each for a single resource and point in
          time).
        """
        return self._metric_group_values


class MetricGroupValues:
    """
    Represents the metric values for a metric group in a MetricsResponse
    string.

    HMC/SE version requirements: None
    """

    def __init__(self, name, object_values):
        """
        Parameters:

          name (:term:`string`):
            Metric group name.

          object_values (:class:`py:list`):
            The :class:`~zhmcclient.MetricObjectValues` objects in this metric
            group. Each of them represents the metric values for a single
            resource at a single point in time.
        """
        self._name = name
        self._object_values = object_values

    @property
    def name(self):
        """
        string: The metric group name.
        """
        return self._name

    @property
    def object_values(self):
        """
        :class:`py:list`: The :class:`~zhmcclient.MetricObjectValues` objects
          in this metric group. Each of them represents the metric values for
          a single resource at a single point in time.
        """
        return self._object_values


class MetricObjectValues:
    """
    Represents the metric values for a single resource at a single point in
    time.

    HMC/SE version requirements: None
    """

    def __init__(self, client, metric_group_definition, resource_uri,
                 timestamp, metrics):
        """
        Parameters:

          client (:class:`~zhmcclient.Client`):
            Client object, for retrieving the actual resource.

          metric_group_definition (:class:`~zhmcclient.MetricGroupDefinition`):
            Metric group definition for this set of metric values.

          resource_uri (:term:`string`):
            Resource URI of the resource these metric values apply to.

          timestamp (:class:`py:datetime.datetime`):
            Point in time when the HMC captured these metric values (as a
            timezone-aware datetime object).

          metrics (dict):
            The metric values, as a dictionary of the (Python typed) metric
            values, by metric name.
        """
        self._client = client
        self._metric_group_definition = metric_group_definition
        self._resource_uri = resource_uri
        self._timestamp = timestamp
        self._metrics = metrics
        self._resource = None  # Lazy initialization

    @property
    def client(self):
        """
        :class:`~zhmcclient.Client`: Client object, for retrieving the actual
        resource.
        """
        return self._client

    @property
    def metric_group_definition(self):
        """
        :class:`~zhmcclient.MetricGroupDefinition`: Metric group definition for
        this set of metric values.
        """
        return self._metric_group_definition

    @property
    def resource_uri(self):
        """
        string: The canonical URI path of the resource these metric values
        apply to.

        Example: ``/api/cpcs/12345``
        """
        return self._resource_uri

    @property
    def timestamp(self):
        """
        :class:`py:datetime.datetime`: Point in time when the HMC captured
          these metric values (as a timezone-aware datetime object).
        """
        return self._timestamp

    @property
    def metrics(self):
        """
        dict: The metric values, as a dictionary of the (Python typed) metric
          values, by metric name.
        """
        return self._metrics

    @property
    def resource(self):
        """
        :class:`~zhmcclient.BaseResource`: The Python resource object of the
          resource these metric values apply to.

        Raises:

          :exc:`~zhmcclient.MetricsResourceNotFound`: The resource for the
          resource URI of the resource these metric values apply to, was not
          found on the HMC.
        """
        if self._resource is not None:
            return self._resource

        resource_class = self.metric_group_definition.resource_class
        resource_uri = self.resource_uri

        if resource_class == 'cpc':
            cpc_managers = [self.client.cpcs]
            filter_args = {'object-uri': resource_uri}
            try:
                resource = self.client.cpcs.find(**filter_args)
            except NotFound:
                raise MetricsResourceNotFound(
                    f"CPC with URI {resource_uri} not found on "
                    f"HMC {self.client.session.host}",
                    Cpc, cpc_managers)
        elif resource_class == 'logical-partition':
            filter_args = {'object-uri': resource_uri}
            if self.client.version_info() >= API_VERSION_HMC_2_14_0:
                lpars = self.client.consoles.console.list_permitted_lpars(
                    filter_args=filter_args)
                if len(lpars) < 1:
                    raise MetricsResourceNotFound(
                        f"LPAR with URI {resource_uri} not found",
                        Lpar, [])
                resource = lpars[0]
            else:
                lpar_managers = []
                cpc_list = self.client.cpcs.list()
                for cpc in cpc_list:
                    lpar_managers.append(cpc.lpars)
                    try:
                        resource = cpc.lpars.find(**filter_args)
                        break
                    except NotFound:
                        pass  # Try next CPC
                else:
                    raise MetricsResourceNotFound(
                        f"LPAR with URI {resource_uri} not found "
                        f"in CPCs {', '.join([cpc.name for cpc in cpc_list])}",
                        Lpar, lpar_managers)
        elif resource_class == 'partition':
            filter_args = {'object-uri': resource_uri}
            if self.client.version_info() >= API_VERSION_HMC_2_14_0:
                partitions = \
                    self.client.consoles.console.list_permitted_partitions(
                        filter_args=filter_args)
                if len(partitions) < 1:
                    raise MetricsResourceNotFound(
                        f"Partition with URI {resource_uri} not found",
                        Partition, [])
                resource = partitions[0]
            else:
                part_managers = []
                cpc_list = self.client.cpcs.list()
                for cpc in cpc_list:
                    part_managers.append(cpc.partitions)
                    try:
                        resource = cpc.partitions.find(**filter_args)
                        break
                    except NotFound:
                        pass  # Try next CPC
                else:
                    raise MetricsResourceNotFound(
                        f"Partition with URI {resource_uri} not found "
                        f"in CPCs {', '.join([cpc.name for cpc in cpc_list])}",
                        Partition, part_managers)
        elif resource_class == 'adapter':
            filter_args = {'object-uri': resource_uri}
            fallback = False
            if self.client.consoles.console.list_api_features(
                    API_FEATURE_ADAPTER_NETWORK_INFORMATION):
                adapters = self.client.consoles.console.list_permitted_adapters(
                    filter_args=filter_args)
                # The method does not return adapters of classic mode CPCs with
                # SE < 2.16.0
                if len(adapters) < 1:
                    fallback = True
                else:
                    resource = adapters[0]
            else:
                fallback = True
            if fallback:
                cpc_list = self.client.cpcs.list()
                adapter_managers = []
                for cpc in cpc_list:
                    adapter_managers.append(cpc.adapters)
                    try:
                        resource = cpc.adapters.find(**filter_args)
                        break
                    except NotFound:
                        pass  # Try next CPC
                else:
                    raise MetricsResourceNotFound(
                        f"Adapter with URI {resource_uri} not found in "
                        f"CPCs {', '.join([cpc.name for cpc in cpc_list])}",
                        Adapter, adapter_managers)
        elif resource_class == 'nic':
            nic_properties = self.client.session.get(resource_uri)
            partition_uri = nic_properties['parent']
            partitions = self.client.consoles.console.list_permitted_partitions(
                filter_args={'object-uri': partition_uri})
            if len(partitions) < 1:
                raise MetricsResourceNotFound(
                    f"Parent partition with URI {partition_uri} of NIC with "
                    f"URI {resource_uri} not found",
                    Partition, [])
            partition = partitions[0]
            cpc = partition.manager.parent
            nic_managers = [partition.nics]
            filter_args = {'element-uri': resource_uri}
            try:
                resource = partition.nics.find(**filter_args)
            except NotFound:
                raise MetricsResourceNotFound(
                    f"NIC with URI {resource_uri} not found in its parent "
                    f"partition {cpc.name}.{partition.name}",
                    Nic, nic_managers)
        else:
            raise ValueError(
                f"Invalid resource class: {resource_class!r}")

        self._resource = resource
        return self._resource

    def dump(self):
        """
        Dump these metric values as a resource definition.

        The timestamp of the object is represented as an ISO8601 string using
        this format::

            YYYY-MM-DD HH:MM:SS[.ssssss]shh:mm

        Where:

          * YYYY-MM-DD - is year, month and day.

          * HH:MM:SS - is hour in 24-hour format, minutes and seconds.

          * .ssssss - is an optional part specifying microseconds. It is not
            created when the timestamp microsecond value is 0.

          * shh:mm - is the timezone offset from UTC with sign, hours (hh) and
            minutes (mm). Since the FakedMetricObjectValues class ensures that
            the timestamp is always timezone-aware, this part is always created.

        Returns:

          dict: Resource definition of this object.
        """
        obj_dict = {}
        # Faked Simple properties
        obj_dict['group_name'] = self.metric_group_definition.name
        obj_dict['resource_uri'] = self.resource_uri
        obj_dict['timestamp'] = datetime_to_isoformat(self.timestamp)
        obj_dict['metrics'] = self.metrics
        return obj_dict
