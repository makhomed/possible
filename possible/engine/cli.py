
__all__ = ['main']

import argparse
import sys

from .app import application
from .config import Config
from .exceptions import PossibleError, PossibleConfigError, PossibleInventoryError, PossiblePosfileError, PossibleApplicationError, PossibleRuntimeError
from .inventory import Inventory
from .posfile import Posfile
from .utils import debug, eprint
from possible import __version__


def parse_args(*, config, args):
    parser = argparse.ArgumentParser(prog='pos', description="possible is configuration management tool")
    if not isinstance(config.verbosity, int):
        config_verbosity = 0
        default_verbosity = ''
    else:
        config_verbosity = config.verbosity
        default_verbosity = ', default: -'+'v'*config.verbosity
    default_task = "" if not config.task else f" (default: {config.task})"
    default_args = "" if not config.args else f" (default: {config.args})"
    parser.add_argument('task', action="store", nargs='?', default=config.task, help=f"task to execute{default_task}")
    parser.add_argument('args', action="store", nargs='*', default=config.args, help=f"args for task{default_args}")
    parser.add_argument('-V', '--version', action='version', version=f'possible {__version__}', help="show program's version and exit")
    parser.add_argument('-C', '--dump-config', dest='dump_config', action="store_true", help="show config dump and exit")
    parser.add_argument('-I', '--dump-inventory', dest='dump_inventory', action="store_true", help="show inventory dump and exit")
    parser.add_argument('-A', '--dump-vars', dest='dump_vars', action="store_true", help="show host vars dump and exit")
    parser.add_argument('-L', '--list', dest='_list', action="store_true", help="show list of available tasks and exit")
    parser.add_argument('-v', '--verbose', dest='verbosity', default=config_verbosity, action="count", help=f"verbose mode (-vv or -vvv for more{default_verbosity})")
    parser.add_argument('-D', '--debug', dest='debug', action="store_true", help="debug mode")
    parser.add_argument('-w', '--workdir', dest='workdir', default=config.workdir, help="specify work dir to use (default: search up from '.')")
    parser.add_argument('-c', '--config', dest='config', default=config.config, help="specify config file to use (default: %(default)s)")
    parser.add_argument('-i', '--inventory', dest='inventory', default=config.inventory, help="specify inventory dir to use (default:  %(default)s)")
    parser.add_argument('-p', '--posfile', dest='posfile', default=config.posfile, help="specify posfile to use (default: %(default)s)")
    parser.add_argument('-t', '--threads', dest='threads', default=config.threads, type=int, help="specify number of threads to use (default: %(default)s)")
    args = parser.parse_args(args)
    if not args.debug:
        debug.disable()
    return args


def parse_all():
    def sys_args_without_help():
        out = []
        for arg in sys.argv[1:]:
            if arg == '-h' or arg == '--help':
                continue
            if arg.startswith('--') or not arg.startswith('-'):
                out.append(arg)
            else:
                assert arg.startswith('-')
                filtered_arg = ''
                for char in arg:
                    if char == 'h':
                        continue
                    else:
                        filtered_arg += char
                out.append(filtered_arg)
        return out
    first_pass_args = parse_args(config=Config.undefined_config(), args=sys_args_without_help())
    first_pass_args.verbosity = None # set default verbosity value after first run of parse_args()
    first_pass_config = Config(first_pass_args)
    args = parse_args(config=first_pass_config, args=sys.argv[1:])
    config = Config(args)
    inventory = Inventory(config)
    posfile = Posfile(config)
    if args.dump_config:
        print(config.dump(), file=sys.stdout, flush=True)
        sys.exit(0)
    if args.dump_inventory:
        print(inventory.dump(), file=sys.stdout, flush=True)
        sys.exit(0)
    if args.dump_vars:
        print(inventory.dump_vars(), file=sys.stdout, flush=True)
        sys.exit(0)
    if args._list:
        print(posfile.tasks(), file=sys.stdout, flush=True)
        sys.exit(0)
    return config, inventory, posfile

def main():
    try:
        sys.dont_write_bytecode = True
        config, inventory, posfile = parse_all()
        application.config = config
        application.inventory = inventory
        application.posfile = posfile
        application.run()
        sys.exit(0)
    except PossibleRuntimeError as e:
        debug.enable()
        eprint(e)
        sys.exit(6)
    except PossibleApplicationError as e:
        eprint(e)
        sys.exit(5)
    except PossiblePosfileError as e:
        eprint(e)
        sys.exit(4)
    except PossibleInventoryError as e:
        eprint(e)
        sys.exit(3)
    except PossibleConfigError as e:
        eprint(e)
        sys.exit(2)
    except PossibleError as e:
        eprint(e)
        sys.exit(1)
    except KeyboardInterrupt:
        eprint("User interrupted execution")
        sys.exit(101)
    except Exception as e:
        debug.enable()
        eprint(e)
        sys.exit(100)