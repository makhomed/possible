
__all__ = ['main']

import argparse
import sys

from .app import application
from .config import Config
from .exceptions import PossibleError, PossibleInventoryError, PossiblePosfileError, PossibleUserError, PossibleRuntimeError
from .inventory import Inventory
from .posfile import Posfile
from .utils import debug, eprint
from possible import __version__


def parse_args():
    parser = argparse.ArgumentParser(prog='pos', description="possible is configuration management tool")
    parser.add_argument('-v', '--version', action='version', version=__version__, help="show program's version and exit")
    parser.add_argument('-I', '--dump-inventory', dest='dump_inventory', action="store_true", help="show inventory dump and exit")
    parser.add_argument('-V', '--dump-vars', dest='dump_vars', action="store_true", help="show host vars dump and exit")
    parser.add_argument('-L', '--list', dest='list_tasks', action="store_true", help="show list of tasks and exit")
    parser.add_argument('-D', '--debug', dest='debug', action="store_true", help="run program in debug mode")
    parser.add_argument('task', action="store", nargs='?', metavar="TASK", help="task to execute")
    parser.add_argument('target', action="store", nargs='?', metavar="TARGET", help="target for task")
    return parser.parse_args()


def parse_all():
    args = parse_args()
    config = Config(args)
    posfile = Posfile(config)
    inventory = Inventory(config)
    if args.dump_inventory:
        print(inventory.dump(), file=sys.stdout, flush=True)
        sys.exit(0)
    if args.dump_vars:
        print(inventory.dump_vars(), file=sys.stdout, flush=True)
        sys.exit(0)
    if args.list_tasks or args.task is None and args.target is None:
        print(posfile.tasks(), file=sys.stdout, flush=True)
        sys.exit(0)
    return config, posfile, inventory

def main():
    try:
        sys.dont_write_bytecode = True
        config, posfile, inventory = parse_all()
        application.config = config
        application.posfile = posfile
        application.inventory = inventory
        application.run()
        sys.exit(0)
    except PossibleRuntimeError as e:
        debug.enable()
        eprint(e)
        sys.exit(5)
    except PossibleUserError as e:
        eprint(e)
        sys.exit(4)
    except PossiblePosfileError as e:
        eprint(e)
        sys.exit(3)
    except PossibleInventoryError as e:
        eprint(e)
        sys.exit(2)
    except PossibleError as e:
        debug.enable()
        eprint(e)
        sys.exit(1)
    except KeyboardInterrupt:
        eprint("User interrupted execution")
        sys.exit(101)
    except Exception as e:
        debug.enable()
        eprint(e)
        sys.exit(100)
