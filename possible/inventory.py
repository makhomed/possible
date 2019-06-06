
__all__ = ['Inventory']

import re
import yaml
from pathlib import Path

from .exceptions import PossibleInventoryError


class HostChecks:
    @staticmethod
    def ensure_valid_host_name(name):
        if not isinstance(name, str):
            raise PossibleInventoryError(f"Bad host name '{name}', it must be string")
        elif not name:
            raise PossibleInventoryError(f"Bad host name '{name}', it can't be empty")
        elif name[-1] == '.':
            raise PossibleInventoryError(f"Bad host name '{name}', it can't end with dot")
        elif  len(name) >= 253:
            raise PossibleInventoryError(f"Bad host name '{name}', it is very long")
        for char in name:
            if not (char == '.' or char == '-' or char == '_' or char >= 'A' and char <= 'Z' or char >= 'a' and char <= 'z' or char >= '0' and char <= '9'):
                raise PossibleInventoryError(f"Bad host name '{name}', symbol '{char}' is not allowed")
        for label in name.split('.'):
            if len(label) > 63:
                raise PossibleInventoryError(f"Bad host name '{name}', label '{label}' is very long")

    @staticmethod
    def ensure_valid_user_name(name):
        if not isinstance(name, str):
            raise PossibleInventoryError(f"Bad user name '{name}', it must be string")
        elif not name:
            raise PossibleInventoryError(f"Bad user name '{name}', it can't be empty")
        elif  len(name) >= 32:
            raise PossibleInventoryError(f"Bad user name '{name}', it is very long")
        elif not re.fullmatch(r'^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,31}$', name):
            raise PossibleInventoryError(f"Bad user name '{name}', it contain not allowed symbols")

    @staticmethod
    def ensure_valid_port_number(port):
        if not isinstance(port, int):
            raise PossibleInventoryError(f"Bad port number '{port}', it must be integer")
        elif port < 1 or port > 65535:
            raise PossibleInventoryError(f"Bad port number '{port}', it must be between 1 and 65535")

    @staticmethod
    def ensure_valid_password(password):
        if password is None:
            return
        if not isinstance(password, str):
            raise PossibleInventoryError(f"Bad password '{password}', it must be string")
        elif not password:
            raise PossibleInventoryError(f"Bad password '{password}', it can't be empty")
        for char in password:
            if char < '\x20' or char > '\x7e':
                raise PossibleInventoryError(f"Bad password '{password}', symbol '{char}' is not allowed")

class DefaultHost:
        name = None
        host = None
        user = 'root'
        port = 22
        password = None
        sudo_password = None

class Host:
    def __init__(self, name, config):
        self.name = name
        self.groups = set()
        self.vars = dict()
        HostChecks.ensure_valid_host_name(self.name)
        if isinstance(config, dict):
            self.host = config.pop('host', DefaultHost.host)
            HostChecks.ensure_valid_host_name(self.host)
            self.user = config.pop('user', DefaultHost.user)
            HostChecks.ensure_valid_user_name(self.user)
            self.port = config.pop('port', DefaultHost.port)
            HostChecks.ensure_valid_port_number(self.port)
            self.password = config.pop('password', DefaultHost.password)
            HostChecks.ensure_valid_password(self.password)
            self.sudo_password = config.pop('sudo_password', DefaultHost.sudo_password)
            HostChecks.ensure_valid_password(self.sudo_password)
            if config:
                raise PossibleInventoryError(f"Bad host {name} configuration: {config}")
        else:
                raise PossibleInventoryError(f"Bad host {name} configuration: {config}")

    def _dict(self):
        return { 'name': self.name, 'host': self.host, 'user': self.user, 'port': self.port, 'password': self.password, 'sudo_password': self.sudo_password }

    def __str__(self):
        return self._dict().__str__()

    def __repr__(self):
        return self._dict().__repr__()

class Hosts():
    def __init__(self):
        self.__hosts = dict()

    def add(self, host):
        if host.name in self.__hosts:
            raise PossibleInventoryError(f"Bad host '{host.name}', it is already defined")
        else:
            self.__hosts[host.name] = host

    def __getitem__(self, key):
        return self.__hosts.__getitem__(key)

    def __iter__(self):
        return self.__hosts.__iter__()

    def __len__(self):
        return self.__hosts.__len__()

    def __contains__(self, item):
        return self.__hosts.__contains__(item)

    def __str__(self):
        return self.__hosts.__str__()

    def __repr__(self):
        return self.__hosts.__repr__()

