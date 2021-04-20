
__all__ = ['Config']

from pathlib import Path


class Config():
    def __init__(self, args):
        self.workdir = Path.cwd()
        self.args = args
        if args.env:
            self.env = args.env
        else:
            self.env = None

    @property
    def files(self): 
        return self.workdir / 'files'

    @property
    def templates(self): 
        return self.workdir / 'templates'
