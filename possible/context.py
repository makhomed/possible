
__all__ = ['Context']

from possible.engine import _hosts


class Context:

    def __init__(self, host):
        self.hlen = len(max(_hosts, key=len))
        self.host = host

    def name(self, message):
        print(f"{self.host:{self.hlen}} *", message)

    def run(self, command):
        print(f"{self.host:{self.hlen}} * run:", command)

    def var(self, var_name):  # c.var.name or c.var['name']
        return 'var value'

    def fact(self, fact_name):
        return 'fact value'  # c.fact.kvm or c.fact['kvm']
