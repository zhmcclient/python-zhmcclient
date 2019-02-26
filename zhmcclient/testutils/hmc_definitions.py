# Copyright 2019 IBM Corp. All Rights Reserved.
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
Encapsulation of HMC definition file defining HMCs for zhmcclient end2end
tests.
"""

from __future__ import absolute_import

import os
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import errno
import yaml
import yamlordereddictloader

THIS_DIR = os.path.dirname(__file__)

DEFAULT_HMC_FILE = os.path.join('tests', 'hmc_definitions.yaml')
EXAMPLE_HMC_FILE = os.path.join('tests', 'example_hmc_definitions.yaml')


class HMCDefinitionFileError(Exception):
    """
    An error in the HMC definition file.
    """
    pass


class HMCDefinitionFile(object):
    """
    Encapsulation of the definitions in the HMC definition file.
    """

    def __init__(self, filepath=DEFAULT_HMC_FILE):
        self._filepath = filepath
        self._hmcs = OrderedDict()
        self._hmc_groups = OrderedDict()
        self._load_file()

    def _load_file(self):
        try:
            with open(self._filepath) as fp:
                try:
                    data = yaml.load(fp, Loader=yamlordereddictloader.Loader)
                except (yaml.parser.ParserError,
                        yaml.scanner.ScannerError) as exc:
                    raise HMCDefinitionFileError(
                        "Invalid YAML syntax in HMC definition file "
                        "{0!r}: {1} {2}".
                        format(self._filepath, exc.__class__.__name__, exc))
        except IOError as exc:
            if exc.errno == errno.ENOENT:
                raise HMCDefinitionFileError(
                    "The HMC definition file {0!r} was not found; "
                    "copy it from {1!r}".
                    format(self._filepath, EXAMPLE_HMC_FILE))
            else:
                raise
        else:
            if data is None:
                raise HMCDefinitionFileError(
                    "The HMC definition file {0!r} is empty".
                    format(self._filepath))
            if not isinstance(data, OrderedDict):
                raise HMCDefinitionFileError(
                    "The HMC definition file {0!r} must contain a "
                    "dictionary at the top level, but contains {1}".
                    format(self._filepath, type(data)))

            if 'hmcs' not in data:
                raise HMCDefinitionFileError(
                    "The HMC definition file {0!r} does not define a "
                    "'hmcs' item, but items: {1}".
                    format(self._filepath, data.keys()))
            hmcs = data.get('hmcs')
            if not isinstance(hmcs, OrderedDict):
                raise HMCDefinitionFileError(
                    "'hmcs' in HMC definition file {0!r} "
                    "must be a dictionary, but is a {1}".
                    format(self._filepath, type(hmcs)))
            self._hmcs.update(hmcs)

            hmc_groups = data.get('hmc_groups', OrderedDict())
            if not isinstance(hmc_groups, OrderedDict):
                raise HMCDefinitionFileError(
                    "'hmc_groups' in HMC definition file {0!r} "
                    "must be a dictionary, but is a {1}".
                    format(self._filepath, type(hmc_groups)))
            for hmc_nick in hmc_groups:
                visited_hmc_nicks = list()
                self._check_hmc_group(hmc_nick, hmc_groups, hmcs,
                                      visited_hmc_nicks)
            self._hmc_groups.update(hmc_groups)

    def _check_hmc_group(self, hmc_nick, hmc_groups, hmcs, visited_hmc_nicks):
        visited_hmc_nicks.append(hmc_nick)
        hmc_group = hmc_groups[hmc_nick]
        if not isinstance(hmc_group, list):
            raise HMCDefinitionFileError(
                "HMC group {0!r} in HMC definition file {1!r} "
                "must be a list, but is a {2}".
                format(hmc_nick, self._filepath, type(hmc_group)))
        for nick in hmc_group:
            if nick in visited_hmc_nicks:
                raise HMCDefinitionFileError(
                    "Circular reference: HMC group {0!r} in HMC "
                    "definition file {1!r} contains HMC group {2!r}, which "
                    "directly or indirectly contains HMC group {0!r}".
                    format(hmc_nick, self._filepath, nick))
            if not isinstance(nick, str):
                raise HMCDefinitionFileError(
                    "Item {0!r} in HMC group {1!r} in HMC definition file "
                    "{2!r} must be a string, but is a {3}".
                    format(nick, hmc_nick, self._filepath, type(nick)))
            if nick in hmc_groups:
                self._check_hmc_group(
                    nick, hmc_groups, hmcs, visited_hmc_nicks)
            elif nick not in hmcs:
                raise HMCDefinitionFileError(
                    "Item {0!r} in HMC group {1!r} in HMC definition file "
                    "{2!r} is not a known HMC or HMC group".
                    format(nick, hmc_nick, self._filepath))

    @property
    def filepath(self):
        """
        Path name of the HMC definition file.
        """
        return self._filepath

    def get_hmc(self, nickname):
        """
        Return a `HMCDefinition` object for the HMC with the specified
        nickname.
        """
        try:
            hmc_dict = self._hmcs[nickname]
        except KeyError:
            raise ValueError(
                "HMC with nickname {0!r} not found in HMC definition file "
                "{1!r}".format(nickname, self._filepath))
        return HMCDefinition(nickname, hmc_dict, self._filepath)

    def list_hmcs(self, nickname):
        """
        Return a list of `HMCDefinition` objects for the hmcs in the HMC group
        with the specified nickname, or the single HMC with the specified
        nickname.
        """
        if nickname in self._hmcs:
            return [self.get_hmc(nickname)]
        elif nickname in self._hmc_groups:
            hmc_list = list()  # of HMCDefinition objects
            hmc_nick_list = list()  # of HMC nicknames
            for item_nick in self._hmc_groups[nickname]:
                for hd in self.list_hmcs(item_nick):
                    if hd.nickname not in hmc_nick_list:
                        hmc_list.append(hd)
                        hmc_nick_list.append(hd.nickname)
            return hmc_list
        else:
            raise ValueError(
                "HMC group or HMC with nickname {0!r} not found in "
                "HMC definition file {1!r}".
                format(nickname, self._filepath))

    def list_all_hmcs(self):
        """
        Return a list of all HMCs in the HMC definition file.
        """
        return [self.get_hmc(nickname) for nickname in self._hmcs]


class HMCDefinition(object):
    """
    Encapsulation of a single HMC definition (e.g. from an HMC definition
    file).

    An HMC definition contains information needed to use the WS API of the HMC
    (such as its IP address and credentials, and any networking preconditions
    for reaching the IP address), some organizational information (such as a
    description and a technical contact), and some information about the CPCs
    managed by the HMC (such as whether they are in DPM mode).
    """

    def __init__(self, nickname, hmc_dict, hmc_filepath):
        self._nickname = nickname
        self._hmc_filepath = hmc_filepath
        self._description = hmc_dict.get('description', '')
        self._contact = hmc_dict.get('contact', '')
        self._access_via = hmc_dict.get('access_via', '')
        self._faked_hmc_file = hmc_dict.get('faked_hmc_file', None)
        if self._faked_hmc_file:
            self._hmc_host = None
            self._hmc_userid = None
            self._hmc_password = None
        else:
            self._hmc_host = self._required_attr(
                hmc_dict, 'hmc_host', nickname)
            self._hmc_userid = self._required_attr(
                hmc_dict, 'hmc_userid', nickname)
            self._hmc_password = self._required_attr(
                hmc_dict, 'hmc_password', nickname)
        self._cpcs = hmc_dict.get('cpcs', dict())

    def _required_attr(self, hmc_dict, attr_name, nickname):
        try:
            return hmc_dict[attr_name]
        except KeyError:
            raise HMCDefinitionFileError(
                "Required HMC attribute is missing in definition of HMC "
                "{0}: {1}".format(nickname, attr_name))

    def __repr__(self):
        return "HMCDefinition(" \
            "nickname={s.nickname!r}, " \
            "hmc_filepath={s.hmc_filepath!r}, " \
            "description={s.description!r}, " \
            "contact={s.contact!r}, " \
            "access_via={s.access_via!r}, " \
            "faked_hmc_file={s.faked_hmc_file!r}, " \
            "hmc_host={s.hmc_host!r}, " \
            "hmc_userid={s.hmc_userid!r}, " \
            "hmc_password=..., " \
            "cert_file={s.cert_file!r}, " \
            "cpcs={s.cpcs!r})". \
            format(s=self)

    @property
    def nickname(self):
        """
        Nickname of the HMC.
        """
        return self._nickname

    @property
    def hmc_filepath(self):
        """
        Path name of the HMC definition file defining this HMC.
        """
        return self._hmc_filepath

    @property
    def description(self):
        """
        Short description of the HMC.
        """
        return self._description

    @property
    def contact(self):
        """
        Name of the technical contact of the HMC.
        """
        return self._contact

    @property
    def access_via(self):
        """
        Networking preconditions for reaching the IP address of the HMC
        (e.g. Boundary firewall, VPN connection).
        """
        return self._access_via

    @property
    def faked_hmc_file(self):
        """
        Path name of faked HMC file, defining a faked HMC with CPCs to be
        used for setting up the zhmcclient mock support.

        This property is `None` for real HMCs.
        """
        return self._faked_hmc_file

    @property
    def hmc_host(self):
        """
        IP address or hostname of the HMC.

        This property is `None` for faked HMCs.
        """
        return self._hmc_host

    @property
    def hmc_userid(self):
        """
        Userid for logging on to the HMC.

        This property is `None` for faked HMCs.
        """
        return self._hmc_userid

    @property
    def hmc_password(self):
        """
        Password for logging on to the HMC.

        This property is `None` for faked HMCs.
        """
        return self._hmc_password

    @property
    def cpcs(self):
        """
        List of CPCs managed by the HMC.

        Each list item represents one CPC and is a dict with these keys:
        * 'name' (string): CPC name.
        * 'dpm' (bool): CPC is in DPM mode. None if not known.
        """
        return self._cpcs