class Group:
    def __init__(self, name):
        self.name = name
        self.members = set()
        self.hosts = set()

    def add(self, name):
        if name in self.members:
            raise PossibleInventoryError(f"Member '{name}' already added to group '{self.name}'")
        else:
            self.members.add(name)

    def __getitem__(self, key):
        return self.members.__getitem__(key)

    def __iter__(self):
        return self.members.__iter__()

    def __len__(self):
        return self.members.__len__()

    def __contains__(self, item):
        return self.members.__contains__(item)

    def __str__(self):
        return self.__dict__.__str__()

    def __repr__(self):
        return self.__dict__.__repr__()

class Groups:
    def __init__(self):
        self.__groups = dict()

    def add(self, group):
        if group.name in self.__groups:
            raise PossibleInventoryError(f"Bad group '{group.name}', it is already defined")
        else:
            self.__groups[group.name] = group

    def __getitem__(self, key):
        return self.__groups.__getitem__(key)

    def __iter__(self):
        return self.__groups.__iter__()

    def __len__(self):
        return self.__groups.__len__()

    def __contains__(self, item):
        return self.__groups.__contains__(item)

    def __str__(self):
        return self.__groups.__str__()

    def __repr__(self):
        return self.__groups.__repr__()


class ObjectVars:
    def __init__(self):
        self.__object_vars = dict()

    def add(self, obj, name, value):
        if name in self.__object_vars:
            raise PossibleInventoryError(f"Variable '{name}' already defined for {obj}")
        else:
            self.__object_vars[name] = value

    def __getitem__(self, key):
        return self.__object_vars.__getitem__(key)

    def __iter__(self):
        return self.__object_vars.__iter__()

    def __len__(self):
        return self.__object_vars.__len__()

    def __contains__(self, item):
        return self.__object_vars.__contains__(item)

    def __str__(self):
        return self.__object_vars.__str__()

    def __repr__(self):
        return self.__object_vars.__repr__()

class Vars:
    def __init__(self):
        self.__objects = dict()

    def add(self, obj, name, value):
        if obj not in self.__objects:
            self.__objects[obj] = ObjectVars()
        self.__objects[obj].add(obj, name, value)

    def __getitem__(self, key):
        return self.__objects.__getitem__(key)

    def __iter__(self):
        return self.__objects.__iter__()

    def __len__(self):
        return self.__objects.__len__()

    def __contains__(self, item):
        return self.__objects.__contains__(item)

    def __str__(self):
        return self.__objects.__str__()

    def __repr__(self):
        return self.__objects.__repr__()


class VarsPriority:
    def __init__(self):
        self._dict = dict()
        self._list = list()
        self._next = 0

    def _add(self, name):
        if name in self._dict:
            raise PossibleInventoryError(f"Bad vars file, unexpected duplicate entry '{name}'")
        else:
            self._dict[name] = self._next
            self._list.append(name)
            self._next = self._next + 1

    def add(self, name):
        if self._next == 0:
            if name == 'all':
                self._add(name)
            else:
                raise PossibleInventoryError(f"Bad vars file, first vars file entry must be for group 'all', not for '{name}'")
        else:
            self._add(name)

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    def __contains__(self, item):
        return self._dict.__contains__(item)

    def __str__(self):
        return self._list.__str__()

    def __repr__(self):
        return self._list.__repr__()


