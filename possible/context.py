
__all__ = ['Context']

from possible.engine import runtime
from possible.engine.exceptions import PossibleRuntimeError
from possible.engine.transport import SSH


class Fact:
    def __init__(self, ssh):
        self.ssh = ssh

    def __getitem__(self, name):
        if name == 'os':
            return 'linux'
        if name == 'distro':
            return 'centos'
        if name == 'virt':
            return True
        if name == 'kvm':
            return True


class Context:

    def __init__(self, hostname):
        self.max_hostname_len = len(max(runtime.hosts, key=len))
        self.hostname = hostname
        if hostname not in runtime.inventory.hosts:
            raise PossibleRuntimeError(f"Host '{hostname}' not found.")
        self.host = runtime.inventory.hosts[hostname]
        self.ssh = SSH(self.host)
        self.var = self.host.vars
        self.fact = Fact(self.ssh)

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
