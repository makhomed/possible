
__all__ = ['Config']

import yaml
from pathlib import Path

from .exceptions import PossibleConfigError

class DefaultConfig:
    config = 'config.yaml'
    posfile = 'posfile.py'
    inventory = 'inventory'
    verbosity = 0
    threads = 1
    color = True
    target = None
    task = None

class Config():
    @staticmethod
    def only_public_members(source_dict):
        dest_dict = dict()
        for key in source_dict:
            if not key.startswith('_'):
                dest_dict[key]=source_dict[key]
        return dest_dict

    def __init__(self, config=DefaultConfig.config, args=None):
        default_config = config == DefaultConfig.config
        self.__dict__['__args'] = args
        self.__dict__['__config'] = Config.only_public_members(DefaultConfig.__dict__)
        self.__dict__['__config_filename'] = config = Path(config).resolve()
        if config.is_file():
            try:
                with open(config) as config_file:
                    self.__dict__['__config'].update(yaml.safe_load(config_file))
            except yaml.YAMLError as e:
                raise PossibleConfigError(f"Error parsing config: {e}")
        elif not default_config:
                raise PossibleConfigError(f"Config file '{config}' not exists")
        if args:
            self.config = args.config
            self.posfile = args.posfile
            self.inventory = args.inventory
            self.verbosity = args.verbosity
            self.threads = args.threads
            self.target = args.target
            self.task = args.task
        self.check_config()

    def check_config(self):
        config = self.__dict__['__config_filename']
        if not isinstance(self.config, str):
            raise PossibleConfigError("Property 'config' must be string type")
        if not self.config.endswith('.yaml'):
            raise PossibleConfigError("Property 'config' must have .yaml extension")
        if '/' in self.config:
            raise PossibleConfigError("Property 'config' must be relative filename")

        if not isinstance(self.posfile, str):
            raise PossibleConfigError("Property 'posfile' must be string type")
        if not self.posfile.endswith('.py'):
            raise PossibleConfigError("Property 'posfile' must have .py extension")
        if '/' in self.posfile:
            raise PossibleConfigError("Property 'posfile' must be relative filename")

        if not isinstance(self.inventory, str):
            raise PossibleConfigError("Property 'inventory' must be string type")
        if '/' in self.inventory:
            raise PossibleConfigError("Property 'inventory' must be relative dirname")

        if not isinstance(self.verbosity, int):
            raise PossibleConfigError("Property 'verbosity' must be int type")
        if self.verbosity < 0 or self.verbosity > 7:
            raise PossibleConfigError("Property 'verbosity' must be between 0 and 7")

        if not isinstance(self.threads, int):
            raise PossibleConfigError("Property 'threads' must be int type")
        if self.threads < 1 or self.threads > 1024:
            raise PossibleConfigError("Property 'threads' must be between 1 and 1024")

        if not isinstance(self.color, bool):
            raise PossibleConfigError("Property 'color' must be bool type")

        if self.target is not None and not isinstance(self.target, str):
            raise PossibleConfigError("Property 'target' must be string type")

        if self.task is not None and not isinstance(self.task, str):
            raise PossibleConfigError("Property 'task' must be string type")

        for key in self.__dict__['__config']:
            if key not in DefaultConfig.__dict__:
                raise PossibleConfigError(f"Unknown property '{key}' in config {config}")

    def __getitem__(self, key):
        return self.__dict__['__config'].__getitem__(key)

    def __setitem__(self, key, value):
        return self.__dict__['__config'].__setitem__(key, value)

    def __delitem__(self, key):
        return self.__dict__['__config'].__delitem__(key)

    def __getattr__(self, key):
        try:
            return self.__dict__['__config'].__getitem__(key)
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        return self.__dict__['__config'].__setitem__(key, value)

    def __delattr__(self, key):
        return self.__dict__['__config'].__delitem__(key)

    def __repr__(self):
        return self.__dict__['__config'].__repr__()

    def __str__(self):
        return self.__dict__['__config'].__str__()

