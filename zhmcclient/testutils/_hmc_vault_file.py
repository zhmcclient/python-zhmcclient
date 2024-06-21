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
Encapsulation of an HMC vault file in YAML format.

HMC vault files conform to the format of Ansible vault files in YAML
format and define specific variables for HMC authentication.
"""


from collections import OrderedDict
import errno
import yaml
import yamlloader
import jsonschema

__all__ = ['HMCVaultFileError', 'HMCVaultFile']

# Structure of an HMC vault file in YAML format:
#
#   hmc_auth:
#     <hmc_name>:  # DNS hostname, IP address, or nickname of HMC
#       userid: <userid>
#       password: <password>
#       verify: <verify>
#       ca_certs: <ca_certs>
#   <var_name>: <var_value>

# Regexp for valid Ansible variable names, HMC nicknames, group names
ANSIBLE_NAME_PATTERN = "^[a-zA-Z_][a-zA-Z_0-9]*$"

# Valid Ansible variable types (using JSON schema type names)
ANSIBLE_VARTYPES = [
    "object", "array", "string", "integer", "number", "boolean", "null"
]

# Regexp for valid Ansible hosts (DNS name, IP address, or HMC nickname)
# Note: Host name ranges like in Ansible are not supported.
ANSIBLE_HOST_PATTERN = r"^[a-zA-Z_0-9:\.\-]+$"

# JSON schema for content of an HMC vault file in YAML format
HMC_VAULT_FILE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "JSON schema for an HMC vault file in YAML format",
    "description": "HMC auth data and additional variables",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "hmc_auth",
    ],
    "properties": {
        "hmc_auth": {
            "description": "Auth data for the HMCs covered by this vault file",
            "type": ["object", "null"],
            "additionalProperties": False,
            "patternProperties": {
                # HMC nickname:
                ANSIBLE_HOST_PATTERN: {
                    "description": "Auth data for a single HMC",
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "userid",
                        "password",
                    ],
                    "properties": {
                        "userid": {
                            "description":
                                "Userid (username) for authenticating with the "
                                "HMC. Required.",
                            "type": "string",
                        },
                        "password": {
                            "description":
                                "Password for authenticating with the HMC. "
                                "Required.",
                            "type": "string",
                        },
                        "verify": {
                            "description":
                                "Verify the HMC certificate as specified in "
                                "'ca_certs'. Optional, default: True.",
                            "type": "boolean",
                            "default": True,
                        },
                        "ca_certs": {
                            "description":
                                "Path name of certificate file or certificate "
                                "directory to be used for verifying the HMC "
                                "certificate, or None. If None, the path name "
                                "in the 'REQUESTS_CA_BUNDLE' environment "
                                "variable, or the path name in the "
                                "'CURL_CA_BUNDLE' environment variable, or the "
                                "certificates in the Mozilla CA Certificate "
                                "List provided by the 'certifi' Python package "
                                "are used. Optional, default: None.",
                            "type": "string",
                            "default": None,
                        },
                    },
                },
            },
        },
    },
    "patternProperties": {
        # Variable name:
        ANSIBLE_NAME_PATTERN: {
            "description": "Variable value",
            "type": ANSIBLE_VARTYPES,
        },
    },
}


class HMCVaultFileError(Exception):
    """
    An error in the :ref:`HMC vault file`.
    """
    pass


class HMCVaultFile:
    """
    Encapsulation of an :ref:`HMC vault file` in YAML format.
    """

    def __init__(self, filepath):
        self._filepath = filepath
        self._data = OrderedDict()  # file content
        self._load_file()

    def _load_file(self):
        """
        Load and validate the :ref:`HMC vault file` in YAML format.
        """
        try:
            # pylint: disable=unspecified-encoding
            with open(self._filepath) as fp:
                try:
                    data = yaml.load(
                        fp, Loader=yamlloader.ordereddict.SafeLoader)
                except (yaml.parser.ParserError,
                        yaml.scanner.ScannerError) as exc:
                    new_exc = HMCVaultFileError(
                        "Invalid YAML syntax in HMC vault file "
                        f"{self._filepath!r}: {exc.__class__.__name__} {exc}")
                    new_exc.__cause__ = None
                    raise new_exc  # HMCVaultFileError
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                new_exc = HMCVaultFileError(
                    f"The HMC vault file {self._filepath!r} was not found")
                new_exc.__cause__ = None
                raise new_exc  # HMCVaultFileError
            raise

        try:
            jsonschema.validate(data, HMC_VAULT_FILE_SCHEMA)
        except jsonschema.exceptions.ValidationError as exc:
            elem = '.'.join(str(e) for e in exc.absolute_path)
            schemaitem = '.'.join(str(e) for e in exc.absolute_schema_path)
            new_exc = HMCVaultFileError(
                f"Invalid data format in HMC vault file {self._filepath}: "
                f"{exc.message}; "
                f"Offending element: {elem}; "
                f"Schema item: {schemaitem}; "
                f"Validator: {exc.validator}={exc.validator_value}")
            new_exc.__cause__ = None
            raise new_exc  # HMCVaultFileError

        self._data.update(data)

    def __repr__(self):
        return (
            "HMCVaultFile("
            f"filepath={self.filepath!r}, "
            f"data={self.data!r})")

    @property
    def filepath(self):
        """
        string: Path name of the :ref:`HMC vault file`.
        """
        return self._filepath

    @property
    def data(self):
        """
        :class:`~py:collections.OrderedDict`: Content of the
        :ref:`HMC vault file`, as nested
        :class:`~py:collections.OrderedDict` and
        :class:`~py:list` objects.
        """
        return self._data
