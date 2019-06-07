
__all__ = ['Config']

import yaml
from pathlib import Path

from .exceptions import PossibleConfigError


class UndefinedValue:
    def __bool__(self):
        return False

class UndefinedConfig:
    def __getattr__(self, key):
        return UndefinedValue()
    def __contains__(self, key):
        return True


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
    def undefined_config():
        return UndefinedConfig()

    @staticmethod
    def is_defined(value):
        return not isinstance(value, UndefinedValue)

    @staticmethod
    def first_if_defined(value1, value2):
        if Config.is_defined(value1):
            return value1
        else:
            return value2

    @staticmethod
    def check_config(conf, config_filename):
        if 'workdir' in conf:
            raise PossibleConfigError(f"Bad config file '{config_filename}', property 'workdir' can't be defined here")

        if 'config' in conf:
            if not isinstance(conf['config'], str):
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'config' must be string type")
            if not conf['config'].endswith('.yaml'):
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'config' must have .yaml extension")
            if '/' in conf['config']:
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'config' must be relative filename")

        if 'posfile' in conf:
            if not isinstance(conf['posfile'], str):
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'posfile' must be string type")
            if not conf['posfile'].endswith('.py'):
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'posfile' must have .py extension")
            if '/' in conf['posfile']:
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'posfile' must be relative filename")

        if 'inventory' in conf:
            if not isinstance(conf['inventory'], str):
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'inventory' must be string type")
            if '/' in conf['inventory']:
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'inventory' must be relative dirname")

        if 'verbosity' in conf:
            if not isinstance(conf['verbosity'], int):
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'verbosity' must be int type")
            if conf['verbosity'] < 0 or conf['verbosity'] > 7:
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'verbosity' must be between 0 and 7")

        if 'thread' in conf:
            if not isinstance(conf['threads'], int):
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'threads' must be int type")
            if conf['threads'] < 1 or conf['threads'] > 1024:
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'threads' must be between 1 and 1024")

        if 'color' in conf:
            if not isinstance(conf['color'], bool):
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'color' must be bool type")

        if 'target' in conf:
            if conf['target'] is not None and not isinstance(conf['target'], str):
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'target' must be string type")

        if 'task' in conf:
            if conf['task'] is not None and not isinstance(conf['task'], str):
                raise PossibleConfigError(f"Bad config file '{config_filename}', property 'task' must be string type")

        for key in conf:
            if key not in DefaultConfig.__dict__:
                raise PossibleConfigError(f"Unknown property '{key}' in config file '{config_filename}'")


    @staticmethod
    def parse_config(config_filename):
        if config_filename.is_file():
            try:
                with open(config_filename) as config_file:
                    conf = yaml.safe_load(config_file)
                    if conf is None:
                        return dict()
                    elif isinstance(conf, dict):
                        Config.check_config(conf, config_filename)
                        return conf
                    else:
                        raise PossibleConfigError(f"Config file {config_filename} content must be yaml/json encoded dictionary, instead given:\n\n{conf}\n")
            except yaml.YAMLError as e:
                raise PossibleConfigError(f"Error parsing config: {e}")
        else:
            raise PossibleConfigError(f"Config file '{config_filename}' not exists")

    def __init__(self, args):
        workdir = Config.first_if_defined(args.workdir, None)
        if workdir is None:
            search_workdir = True
            workdir = Path.cwd()
        else:
            search_workdir = False
            workdir = Path(workdir)
        config = Config.first_if_defined(args.config, DefaultConfig.config)

        while True:
            config_filename = workdir / config
            if config_filename.is_file():
                break
            else:
                if search_workdir:
                    if workdir == Path('/'):
                        raise PossibleConfigError(f"Can't find config file '{config}' in '{Path.cwd()}' and all upper directories")
                    else:
                        workdir = workdir.parent
                else:
                    raise PossibleConfigError(f"Can't find config file '{config}' in '{workdir}' directory")

        conf = Config.parse_config(config_filename)
        if 'config' in conf:
            if len(conf) == 1:
                config = conf['config']
                second_config_filename = workdir / config
                second_conf = Config.parse_config(second_config_filename)
                if 'config' in second_conf:
                    raise PossibleConfigError(f"Property 'config' is not allowed in second-level config file '{second_config_filename}'")
                conf.update(second_conf)
            else:
                raise PossibleConfigError(f"Property 'config' present in first-level config file '{config_filename}', in this case no other properties allowed, but given:\n\n{conf}\n")

        self.workdir = workdir
        self.config = config

        if Config.is_defined(args.posfile):
            self.posfile = args.posfile
        else:
            self.posfile = conf.get('posfile', DefaultConfig.posfile)

        if Config.is_defined(args.inventory):
            self.inventory = args.inventory
        else:
            self.inventory = conf.get('inventory', DefaultConfig.inventory)

        if Config.is_defined(args.verbosity):
            self.verbosity = args.verbosity
        else:
            self.verbosity = conf.get('verbosity', DefaultConfig.verbosity)

        if Config.is_defined(args.threads):
            self.threads = args.threads
        else:
            self.threads = conf.get('threads', DefaultConfig.threads)

        if Config.is_defined(args.target):
            self.target = args.target
        else:
            self.target = conf.get('target', DefaultConfig.target)

        if Config.is_defined(args.task):
            self.task = args.task
        else:
            self.task = conf.get('task', DefaultConfig.task)

    def dump(self):
        temp_dict = dict(self.__dict__)
        temp_dict['workdir'] = str( temp_dict['workdir'])
        return yaml.dump(temp_dict)
