
__all__ = ['Context']

from possible.engine import runtime
from possible.engine import PossibleUserError


class Context:

    def __init__(self, hostname):
        self.max_hostname_len = len(max(runtime.hosts, key=len))
        self.hostname = hostname
        if hostname not in runtime.inventory.hosts:
            raise PossibleUserError(f"Host '{hostname}' not found // in posfile call to Context('{hostname}')")
        self.host = runtime.inventory.hosts[hostname]

    def name(self, message):
        print(f"{self.hostname:{self.max_hostname_len}} *", message)

    def run(self, command):
        print(f"{self.hostname:{self.max_hostname_len}} * run:", command)

    def sudo(self, command):
        print(f"{self.hostname:{self.max_hostname_len}} * sudo:", command)

    def put(self, local_file, remote_file):
        pass

    def get(self, remote_file, local_file):
        pass

    def var(self, var_name):  # c.var.name or c.var['name']
        return 'var value'

    def fact(self, fact_name):
        return 'fact value'  # c.fact.kvm or c.fact['kvm']
