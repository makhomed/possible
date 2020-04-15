
__all__ = ['Context']

from .engine import hosts


class Context:

    def __init__(self, host):
        self.hlen= len(max(hosts, key=len))
        self.host = host

    def name(self, message):
        print(f"{self.host:{self.hlen}} *", message)

    def run(self, command):
        print(f"{self.host:{self.hlen}} * run:", command)

    def var(self, name):
        return 'value'

