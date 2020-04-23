
__all__ = ['SSH']

from possible.engine.utils import debug


class SSH:
    def __init__(self, host):
        self.host = host
