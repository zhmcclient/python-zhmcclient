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
HMC definition for zhmcclient end2end tests.
"""

from __future__ import absolute_import

__all__ = ['HMCDefinition']


class HMCDefinition(object):
    """
    A single HMC definition.

    An HMC definition contains information needed to use the WS API of a real
    HMC or to setup and use a mocked HMC, some organizational information about
    the HMC, and some information about the CPCs managed by the HMC that are to
    be tested. It can also contain arbitrary additional variables.
    """

    def __init__(self, nickname, description='', contact='', access_via='',
                 mock_file=None, host=None, userid=None,
                 password=None, verify=True, ca_certs=None,
                 cpcs=None, add_vars=None):
        """
        Parameters:

          nickname (string): Nickname of the HMC (DNS name, IP address, or
            host alias).

          description (string): Short description of the HMC.

          contact (string): Name of the technical contact of the HMC.

          access_via (string): Networking preconditions for reaching the HMC.

          mock_file (string): Path name of HMC mock file. This argument is used
            to detect whether the HMC is a real or mocked HMC: If `None`, it is
            a real HMC.

          host (string): IP address or DNS hostname of the real HMC.
            Ignored for mocked HMCs, must not be `None` for real HMCs.

          userid (string): Userid (username) for authenticating with the
            HMC. Ignored for mocked HMCs, must not be `None` for real HMCs.

          password (string): Password for authenticating with the HMC.
            Ignored for mocked HMCs, must not be `None` for real HMCs.

          verify (bool): Verify the HMC certificate as specified in
            `ca_certs`.
            Ignored for mocked HMCs, defaults to `True` for real HMCs.

          ca_certs (string): Path name of certificate file or certificate
            directory to be used for verifying the HMC certificate, or `None`.
            If `None`, the path name in the 'REQUESTS_CA_BUNDLE' environment
            variable, or the path name in the 'CURL_CA_BUNDLE' environment
            variable, or the certificates in the Mozilla CA Certificate List
            provided by the 'certifi' Python package are used.
            Ignored for mocked HMCs, defaults to `None` for real HMCs.

          cpcs (dict): CPCs managed by the HMC that are to be tested.
            If `None`, no CPCs are tested.

            * key: CPC name.
            * value: dict of expected CPC properties, using underscored
              property names. Used for basic classification of the CPC,
              e.g. 'dpm-mode', 'machine-type', 'machine-model'.

          add_vars (dict): Additional variables. The variable values can have
            arbitrary types.
        """
        assert nickname
        self._nickname = nickname
        self._description = description or ''
        self._contact = contact or ''
        self._access_via = access_via or ''
        self._mock_file = mock_file
        if self._mock_file:
            self._host = None
            self._userid = None
            self._password = None
            self._verify = None
            self._ca_certs = None
        else:
            # assert host
            # assert userid
            # assert password
            self._host = host
            self._userid = userid
            self._password = password
            self._verify = verify
            self._ca_certs = ca_certs
        self._cpcs = cpcs or {}
        self._add_vars = add_vars or {}

    def __repr__(self):
        return "HMCDefinition(" \
            "nickname={s.nickname!r}, " \
            "description={s.description!r}, " \
            "contact={s.contact!r}, " \
            "access_via={s.access_via!r}, " \
            "mock_file={s.mock_file!r}, " \
            "host={s.host!r}, " \
            "userid={s.userid!r}, " \
            "password=..., " \
            "verify={s.verify!r}, " \
            "ca_certs={s.ca_certs!r}, " \
            "verify_cert={s.verify_cert!r}, " \
            "cpcs={s.cpcs!r}, " \
            "add_vars={s.add_vars!r})". \
            format(s=self)

    @property
    def nickname(self):
        """
        string: Nickname of the HMC (exists only in this encapsulation class,
          not known by the HMC itself).
        """
        return self._nickname

    @property
    def description(self):
        """
        string: Short description of the HMC.
        """
        return self._description

    @property
    def contact(self):
        """
        string: Name of the technical contact of the HMC.
        """
        return self._contact

    @property
    def access_via(self):
        """
        string: Networking preconditions for reaching the HMC.

        For example, Boundary firewall or VPN connection.
        """
        return self._access_via

    @property
    def mock_file(self):
        """
        string: Path name of HMC mock file.

        An HMC mock file defines a mocked HMC based on the zhmcclient_mock
        support.

        This property indicates whether the HMC is a real or mocked HMC:
        If `None`, it is a real HMC, otherwise it is a mocked HMC.
        """
        return self._mock_file

    @property
    def host(self):
        """
        string: IP address or DNS hostname of the HMC.

        This property is used only for real HMCs and is `None` for mocked HMCs.
        """
        return self._host

    @property
    def userid(self):
        """
        string: Userid (username) for authenticating with the HMC.

        This property is used only for real HMCs and is `None` for mocked HMCs.
        """
        return self._userid

    @property
    def password(self):
        """
        string: Password for authenticating with the HMC.

        This property is used only for real HMCs and is `None` for mocked HMCs.
        """
        return self._password

    @property
    def verify(self):
        """
        bool: Verify the HMC certificate as specified in :attr:`ca_certs`.

        This property is used only for real HMCs and is `None` for mocked HMCs.
        """
        return self._verify

    @property
    def ca_certs(self):
        """
        string: Path name of certificate file or certificate directory to be
        used for verifying the HMC certificate, or `None`.

        If `None`, the path name in the 'REQUESTS_CA_BUNDLE' environment
        variable, or the path name in the 'CURL_CA_BUNDLE' environment
        variable, or the certificates in the Mozilla CA Certificate List
        provided by the 'certifi' Python package are used.

        This property is used only for real HMCs and is `None` for mocked HMCs.
        """
        return self._ca_certs

    @property
    def verify_cert(self):
        """
        bool or string: A combination of :attr:`verify` and
        :attr:`ca_certs` for direct use as the `verify_cert` parameter of
        :class:`zhmcclient.Session`.

        This property is used only for real HMCs and is `None` for mocked HMCs.
        """
        if self._ca_certs:
            return self._ca_certs
        return self._verify

    @property
    def cpcs(self):
        """
        dict: CPCs managed by the HMC that are to be tested.

        Each dict item represents one CPC:

        * key (string): CPC name.
        * value (dict): Dict with expected CPC properties (with underscores).
        """
        return self._cpcs

    @property
    def add_vars(self):
        """
        dict: Additional variables for the HMC definition.

        Each dict item represents one variable:

        * key (string): Variable name.
        * value (object): Variable value.
        """
        return self._add_vars
