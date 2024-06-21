# Copyright 2019,2021 IBM Corp. All Rights Reserved.
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
HMC definitions for zhmcclient end2end tests.
"""


import os

from ._hmc_inventory_file import HMCInventoryFile
from ._hmc_vault_file import HMCVaultFile
from ._hmc_definition import HMCDefinition

__all__ = ['print_hmc_definitions', 'hmc_definitions', 'HMCDefinitions',
           'HMCNoVaultError', 'HMCNotFound']

# Path name of user's home directory
HOME_DIR = os.path.expanduser("~")

# Default file names of HMC inventory and vault files in user's home directory.
# Keep in sync with Makefile.
DEFAULT_TESTINVENTORY_FN = '.zhmc_inventory.yaml'
DEFAULT_TESTVAULT_FN = '.zhmc_vault.yaml'

DEFAULT_TESTINVENTORY_FILE = os.path.join(HOME_DIR, DEFAULT_TESTINVENTORY_FN)
DEFAULT_TESTVAULT_FILE = os.path.join(HOME_DIR, DEFAULT_TESTVAULT_FN)

# Default group name or HMC nickname in HMC inventory file to test against.
# Keep in sync with Makefile.
DEFAULT_TESTHMC = 'default'


def hmc_definitions(load=True):
    """
    Return the list of HMC definitions to be used for testing.

    Parameters:

      load (bool): Load the HMC inventory and vault files. Otherwise, these
        files are not loaded. This is used to avoid a dependency on these
        files for normal zhmcclient users.
        If `None`, the 'TESTEND2END_LOAD' environment variable is used.

    Returns:

      list of :class:`zhmcclient.testutils.HMCDefinition`
    """
    hmcdefs = HMCDefinitions(load=load)
    hd_list = hmcdefs.list_hmcs(hmcdefs.testhmc)
    return hd_list


def print_hmc_definitions():
    """
    Print all available HMC definitions in the HMC inventory and vault files.
    """
    hmcdefs = HMCDefinitions()
    print("\nHMC definitions for end2end tests:")

    print(f"\nHMC inventory file: {hmcdefs.inventory_file}")
    print(f"HMC vault file: {hmcdefs.vault_file}")
    print(f"Default test group/nickname: {hmcdefs.testhmc}")

    print("\nHMCs in inventory file:")
    print("{:20s} {:24s} {:}".
          format("HMC nickname", "HMC host / mock file", "Description"))
    for hd in hmcdefs.list_all_hmcs():
        host = hd.mock_file or hd.host
        if isinstance(host, list):
            host = ','.join(host)
        print(f"{hd.nickname:20s} {str(host):24s} {hd.description}")

    print("\nGroups in inventory file:")
    print("Group name           HMCs in the group")
    for group_name in hmcdefs.list_all_group_names():
        hmc_names = ', '.join(
            [hd.nickname for hd in hmcdefs.list_hmcs(group_name)])
        print(f"{group_name:20s} {hmc_names}")


def _default(vars_tuple, key, default):
    """
    Return the key value from one of the dicts in vars_tuple, or the default.
    """
    for vars_dict in vars_tuple:
        if vars_dict and key in vars_dict:
            return vars_dict[key]
    return default


class HMCNoVaultError(Exception):
    """
    The :ref:`HMC vault file` does not have a corresponding entry for the HMC.
    """
    pass


class HMCNotFound(Exception):
    """
    The HMC group or nickname was not found in the :ref:`HMC inventory file`.
    """
    pass


class HMCDefinitions:
    """
    The HMC definitions in the :ref:`HMC inventory file` and their credentials
    in the :ref:`HMC vault file`.
    """

    def __init__(self, inventory_file=None, vault_file=None, testhmc=None,
                 load=None):
        """
        Parameters:

          inventory_file (string): Path name of HMC inventory file`.
            If `None`, the file specified in the 'TESTINVENTORY' environment
            variable or if not set, the default file ``~/.zhmc_inventory.yaml``
            is used.

          vault_file (string): Path name of HMC vault file.
            If `None`, the file specified in the 'TESTVAULT' environment
            variable or if not set, the default file ``~/.zhmc_vault.yaml``
            is used.

          testhmc (string): Group nickname or HMC nickname in HMC inventory file
            to test against.
            If `None`, the nickname specified in the 'TESTHMC' environment
            variable or if not set, the nickname "default" is used.

          load (bool): Load the HMC inventory and vault files. Otherwise, these
            files are not loaded. This is used to avoid a dependency on these
            files for normal zhmcclient users.
            If `None`, the 'TESTEND2END_LOAD' environment variable is used.

        Raises:

          zhmcclient.testutils.HMCInventoryFileError:
          zhmcclient.testutils.HMCVaultFileError:
          zhmcclient.testutils.HMCNoVaultError:
        """

        # The Sphinx build imports this module and the use of this function
        # in the hmc_definition() fixture along with the wildcard imports in
        # the testutils/__init__.py module causes this function to be executed
        # upon module import. Since there are no HMC inventory and vault files
        # when GitHub Actions or ReadTheDocs builds the documentation, the
        # boolean 'TESTEND2END_LOAD' env.var is used to enable the loading of
        # the files in these cases. This env.var needs to be set to 'true' in
        # the Makefile for end2end targets.
        if load is None:
            load = bool(os.getenv('TESTEND2END_LOAD'))

        if not load:
            self._inventory_file = None
            self._vault_file = None
            self._testhmc = None
            self._inventory = None
            self._vault = None
            self._hd_dict = {}
        else:
            self._inventory_file = inventory_file or os.getenv(
                'TESTINVENTORY', DEFAULT_TESTINVENTORY_FILE)
            self._vault_file = vault_file or os.getenv(
                'TESTVAULT', DEFAULT_TESTVAULT_FILE)
            self._testhmc = testhmc or os.getenv(
                'TESTHMC', DEFAULT_TESTHMC)

            self._inventory = HMCInventoryFile(self._inventory_file)
            self._vault = HMCVaultFile(self._vault_file)

            # All HMC definitions, represented as a flat set of groups
            # with their hosts. All variables are stored in the hosts.
            # The list methods create and return HMCDefinition objects
            # from this representation.
            # Dictionary structure:
            #   key: group name, value: dict of HMC definitions with:
            #     key: HMC nickname, value: dict of HMCDefinition attrs with:
            #       key: attr name, value: attr value
            self._hd_dict = {}

            # Update self._hd_dict from groups, starting with top-level groups
            self._init_groups(self._inventory.data, {})

            # Update self._hd_dict with propagated host properties
            self._propagate_groups(self._inventory.data)

            # Update self._hd_dict from HMC vault file
            self._add_vault_data(self._vault, self._inventory.filepath)

    def _init_groups(self, groups, inherited_vars):
        """
        Process groups from an HMC inventory filer.

        Parameters:

          groups (dict): The groups, as a data structure from the HMC inventory
            file. Key: group name, Value: dict with hosts/vars/children.
            At the top level, groups is a dict with a single item 'all'. Below
            that, groups is a dict with the items from the 'children' item.

          inherited_vars (dict): Additional variables inherited from parents.
        """
        for group_name, group_dict in groups.items():
            if not group_dict:
                continue
            group_vars = dict(inherited_vars)
            group_vars.update(group_dict.get('vars') or {})
            self._init_group(group_name, group_dict, group_vars)
            child_groups = group_dict.get('children') or {}
            self._init_groups(child_groups, group_vars)

    def _init_group(self, group_name, group_dict, inherited_vars):
        """
        Process a single group from an HMC inventory file.

        Parameters:

          group_name (string): Name of the group.

          group_dict (dict): The group, as a dict with hosts/vars/children.

          inherited_vars (dict): Additional variables inherited from parents.
        """

        _host_dict = {}
        hosts = group_dict.get('hosts') or {}
        for nickname, host_vars in hosts.items():

            combined_vars = dict(inherited_vars)
            if host_vars:
                combined_vars.update(host_vars)

            description = combined_vars.pop('description', '')
            contact = combined_vars.pop('contact', '')
            access_via = combined_vars.pop('access_via', '')
            mock_file = combined_vars.pop('mock_file', None)
            ansible_host = combined_vars.pop('ansible_host', None)
            cpcs = combined_vars.pop('cpcs', None)
            add_vars = combined_vars

            _host_dict[nickname] = dict(
                description=description, contact=contact, access_via=access_via,
                mock_file=mock_file, ansible_host=ansible_host, cpcs=cpcs,
                add_vars=add_vars)

        self._hd_dict[group_name] = _host_dict

    def _propagate_groups(self, groups, parent_hosts=None):
        """
        Propagate host properties of groups to their child groups.

        Parameters:

          groups (dict): The groups, as a data structure from the HMC inventory
            file. Key: group name, Value: dict with hosts/vars/children.
            At the top level, groups is a dict with a single item 'all'. Below
            that, groups is a dict with the items from the 'children' item.

          parent_hosts (dict): The parent hosts of the groups, as a data
            structure from the HMC inventory file, or None for top level.
            Key: host nickname, Value: dict with host attributes.
        """
        for group_name, group_dict in groups.items():

            if not group_dict:
                continue

            self._propagate_group(group_name, group_dict, parent_hosts)

            child_groups = group_dict.get('children') or {}
            hosts = group_dict.get('hosts') or {}
            self._propagate_groups(child_groups, hosts)

    def _propagate_group(self, group_name, group_dict, parent_hosts):
        """
        Propagate host properties of a group to its hosts.

        Parameters:

          group_name (string): Name of the group.

          group_dict (dict): The group, as a dict with hosts/vars/children.

          parent_hosts (dict): The parent hosts of the group, as a data
            structure from the HMC inventory file, or None for top level.
            Key: host nickname, Value: dict with host attributes.
        """
        if parent_hosts is None:
            parent_hosts = {}

        hosts = group_dict.get('hosts') or {}
        for nickname, host_vars in hosts.items():

            try:
                parent_vars = parent_hosts[nickname]
            except KeyError:
                parent_vars = {}

            if host_vars is not None:
                host_vars_new = dict(host_vars)
            else:
                host_vars_new = {}

            if 'description' in parent_vars:
                host_vars_new.setdefault(
                    'description', parent_vars['description'])
            if 'contact' in parent_vars:
                host_vars_new.setdefault(
                    'contact', parent_vars['contact'])
            if 'access_via' in parent_vars:
                host_vars_new.setdefault(
                    'access_via', parent_vars['access_via'])
            if 'ansible_host' in parent_vars:
                host_vars_new.setdefault(
                    'ansible_host', parent_vars['ansible_host'])
            if 'mock_file' in parent_vars:
                host_vars_new.setdefault(
                    'mock_file', parent_vars['mock_file'])
            if 'cpcs' in parent_vars:
                host_vars_new.setdefault(
                    'cpcs', parent_vars['cpcs'])
            if 'add_vars' in parent_vars:
                host_vars_new.setdefault(
                    'add_vars', parent_vars['add_vars'])

            # The vault file variables are not in parent_vars and cannot
            # be propagated (they are defined once in the vault file).

            self._hd_dict[group_name][nickname].update(host_vars_new)

    def _add_vault_data(self, hmc_vault, inv_file):
        """
        Add data from HMC vault file to each host of all groups.

        Parameters:

          hmc_vault (HMCVault): Content of HMC vault file.

          inv_file (string): Path name of HMV inventory file (for messages).

        Raises:

          HMCNoVaultError: No cprresponding entry in HMC vault file.
        """
        auth = hmc_vault.data['hmc_auth'] or {}
        for group_dict in self._hd_dict.values():
            for nickname, host_vars in group_dict.items():

                try:
                    auth_vars = auth[nickname]
                except KeyError:
                    new_exc = HMCNoVaultError(
                        f"HMC {nickname!r} defined in HMC inventory file "
                        f"{inv_file} has no corresponding entry in HMC "
                        f"vault file {hmc_vault.filepath}")
                    new_exc.__cause__ = None
                    raise new_exc  # HMCNoVaultError

                # userid and password are required by the JSON schema
                host_vars['userid'] = auth_vars['userid']
                host_vars['password'] = auth_vars['password']
                host_vars['verify'] = auth_vars.get('verify', True)
                host_vars['ca_certs'] = auth_vars.get('ca_certs', None)

    def __repr__(self):
        return (
            "HMCDefinitions("
            f"inventory_file={self.inventory_file!r}, "
            f"vault_file={self.vault_file!r}, "
            f"testhmc={self.testhmc!r}, "
            f"group_names={self.group_names!r})")

    @property
    def inventory_file(self):
        """
        string: Path name of HMC inventory file.
        """
        return self._inventory_file

    @property
    def vault_file(self):
        """
        string: Path name of HMC vault file.
        """
        return self._vault_file

    @property
    def testhmc(self):
        """
        string: HMC group or single HMC nickname to be tested.
        """
        return self._testhmc

    @property
    def group_names(self):
        """
        list of string: The names of the HMC groups in the HMC inventory file.
        """
        return list(self._hd_dict.keys())

    def list_hmcs(self, name=None):
        """
        Return a list of :class:`HMCDefinition` objects in the HMC inventory
        file, for the specified HMC group or single HMC nickname.

        The path names in the :attr:`HMCDefinition.mock_file` property are
        absolute path names, whereby any relative path names in the HMC
        inventory file have been interpreted relative to the directory of
        the HMC inventory file.

        Parameters:

          name (string): Name of an HMC group or nickname of a single HMC in the
            HMC inventory file. If `None`, the default group or nickname
            defined in :attr:`HMCDefinitions.testhmc` is used.

        Returns:

          list of :class:`HMCDefinition`: The specified HMCs in the HMC
            inventory file.

        Raises:

          zhmcclient.testutils.HMCNotFound: HMC group or nickname not found.
        """
        if not self._hd_dict:
            return []

        if name is None:
            name = self._testhmc

        # Try to find a group with this name
        try:
            host_dict = self._hd_dict[name]
        except KeyError:
            # Try to find a single HMC with this nickname in group 'all'
            all_host_dict = self._hd_dict['all']
            for nickname, host_vars in all_host_dict.items():
                if nickname == name:
                    host_dict = {name: host_vars}
                    break
            else:
                new_exc = HMCNotFound(
                    f"HMC group or nickname {name!r} not found in HMC "
                    f"inventory file {self._inventory_file}")
                new_exc.__cause__ = None
                raise new_exc  # HMCNotFound

        hd_list = []
        for nickname, host_vars in host_dict.items():

            description = host_vars.get('description', '')
            contact = host_vars.get('contact', '')
            access_via = host_vars.get('access_via', '')
            mock_file = host_vars.get('mock_file', None)
            userid = host_vars.get('userid', None)
            password = host_vars.get('password', None)
            verify = host_vars.get('verify', None)
            ca_certs = host_vars.get('ca_certs', None)
            cpcs = host_vars.get('cpcs', None)
            add_vars = host_vars.get('add_vars', None)

            if mock_file:
                # The host will be set from the 'host' attribute in the
                # mock file. Since that file is read only later, we set
                # the HMC definition's host to None, for now.
                host = None
            else:
                # If ansible_host was set, it is always used, and otherwise
                # the HMC nickname is used as a DNS name or IP address.
                ansible_host = host_vars.get('ansible_host')
                # Note: ansible_host may be a string or list of strings.
                host = ansible_host or nickname

            # Make relative mock_file relative to inventory file
            if mock_file and not os.path.isabs(mock_file):
                mock_file = os.path.join(
                    os.path.dirname(self._inventory_file), mock_file)

            hd = HMCDefinition(
                nickname=nickname, description=description,
                contact=contact, access_via=access_via, mock_file=mock_file,
                host=host, userid=userid, password=password, verify=verify,
                ca_certs=ca_certs, cpcs=cpcs, add_vars=add_vars)

            hd_list.append(hd)

        return hd_list

    def list_all_hmcs(self):
        """
        List all HMCs in the HMC inventory file.

        Returns:

          list of :class:`HMCDefinition`: All HMCs in the HMC inventory file.
        """
        return self.list_hmcs('all')

    def list_all_group_names(self):
        """
        List all group names in the HMC inventory file.

        Returns:

          list of string: All group names in the HMC inventory file.
        """
        return list(self._hd_dict.keys())
