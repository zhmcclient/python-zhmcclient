# Copyright 2016,2021 IBM Corp. All Rights Reserved.
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


from collections import OrderedDict
import yaml
import yamlloader
import jsonschema
import zhmcclient

from zhmcclient._utils import datetime_from_isoformat, repr_obj_id

from ._hmc import FakedHmc, FakedMetricObjectValues
from ._urihandler import UriHandler, HTTPError, URIS
from ._urihandler import ConnectionError  # pylint: disable=redefined-builtin

__all__ = ['FakedSession', 'HmcDefinitionYamlError', 'HmcDefinitionSchemaError']


# JSON schema for a faked HMC definition
FAKED_HMC_DEFINITION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "description": "JSON schema for a faked HMC definition",
    "definitions": {
        "Properties": {
            "description": "Dictionary of resource properties. Keys are the "
                           "property names in HMC format (with dashes)",
            "type": "object",
            "patternProperties": {
                "^[a-z0-9\\-]+$": {
                    "description": "A resource property value",
                    "type": ["object", "array", "string", "integer", "number",
                             "boolean", "null"],
                },
            },
        },
        "Hmc": {
            "description": "The definition of a faked HMC",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "host",
                "api_version",
                "consoles",
            ],
            "properties": {
                "host": {
                    "description": "The hostname or IP address of the HMC host",
                    "type": "string",
                },
                "api_version": {
                    "description": "The version of the HMC WS API, as "
                                   "major.minor",
                    "type": "string",
                },
                "metric_values": {
                    "description": "The metric values prepared for later "
                                   "retrieval",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/MetricValues"
                    },
                },
                "metrics_contexts": {
                    "description": "The metrics contexts defined on this HMC",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/MetricsContext"
                    },
                },
                "consoles": {
                    "description": "The consoles (HMCs). There is only "
                                   "a single console.",
                    "type": "array",
                    "maxItems": 1,
                    "items": {
                        "$ref": "#/definitions/Console"
                    },
                },
                "cpcs": {
                    "description": "The CPCs managed by this HMC",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/Cpc"
                    },
                },
            },
        },
        "MetricValues": {
            "description": "The metric values of a single metric group for a "
                           "single resource object at a point in time, "
                           "prepared for later retrieval",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "group_name",
                "resource_uri",
                "timestamp",
                "metrics",
            ],
            "properties": {
                "group_name": {
                    "description": "Name of the metric group definition for "
                                   "these metric values",
                    "type": "string",
                },
                "resource_uri": {
                    "description": "URI of the resource object for these "
                                   "metric values",
                    "type": "string",
                },
                "timestamp": {
                    "description": "Point in time for these metric values, "
                                   "as a string in ISO8601 format",
                    "type": "string",
                },
                "metrics": {
                    "description": "The metrics (values by name)",
                    "type": "object",
                    "patternProperties": {
                        "^[a-z0-9\\-]+$": {
                            "description": "The value of the metric",
                            "type": ["string", "integer", "number",
                                     "boolean", "null"],
                        },
                    },
                },
            },
        },
        "MetricsContext": {
            "description": "A metrics context defined on an HMC",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "Console": {
            "description": "A console (HMC)",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
                "users": {
                    "description": "The users defined on this HMC",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/User"
                    },
                },
                "user_roles": {
                    "description": "The user roles defined on this HMC",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/UserRole"
                    },
                },
                "user_patterns": {
                    "description": "The user patterns defined on this HMC",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/UserPattern"
                    },
                },
                "password_rules": {
                    "description": "The password rules defined on this HMC",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/PasswordRule"
                    },
                },
                "tasks": {
                    "description": "The tasks defined on this HMC",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/Task"
                    },
                },
                "ldap_server_definitions": {
                    "description": "The LDAP server definitions on this HMC",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/LdapServerDefinition"
                    },
                },
                "unmanaged_cpcs": {
                    "description": "The unmanaged CPCs discovered by this HMC",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/UnmanagedCpc"
                    },
                },
                "storage_groups": {
                    "description": "The storage groups defined on this HMC",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/StorageGroup"
                    },
                },
            },
        },
        "User": {
            "description": "A user defined on an HMC",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "UserRole": {
            "description": "A user role defined on an HMC",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "UserPattern": {
            "description": "A user pattern defined on an HMC",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "PasswordRule": {
            "description": "A password rule defined on an HMC",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "Task": {
            "description": "A task defined on an HMC",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "LdapServerDefinition": {
            "description": "An LPAP server definition on an HMC",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "UnmanagedCpc": {
            "description": "An unmanaged CPC discovered by an HMC",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "StorageGroup": {
            "description": "A storage group defined on an HMC (and associated "
                           "with a CPC)",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
                "storage_volumes": {
                    "description": "The storage volumes of this storage group",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/StorageVolume"
                    },
                },
                "virtual_storage_resources": {
                    "description": "The VSRs of this storage group",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/VirtualStorageResource"
                    },
                },
            },
        },
        "StorageVolume": {
            "description": "A storage volume of a storage group",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "VirtualStorageResource": {
            "description": "A VSR of a storage group",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "Cpc": {
            "description": "A CPC managed by an HMC",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
                "capacity_groups": {
                    "description": "The capacity groups of this CPC (any mode)",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/CapacityGroup"
                    },
                },
                "partitions": {
                    "description": "The partitions of this CPC (DPM mode)",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/Partition"
                    },
                },
                "adapters": {
                    "description": "The adapters of this CPC (DPM mode)",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/Adapter"
                    },
                },
                "virtual_switches": {
                    "description": "The virtual switches of this CPC "
                                   "(DPM mode)",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/VirtualSwitch"
                    },
                },
                "lpars": {
                    "description": "The LPARs of this CPC (classic mode)",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/Lpar"
                    },
                },
                "reset_activation_profiles": {
                    "description": "The reset activation profiles of this CPC "
                                   "(classic mode)",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/ResetActivationProfile"
                    },
                },
                "image_activation_profiles": {
                    "description": "The image activation profiles of this CPC "
                                   "(classic mode)",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/ImageActivationProfile"
                    },
                },
                "load_activation_profiles": {
                    "description": "The load activation profiles of this CPC "
                                   "(classic mode)",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/LoadActivationProfile"
                    },
                },
            },
        },
        "CapacityGroup": {
            "description": "A capacity group in a CPC",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "Partition": {
            "description": "A partition of a CPC (DPM mode)",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
                "devno_pool": {
                    "description": "Internal state: The pool of "
                                   "auto-allocated device numbers for this "
                                   "partition",
                    "type": "object",
                    "additionalProperties": True,
                },
                "wwpn_pool": {
                    "description": "Internal state: The pool of "
                                   "auto-allocated WWPNs for this partition",
                    "type": "object",
                    "additionalProperties": True,
                },
                "nics": {
                    "description": "The NICs of this partition",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/Nic"
                    },
                },
                "hbas": {
                    "description": "The HBAs of this partition (up to z13)",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/Hba"
                    },
                },
                "virtual_functions": {
                    "description": "The virtual functions of this partition",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/VirtualFunction"
                    },
                },
            },
        },
        "Nic": {
            "description": "A NIC of a partition",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "Hba": {
            "description": "An HBA of a partition (up to z13)",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "VirtualFunction": {
            "description": "A virtual function of a partition",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "Adapter": {
            "description": "An adapter of a CPC (DPM mode)",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
                "ports": {
                    "description": "The ports of this adapter",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/Port"
                    },
                },
            },
        },
        "Port": {
            "description": "A port of an adapter",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "Lpar": {
            "description": "An LPAR of a CPC (classic mode)",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "VirtualSwitch": {
            "description": "A virtual switch in a CPC (DPM mode)",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "ResetActivationProfile": {
            "description": "A reset activation profile of a CPC (classic mode)",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "ImageActivationProfile": {
            "description": "An image activation profile of a CPC "
                           "(classic mode)",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
        "LoadActivationProfile": {
            "description": "A load activation profile of a CPC (classic mode)",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "properties",
            ],
            "properties": {
                "properties": {
                    "$ref": "#/definitions/Properties"
                },
            },
        },
    },
    "type": "object",
    "additionalProperties": False,
    "required": [
        "hmc_definition",
    ],
    "properties": {
        "hmc_definition": {
            "$ref": "#/definitions/Hmc"
        },
    },
}


class HmcDefinitionYamlError(Exception):
    """
    An error that is raised when loading an HMC definition and that indicates
    invalid YAML syntax in the faked HMC definition, at the YAML scanner or
    parser level.

    ``args[0]`` will be set to a message detailing the issue.
    """

    def __init__(self, message):
        # pylint: disable=useless-super-delegation
        super().__init__(message)


class HmcDefinitionSchemaError(Exception):
    """
    An error that is raised when loading an HMC definition and that indicates
    that the data in the faked HMC definition fails schema validation.

    ``args[0]`` will be set to a message detailing the issue.
    """

    def __init__(self, message):
        # pylint: disable=useless-super-delegation
        super().__init__(message)


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

    def __init__(self, host, hmc_name, hmc_version, api_version,
                 userid=None, password=None):
        """
        Parameters:

          host (:term:`string`):
            HMC host the mocked HMC will be set up with.

          hmc_name (:term:`string`):
            HMC name. Used for result of Query Version Info operation.

          hmc_version (:term:`string`):
            HMC version string (e.g. '2.13.1'). Used for result of
            Query Version Info operation.

          api_version (:term:`string`):
            HMC API version string (e.g. '1.8'). Used for result of
            Query Version Info operation.

          userid (:term:`string`):
            HMC userid for logging in to the mocked HMC.

          password (:term:`string`):
            HMC password for logging in to the mocked HMC.
        """
        super().__init__(
            host, userid=userid, password=password)
        self._hmc = FakedHmc(self, hmc_name, hmc_version, api_version)
        self._urihandler = UriHandler(URIS)
        self._object_topic = 'faked-notification-topic'
        self._job_topic = 'faked-job-notification-topic'

    def __repr__(self):
        """
        Return a string with the state of this faked session, for debug
        purposes.
        """
        ret = (
            f"{repr_obj_id(self)} (\n"
            f"  _hosts = {self._hosts!r}\n"
            f"  _userid = {self._userid!r}\n"
            f"  _password = '...'\n"
            f"  _get_password = {self._get_password!r}\n"
            f"  _retry_timeout_config = {self._retry_timeout_config!r}\n"
            f"  _actual_host = {self._actual_host!r}\n"
            f"  _base_url = {self._base_url!r}\n"
            f"  _headers = {self._headers!r}\n"
            f"  _session_id = {self._session_id!r}\n"
            f"  _session = {self._session!r}\n"
            f"  _hmc = {repr_obj_id(self._hmc)}\n"
            f"  _urihandler = {self._urihandler!r}\n"
            ")")
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

    @staticmethod
    def from_hmc_yaml_file(filepath, userid=None, password=None):
        """
        Return a new FakedSession object from an HMC definition in a YAML file.

        The data format of the YAML file is validated using a schema.

        Parameters:

          filepath(:term:`string`): Path name of the YAML file that contains
            the HMC definition.

          userid (:term:`string`):
            Userid of the HMC user to be used for logging in, or `None`.

          password (:term:`string`):
            Password of the HMC user if `userid` was specified, or `None`.

        Returns:

          FakedSession: New faked session with faked HMC set up from HMC
          definition.

        Raises:

            IOError: Error opening the YAML file for reading.
            YamlFormatError: Invalid YAML syntax in HMC definition.
            HmcDefinitionSchemaError: Invalid data format in HMC definition.
        """
        # pylint: disable=unspecified-encoding
        with open(filepath) as fp:
            hmc = FakedSession.from_hmc_yaml(fp, filepath, userid, password)
        return hmc

    @staticmethod
    def from_hmc_yaml(hmc_yaml, filepath=None, userid=None, password=None):
        """
        Return a new FakedSession object from an HMC definition YAML string
        or stream.

        An HMC definition YAML string can be created using
        :meth:`zhmcclient.Client.to_hmc_yaml`.

        The timestamp in metric values can have any valid ISO8601 format.
        Timezone-naive values are amended with the local timezone.

        The data format of the YAML string is validated using a schema.

        Parameters:

          hmc_yaml(string or stream): HMC definition YAML string or stream.

          filepath(string): Path name of the YAML file that contains the HMC
            definition; used only in exception messages. If `None`, no
            filename is used in exception messages.

          userid (:term:`string`):
            Userid of the HMC user to be used for logging in, or `None`.

          password (:term:`string`):
            Password of the HMC user if `userid` was specified, or `None`.

        Returns:

          FakedSession: New faked session with faked HMC set up from HMC
          definition.

        Raises:

            YamlFormatError: Invalid YAML syntax in HMC definition YAML string
              or stream.
            HmcDefinitionSchemaError: Invalid data format in HMC definition.
        """

        try:
            hmc_dict = yaml.load(
                hmc_yaml, Loader=yamlloader.ordereddict.SafeLoader)
        except (yaml.parser.ParserError, yaml.scanner.ScannerError) as exc:
            if filepath:
                file_str = f" in file {filepath}"
            else:
                file_str = ""
            new_exc = HmcDefinitionYamlError(
                f"Invalid YAML syntax in faked HMC definition{file_str}: {exc}")
            new_exc.__cause__ = None
            raise new_exc  # HmcDefinitionYamlError

        hmc = FakedSession.from_hmc_dict(hmc_dict, filepath, userid, password)
        return hmc

    @staticmethod
    def from_hmc_dict(hmc_dict, filepath=None, userid=None, password=None):
        """
        Return a new FakedSession object from an HMC definition dictionary.

        An HMC definition dictionary can be created using
        :meth:`zhmcclient.Client.to_hmc_dict`.

        The timestamp in metric values can have any valid ISO8601 format.
        Timezone-naive values are amended with the local timezone.

        The data format of the YAML string is validated using a schema.

        Parameters:

          hmc_dict(dict): HMC definition dictionary.

          filepath(string): Path name of the YAML file that contains the HMC
            definition; used only in exception messages. If `None`, no
            filename is used in exception messages.

          userid (:term:`string`):
            Userid of the HMC user to be used for logging in, or `None`.

          password (:term:`string`):
            Password of the HMC user if `userid` was specified, or `None`.

        Returns:

          FakedSession: New faked session with faked HMC set up from the HMC
          definition.

        Raises:

            HmcDefinitionSchemaError: Invalid data format in HMC definition.
        """

        try:
            jsonschema.validate(hmc_dict, FAKED_HMC_DEFINITION_SCHEMA)
        except jsonschema.exceptions.ValidationError as exc:
            if filepath:
                file_str = f" in file {filepath}"
            else:
                file_str = ""
            elem = '.'.join(str(e) for e in exc.absolute_path)
            schemaitem = '.'.join(str(e) for e in exc.absolute_schema_path)
            new_exc = HmcDefinitionSchemaError(
                f"Invalid data format in faked HMC definition{file_str}: "
                f"{exc.message}; "
                f"Offending element: {elem}; "
                f"Schema item: {schemaitem}; "
                f"Validator: {exc.validator}={exc.validator_value}")
            new_exc.__cause__ = None
            raise new_exc  # HmcDefinitionSchemaError

        hmc_res_dict = hmc_dict['hmc_definition']

        consoles = hmc_res_dict.get('consoles')
        console = consoles[0]
        host = hmc_res_dict['host']
        api_version = hmc_res_dict['api_version']
        hmc_name = console['properties']['name']
        hmc_version = console['properties']['version']

        session = FakedSession(host, hmc_name, hmc_version, api_version,
                               userid=userid, password=password)

        res_dict = OrderedDict()
        res_dict['consoles'] = consoles
        cpcs = hmc_res_dict.get('cpcs')
        if cpcs:
            res_dict['cpcs'] = cpcs
        metrics_contexts = hmc_res_dict.get('metrics_contexts')
        if metrics_contexts:
            res_dict['metrics_contexts'] = metrics_contexts
        session.hmc.add_resources(res_dict)

        mv_dicts = hmc_res_dict.get('metric_values')
        if mv_dicts:
            for mv_dict in mv_dicts:
                group_name = mv_dict['group_name']
                resource_uri = mv_dict['resource_uri']
                timestamp = datetime_from_isoformat(mv_dict['timestamp'])
                values = []
                for name, value in mv_dict['metrics'].items():
                    item_tup = (name, value)
                    values.append(item_tup)
                mv = FakedMetricObjectValues(
                    group_name=group_name,
                    resource_uri=resource_uri,
                    timestamp=timestamp,
                    values=values)
                session.hmc.add_metric_values(mv)

        return session

    def get(self, uri, resource=None, logon_required=True, renew_session=True):
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

          renew_session (bool):
            Boolean indicating whether the session should be renewed in case
            it is expired.

            This parameter exists for compatibility with real HMCs, but is
            ignored.

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
            new_exc = zhmcclient.HTTPError(exc.response())
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient.HTTPError
        except ConnectionError as exc:
            new_exc = zhmcclient.ConnectionError(exc.message, None)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient.ConnectionError

    def post(self, uri, resource=None, body=None, logon_required=True,
             wait_for_completion=True, operation_timeout=None,
             renew_session=True):
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

          renew_session (bool):
            Boolean indicating whether the session should be renewed in case
            it is expired.

            This parameter exists for compatibility with real HMCs, but is
            ignored.

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
            new_exc = zhmcclient.HTTPError(exc.response())
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient.HTTPError
        except ConnectionError as exc:
            new_exc = zhmcclient.ConnectionError(exc.message, None)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient.ConnectionError

    def delete(
            self, uri, resource=None, logon_required=True, renew_session=True):
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

          renew_session (bool):
            Boolean indicating whether the session should be renewed in case
            it is expired.

            This parameter exists for compatibility with real HMCs, but is
            ignored.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError` (not implemented)
          :exc:`~zhmcclient.AuthError` (not implemented)
          :exc:`~zhmcclient.ConnectionError`
        """
        try:
            self._urihandler.delete(self._hmc, uri, logon_required)
        except HTTPError as exc:
            new_exc = zhmcclient.HTTPError(exc.response())
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient.HTTPError
        except ConnectionError as exc:
            new_exc = zhmcclient.ConnectionError(exc.message, None)
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient.ConnectionError
