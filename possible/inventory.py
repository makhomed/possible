
__all__ = ['Inventory']

import re
import yaml
from pathlib import Path

from .exceptions import PossibleInventoryError


class Check:
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
        Check.ensure_valid_host_name(self.name)
        if isinstance(config, dict):
            self.host = config.pop('host', DefaultHost.host)
            Check.ensure_valid_host_name(self.host)
            self.user = config.pop('user', DefaultHost.user)
            Check.ensure_valid_user_name(self.user)
            self.port = config.pop('port', DefaultHost.port)
            Check.ensure_valid_port_number(self.port)
            self.password = config.pop('password', DefaultHost.password)
            Check.ensure_valid_password(self.password)
            self.sudo_password = config.pop('sudo_password', DefaultHost.sudo_password)
            Check.ensure_valid_password(self.sudo_password)
            if config:
                raise PossibleInventoryError(f"Bad host {name} configuration: {config}")
        else:
                raise PossibleInventoryError(f"Bad host {name} configuration: {config}")

    def __str__(self):
        return self.__dict__.__str__()

    def __repr__(self):
        return self.__dict__.__repr__()


class Hosts():
    def __init__(self):
        self.__hosts = dict()

    def add(self, host):
        if host.name in self.__hosts:
            raise PossibleInventoryError(f"Bad host '{host.name}', it is already defined in hosts")
        else:
            self.__hosts[host.name] = host

    def __getitem__(self, key):
        return self.__hosts.__getitem__(key)

    def __iter__(self):
        return self.__hosts.__iter__()

    def __contains__(self, item):
        return self.__hosts.__contains__(item)

    def __str__(self):
        return self.__hosts.__str__()

    def __repr__(self):
        return self.__hosts.__repr__()




class Group: pass

class Var: pass

class Inventory:
    def __init__(self, path):
        path = Path(path).resolve()
        if not path.exists() or not path.is_dir():
            raise PossibleInventoryError(f'Inventory directory {path} not exists')
        self.inventory_directory = path
        self.hosts_filename = path / 'hosts.yaml'
        self.parse_hosts()
        self.groups_filename = path / 'groups.yaml'
        self.vars_filename = path / 'vars.yaml'

    def parse_hosts(self):
        if self.hosts_filename.is_file():
            self.hosts = Hosts()
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

    def dump(self):
        inventory = dict()
        inventory['hosts'] = hosts = list()
        for host in self.hosts:
            temp_dict = dict()
            temp_dict[host] = self.hosts[host].__dict__
            hosts.append( temp_dict )

        return yaml.dump(inventory)


