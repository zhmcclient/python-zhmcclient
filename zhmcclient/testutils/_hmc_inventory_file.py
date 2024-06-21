# Copyright 2022 IBM Corp. All Rights Reserved.
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
Encapsulation of an HMC inventory file in YAML format.

HMC inventory files conform to the format of HMC inventory files in YAML
format and define specific additional variables for HMCs.
"""


from collections import OrderedDict
import errno
import yaml
import yamlloader
import jsonschema

__all__ = ['HMCInventoryFileError', 'HMCInventoryFile']

# Structure of an HMC inventory file in YAML format:
#
#   all:  # the top-level group
#     hosts:
#       <hmc_name>:  # DNS hostname, IP address, or nickname of HMC
#         description: <string>
#         contact: <string>
#         access_via: <string>
#         ansible_host: <host> or [<host>, ...]   # if real HMC
#         mock_file: <path_name>                  # if mocked HMC
#         cpcs:
#           <cpc_name>:
#             <prop_name>: <prop_value>
#         <var_name>: <var_value>  # additional variables for host
#     vars:
#       <var_name>: <var_value>  # additional variables for all hosts in group
#     children:
#       <group_name>:  # a child group
#         hosts: ...
#         vars: ...
#         children: ...

# Regexp for valid Ansible variable names, host aliases, group names
ANSIBLE_NAME_PATTERN = r"^[a-zA-Z_][a-zA-Z_0-9]*$"

# Valid Ansible variable types (using JSON schema type names)
ANSIBLE_VARTYPES = [
    "object", "array", "string", "integer", "number", "boolean", "null"
]

# Regexp for valid Ansible hosts (DNS name, IP address, or host alias)
# Note: Host name ranges like in Ansible are not supported.
ANSIBLE_HOST_PATTERN = r"^[a-zA-Z_0-9:\.\-]+$"

# Regexp for valid HMC CPC names
CPCNAME_PATTERN = r"^[A-Z][A-Z0-9_]*$"

# Regexp for valid HMC resource property names (with underscores instead of
# hyphens)
PROPNAME_PATTERN = r"^[a-z][a-z0-9_]*$"

# JSON schema for content of an HMC inventory file in YAML format
HMC_INVENTORY_FILE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "JSON schema for an HMC inventory file in YAML format",
    "definitions": {
        "HostVars": {
            "description": "Variables for the host",
            "type": ["object", "null"],
            "additionalProperties": False,
            "properties": {
                "description": {
                    "description": "Short description of the HMC. "
                                   "Optional, default: empty.",
                    "type": "string",
                },
                "contact": {
                    "description": "Name of technical contact for the HMC. "
                                   "Optional, default: empty.",
                    "type": "string",
                },
                "access_via": {
                    "description": "Preconditions to reach the network "
                                   "of the HMC. "
                                   "Optional, default: empty.",
                    "type": "string",
                },
                "ansible_host": {
                    "description": "For real HMCs: DNS host name or IP "
                                   "address of the HMC or of a list of "
                                   "redundant HMCs. "
                                   "Mandatory for real HMCs.",
                    "type": ["string", "array"],
                },
                "mock_file": {
                    "description": "For mocked HMCs: Path name of HMC mock "
                                   "file, relative to the directory of this "
                                   "HMC inventory file. "
                                   "Mandatory for mocked HMCs.",
                    "type": "string",
                },
                "cpcs": {
                    "description": "CPCs managed by this HMC that are to be "
                                   "tested. If omitted or None, no CPCs are "
                                   "tested.",
                    "type": "object",
                    "additionalProperties": False,
                    "patternProperties": {
                        # CPC name:
                        CPCNAME_PATTERN: {
                            "description":
                                "Expected CPC properties. Used for basic "
                                "classification of the CPC, e.g. 'dpm-mode', "
                                "'machine-type', 'machine-model'.",
                            "type": "object",
                            "additionalProperties": False,
                            "patternProperties": {
                                # CPC property name (with underscores):
                                PROPNAME_PATTERN: {
                                    "description": "Expected property value",
                                    "type": ANSIBLE_VARTYPES,
                                },
                            },
                        },
                    },
                },
            },
            "patternProperties": {
                # Additional variables for the host.
                # Variable name:
                ANSIBLE_NAME_PATTERN: {
                    "description": "Variable value",
                    "type": ANSIBLE_VARTYPES,
                },
            },
        },
        "GroupVars": {
            "description":
                "Additional variables for all hosts in the group",
            "type": ["object", "null"],
            "additionalProperties": False,
            "patternProperties": {
                # Variable name:
                ANSIBLE_NAME_PATTERN: {
                    "description": "Variable value",
                    "type": ANSIBLE_VARTYPES,
                },
            },
        },
        "Hosts": {
            "description": "Hosts in the group",
            "type": ["object", "null"],
            "additionalProperties": False,
            "patternProperties": {
                # Host DNS name, IP address, or alias:
                ANSIBLE_HOST_PATTERN: {
                    "$ref": "#/definitions/HostVars"
                },
            },
        },
        "Children": {
            "description": "Child groups of a group",
            "type": ["object", "null"],
            "additionalProperties": False,
            "patternProperties": {
                # Child group name:
                ANSIBLE_NAME_PATTERN: {
                    "description": "Content of the child group",
                    "type": ["object", "null"],
                    "additionalProperties": False,
                    "properties": {
                        "hosts": {
                            "$ref": "#/definitions/Hosts"
                        },
                        "vars": {
                            "$ref": "#/definitions/GroupVars"
                        },
                        "children": {
                            "$ref": "#/definitions/Children"
                        },
                    },
                },
            },
        },
    },
    "description": "Top-level group named 'all'",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "all",
    ],
    "properties": {
        # Top-level group name:
        "all": {
            "description": "Content of the top-level group",
            "type": ["object", "null"],
            "additionalProperties": False,
            "properties": {
                "hosts": {
                    "$ref": "#/definitions/Hosts"
                },
                "vars": {
                    "$ref": "#/definitions/GroupVars"
                },
                "children": {
                    "$ref": "#/definitions/Children"
                },
            },
        },
    },
}


class HMCInventoryFileError(Exception):
    """
    An error in the :ref:`HMC inventory file`.
    """
    pass


class HMCInventoryFile:
    """
    Encapsulation of an :ref:`HMC inventory file` in YAML format.
    """

    def __init__(self, filepath):
        self._filepath = filepath
        self._data = OrderedDict()  # File content
        self._load_file()

    def _load_file(self):
        """
        Load and validate the :ref:`HMC inventory file` in YAML format.
        """
        try:
            # pylint: disable=unspecified-encoding
            with open(self._filepath) as fp:
                try:
                    data = yaml.load(
                        fp, Loader=yamlloader.ordereddict.SafeLoader)
                except (yaml.parser.ParserError,
                        yaml.scanner.ScannerError) as exc:
                    new_exc = HMCInventoryFileError(
                        "Invalid YAML syntax in HMC inventory file "
                        f"{self._filepath!r}: {exc.__class__.__name__} {exc}")
                    new_exc.__cause__ = None
                    raise new_exc  # HMCInventoryFileError
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                new_exc = HMCInventoryFileError(
                    f"The HMC inventory file {self._filepath!r} was not found")
                new_exc.__cause__ = None
                raise new_exc  # HMCInventoryFileError
            raise

        try:
            jsonschema.validate(data, HMC_INVENTORY_FILE_SCHEMA)
        except jsonschema.exceptions.ValidationError as exc:
            elem = '.'.join(str(e) for e in exc.absolute_path)
            schemaitem = '.'.join(str(e) for e in exc.absolute_schema_path)
            new_exc = HMCInventoryFileError(
                "Invalid data format in HMC inventory file "
                f"{self._filepath}: {exc.message}; "
                f"Offending element: {elem}; "
                f"Schema item: {schemaitem}; "
                f"Validator: {exc.validator}={exc.validator_value}")
            new_exc.__cause__ = None
            raise new_exc  # HMCInventoryFileError

        self._data.update(data)

    def __repr__(self):
        return (
            "HMCVaultFile("
            f"filepath={self.filepath!r}, "
            f"data={self.data!r})")

    @property
    def filepath(self):
        """
        string: Path name of the :ref:`HMC inventory file`.
        """
        return self._filepath

    @property
    def data(self):
        """
        :class:`~py:collections.OrderedDict`: Content of the
        :ref:`HMC inventory file`, as nested
        :class:`~py:collections.OrderedDict` and
        :class:`~py:list` objects.
        """
        return self._data
