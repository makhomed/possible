
__all__ = ['Context']

import shlex

from possible.engine import runtime
from possible.engine.exceptions import PossibleRuntimeError
from possible.engine.transport import SSH
from possible.engine.utils import to_str


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


class Result:
    def __init__(self, returncode, stdout_bytes, stderr_bytes):
        self.returncode = returncode
        self.stdout_bytes = stdout_bytes
        self.stderr_bytes = stderr_bytes
        self.stdout = stdout_bytes.decode(encoding="utf-8", errors="ignore")
        self.stderr = stderr_bytes.decode(encoding="utf-8", errors="ignore")

    def __bool__(self):
        return self.returncode == 0


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

    def run(self, command, *, stdin=None, shell=False, can_fail=False):
        if shell:
            command = "/bin/bash -c %s" % shlex.quote(command)
        returncode, stdout_bytes, stderr_bytes = self.ssh.run(command, stdin=stdin)
        result = Result(returncode, stdout_bytes, stderr_bytes)
        if result or can_fail:
            return result
        else:
            raise PossibleRuntimeError(f"Unexpected returncode '{returncode}'\ncommand: {command}\nstdout: {stdout_bytes}\nstderr: {stderr_bytes}")


    def put(self, local_filename, remote_filename, *, can_fail=False):
        returncode, stdout_bytes, stderr_bytes = self.ssh.put(local_filename, remote_filename)
        result = Result(returncode, stdout_bytes, stderr_bytes)
        if result or can_fail:
            return result
        else:
            raise PossibleRuntimeError(f"Unexpected returncode '{returncode}'\ncommand: put({local_filename}, {remote_filename})\nstdout: {stdout_bytes}\nstderr: {stderr_bytes}")


    def get(self, remote_filename, local_filename, *, can_fail=False):
        returncode, stdout_bytes, stderr_bytes = self.ssh.get(remote_filename, local_filename)
        result = Result(returncode, stdout_bytes, stderr_bytes)
        if result or can_fail:
            return result
        else:
            raise PossibleRuntimeError(f"Unexpected returncode '{returncode}'\ncommand: get({remote_filename}, {local_filename})\nstdout: {stdout_bytes}\nstderr: {stderr_bytes}")
