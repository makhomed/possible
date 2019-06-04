
__all__ = ['Inventory']

from pathlib import Path

from .exceptions import PossibleInventoryError

class Host: pass

class Group: pass

class Var: pass

class Inventory:
    def __init__(self, path):
        if path is None:
            path = Path.cwd().joinpath('inventory')
        path = Path(path).resolve()
        if not path.exists() or not path.is_dir():
            raise PossibleInventoryError(f'Inventory directory {path} not exists')
        self.__path = path