class Inventory:
    def __init__(self, path):
        self.all_group = Group('all')
        self.ungrouped_group = Group('ungrouped')
        self.hosts = Hosts()
        self.groups = Groups()
        self.groups.add(self.all_group)
        self.groups.add(self.ungrouped_group)
        self.vars = Vars()
        self.vars_priority = VarsPriority()

        path = Path(path).resolve()
        if not path.exists() or not path.is_dir():
            raise PossibleInventoryError(f'Inventory directory {path} not exists')
        self.inventory_directory = path
        self.hosts_filename = path / 'hosts.yaml'
        self.parse_hosts()
        self.groups_filename = path / 'groups.yaml'
        self.parse_groups()
        self.check_groups()
        self.create_ungrouped_group()
        self.set_groups_hosts_sets()
        self.vars_filename = path / 'vars.yaml'
        self.parse_vars()
        self.merge_vars()

    def parse_hosts(self):
        if self.hosts_filename.is_file():
            try:
                with open(self.hosts_filename) as hosts_file:
                    hosts = yaml.safe_load(hosts_file)
                    if hosts is None:
                        raise PossibleInventoryError(f"Hosts file {self.hosts_filename} is empty")
                    elif isinstance(hosts, list):
                        for entry in hosts:
                            if isinstance(entry, dict):
                                if len(entry) == 1:
                                    name = list(entry.keys())[0]
                                    self.all_group.add(name)
                                    self.hosts.add(Host(name, entry[name]))
                                else:
                                    raise PossibleInventoryError(f"Bad hosts file {self.hosts_filename}, invalid host fragment {entry} - it must be one entry dict")
                            else:
                                raise PossibleInventoryError(f"Bad hosts file {self.hosts_filename}, invalid host fragment {entry} - it must be dict type")
                    else:
                        raise PossibleInventoryError(f"Hosts file {self.hosts_filename} content must be list type, given:\n\n{hosts}\n")
            except yaml.YAMLError as e:
                raise PossibleInventoryError(f"Error hosts file config: {e}")
        else:
            raise PossibleInventoryError(f"Hosts file '{self.hosts_filename}' not exists")

    def parse_groups(self):
        if self.groups_filename.is_file():
            try:
                with open(self.groups_filename) as groups_file:
                    groups = yaml.safe_load(groups_file)
                    if groups is None:
                        raise PossibleInventoryError(f"Groups file {self.groups_filename} is empty")
                    elif isinstance(groups, list):
                        for entry in groups:
                            if isinstance(entry, dict):
                                if len(entry) == 1:
                                    name = list(entry.keys())[0]
                                    group = Group(name)
                                    self.groups.add(group)
                                    members = entry[name]
                                    if isinstance(members, list):
                                        for member in members:
                                            if isinstance(member, str):
                                                if member == 'all' or member == 'ungrouped':
                                                    raise PossibleInventoryError(f"Group '{member}' can't be used in group file")
                                                group.add(member)
                                            else:
                                                PossibleInventoryError(f"Bad groups file {self.groups_filename}, invalid group fragment {entry} - it must be one entry dict of list of strings")
                                    else:
                                        PossibleInventoryError(f"Bad groups file {self.groups_filename}, invalid group fragment {entry} - it must be one entry dict of list of strings")

                                else:
                                    raise PossibleInventoryError(f"Bad groups file {self.groups_filename}, invalid group fragment {entry} - it must be one entry dict")
                            else:
                                raise PossibleInventoryError(f"Bad groups file {self.groups_filename}, invalid group fragment {entry} - it must be dict type")
                    else:
                        raise PossibleInventoryError(f"Groups file {self.groups_filename} content must be list type, given:\n\n{groups}\n")
            except yaml.YAMLError as e:
                raise PossibleInventoryError(f"Error groups file config: {e}")
        else:
            raise PossibleInventoryError(f"Groups file '{self.groups_filename}' not exists")

    def check_groups_recursion(self):
        def recursive_check(group, seen):
            seen.add(group)
            for member in self.groups[group]:
                if member in self.groups:
                    if member in seen:
                        raise PossibleInventoryError(f"Bad groups file, unexpected recursive group '{member}'")
                    else:
                        recursive_check(member, seen)
        for group in self.groups:
            seen = set()
            recursive_check(group, seen)

    def check_groups(self):
        for name in self.hosts:
            if name in self.groups:
                raise PossibleInventoryError(f"Bad inventory, name '{member}' used as name for host and name for group")
        for group in self.groups:
            for member in self.groups[group]:
                if member not in self.hosts and member not in self.groups:
                    raise PossibleInventoryError(f"Bad groups file, unexpected member name '{member}' in group '{group}'")
        self.check_groups_recursion()

    def set_groups_hosts_sets(self):
        def set_groups_hosts(group_name, group):
            for member in group:
                if member in self.hosts:
                    self.hosts[member].groups.add(group_name)
                    self.groups[group_name].hosts.add(member)
                else:
                    set_groups_hosts(group_name, self.groups[member])
        for group_name in self.groups:
            set_groups_hosts(group_name, self.groups[group_name])

    def create_ungrouped_group(self):
        temp = self.all_group.members.copy()
        for group in self.groups:
            if group == 'all':
                continue
            for member in self.groups[group]:
                if member in temp:
                    temp.remove(member)
        for host in temp:
            self.ungrouped_group.add(host)

    def parse_vars(self):
        group_expected = True
        if self.vars_filename.is_file():
            try:
                with open(self.vars_filename) as vars_file:
                    vars = yaml.safe_load(vars_file)
                    if vars is None:
                        raise PossibleInventoryError(f"Vars file {self.vars_filename} is empty")
                    elif isinstance(vars, list):
                        for entry in vars:
                            if isinstance(entry, dict):
                                if len(entry) == 1:
                                    obj = list(entry.keys())[0]
                                    if obj not in self.hosts and obj not in self.groups:
                                        raise PossibleInventoryError(f"Bad vars file {self.vars_filename}, unexpected host/group name '{obj}'")
                                    if obj in self.hosts:
                                        group_expected = False
                                    if obj in self.groups:
                                        if not group_expected:
                                            raise PossibleInventoryError(f"Bad vars file {self.vars_filename}, unexpected group '{obj}' vars after host vars")
                                    self.vars_priority.add(obj)
                                    obj_vars = entry[obj]
                                    if isinstance(obj_vars, dict):
                                        for obj_var in obj_vars:
                                            value = obj_vars[obj_var]
                                            self.vars.add(obj, obj_var, value)
                                    else:
                                        PossibleInventoryError(f"Bad vars file {self.vars_filename}, invalid vars fragment {entry} - it must be one entry dict of dicts")

                                else:
                                    raise PossibleInventoryError(f"Bad vars file {self.vars_filename}, invalid vars fragment {entry} - it must be one entry dict")
                            else:
                                raise PossibleInventoryError(f"Bad vars file {self.vars_filename}, invalid vars fragment {entry} - it must be dict type")
                    else:
                        raise PossibleInventoryError(f"Vars file {self.vars_filename} content must be list type, given:\n\n{vars}\n")
            except yaml.YAMLError as e:
                raise PossibleInventoryError(f"Error vars file config: {e}")
        else:
            raise PossibleInventoryError(f"Vars file '{self.vars_filename}' not exists")

    def merge_vars(self):
        def copy_vars(from_name, to_host):
            host = self.hosts[to_host]
            for var in self.vars[from_name]:
                host.vars[var]= self.vars[from_name][var]
        for from_name in self.vars_priority:
            if from_name in self.groups:
                for to_host in self.groups[from_name].hosts:
                    copy_vars(from_name, to_host)
            else:
                to_host = from_name
                copy_vars(from_name, to_host)
        pass

    def dump(self):
        inventory = list()
        hosts = list()
        inventory.append({'hosts': hosts})
        for host in self.hosts:
            temp_dict = dict()
            temp_dict[host] = self.hosts[host]._dict()
            hosts.append(temp_dict)
        groups = list()
        inventory.append({'groups': groups})
        for group in self.groups:
            temp_dict = dict()
            temp_dict[group] = list(self.groups[group])
            groups.append(temp_dict)
        vars = list()
        inventory.append({'vars': vars})
        for obj in self.vars:
            temp_dict = dict()
            temp_dict[obj] = dict()
            for obj_var in self.vars[obj]:
                value = self.vars[obj][obj_var]
                temp_dict[obj][obj_var] = value
            vars.append(temp_dict)
        vars_priority = list()
        inventory.append({'vars_priority': vars_priority})
        for obj in self.vars_priority:
            temp_dict = dict()
            temp_dict[obj] = self.vars_priority[obj]
            vars_priority.append(temp_dict)
        hosts_groups = list()
        inventory.append({'hosts_groups': hosts_groups})
        for host in self.hosts:
            temp_dict = dict()
            temp_dict[host] = sorted(self.hosts[host].groups)
            hosts_groups.append(temp_dict)
        groups_hosts = list()
        inventory.append({'groups_hosts': groups_hosts})
        for group in self.groups:
            temp_dict = dict()
            temp_dict[group] = sorted(self.groups[group].hosts)
            groups_hosts.append(temp_dict)
        return yaml.dump(inventory)

    def dump_vars(self):
        hosts_vars = list()
        for host in sorted(self.hosts):
            temp_dict = dict()
            temp_dict[host] = self.hosts[host].vars
            hosts_vars.append(temp_dict)
        return yaml.dump(hosts_vars)
