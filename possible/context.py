
__all__ = ['Context']

import os
import shlex
import tempfile

from possible.engine import runtime
from possible.engine.exceptions import PossibleRuntimeError, PossibleFileNotFound
from possible.engine.utils import to_bytes, to_text
from possible.engine.transport import SSH


class Result:
    def __init__(self, returncode, stdout_bytes, stderr_bytes):
        self.returncode = returncode
        self.stdout_bytes = stdout_bytes
        self.stderr_bytes = stderr_bytes
        self.stdout = stdout_bytes.decode(encoding="utf-8", errors="replace")
        self.stderr = stderr_bytes.decode(encoding="utf-8", errors="replace")

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
        self.fact = Fact(self)

    def name(self, message):
        if not runtime.config.args.quiet:
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

    def exists(self, remote_filename):
        return self.run(f"""if [ -e {shlex.quote(remote_filename)} ]; then echo "True"; fi""").stdout.strip() == "True"

    def isfile(self, remote_filename):
        return self.run(f"""if [ -f {shlex.quote(remote_filename)} ]; then echo "True"; fi""").stdout.strip() == "True"

    def islink(self, remote_filename):
        return self.run(f"""if [ -L {shlex.quote(remote_filename)} ]; then echo "True"; fi""").stdout.strip() == "True"

    def isdir(self, remote_filename):
        return self.run(f"""if [ -d {shlex.quote(remote_filename)} ]; then echo "True"; fi""").stdout.strip() == "True"

    def copy(self, local_filename, remote_filename):
        if os.path.isabs(local_filename):
            raise PossibleRuntimeError(f"Local filename must be relative: {local_filename}")
        local_filename = str(runtime.config.files / local_filename)
        if not os.path.isabs(remote_filename):
            raise PossibleRuntimeError(f"Remote filename must be absolute: {remote_filename}")
        if self.isfile(remote_filename):
            local_file = open(local_filename, mode="rb")
            local_content = local_file.read()
            local_file.close()
            remote_content = self.get(remote_filename, as_bytes=True)
            if local_content == remote_content:
                return False
        returncode, stdout_bytes, stderr_bytes = self.ssh.put(local_filename, remote_filename)
        if returncode != 0:
            raise PossibleRuntimeError(f"Unexpected returncode '{returncode}'\ncommand: copy({local_filename}, {remote_filename})\nstdout: {stdout_bytes}\nstderr: {stderr_bytes}")
        return True

    def put(self, content, remote_filename, mode=0o644):
        if not os.path.isabs(remote_filename):
            raise PossibleRuntimeError(f"Remote filename must be absolute: {remote_filename}")
        if self.isfile(remote_filename):
            local_content = to_bytes(content)
            remote_content = self.get(remote_filename, as_bytes=True)
            if local_content == remote_content:
                return False
        fd, temp_filename = tempfile.mkstemp(suffix='.tmp', prefix='possible-', dir='/tmp')
        try:
            temp_file = os.fdopen(fd, mode='wb')
            temp_file.write(to_bytes(content))
            temp_file.close()
            os.chmod(temp_filename, mode)
            returncode, stdout_bytes, stderr_bytes = self.ssh.put(temp_filename, remote_filename)
            if returncode != 0:
                raise PossibleRuntimeError(f"Unexpected returncode '{returncode}'\ncommand: put('{content}', {remote_filename})\nstdout: {stdout_bytes}\nstderr: {stderr_bytes}")
            else:
                return True
        finally:
            os.remove(temp_filename)

    def get(self, remote_filename, *, as_bytes=False):
        if not os.path.isabs(remote_filename):
            raise PossibleRuntimeError(f"Remote filename must be absolute: {remote_filename}")
        if not self.isfile(remote_filename):
            raise PossibleFileNotFound("Remote file does not exist: {remote_filename}")
        fd, temp_filename = tempfile.mkstemp(suffix='.tmp', prefix='possible-', dir='/tmp')
        try:
            returncode, stdout_bytes, stderr_bytes = self.ssh.get(remote_filename, temp_filename)
            if returncode != 0:
                raise PossibleRuntimeError(f"Unexpected returncode '{returncode}'\ncommand: get({remote_filename})\nstdout: {stdout_bytes}\nstderr: {stderr_bytes}")
            temp_file = os.fdopen(fd, mode="rb")
            content = temp_file.read()
            temp_file.close()
            if as_bytes:
                return content
            else:
                return to_text(content)
        finally:
            os.remove(temp_filename)


class Fact:
    def __init__(self, c):
        self.c = c

    def __getitem__(self, name):
        if name == 'os':
            return self.c.run('uname -s').stdout.strip()
        if name == 'distro':
            return 'centos'
        if name == 'virt':
            return True
        if name == 'kvm':
            return True
