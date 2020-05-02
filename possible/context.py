
__all__ = ['Context']

import re
import os
import shlex
import sys
import time
import tempfile

from possible.engine import runtime
from possible.editors import _apply_editors
from possible.engine.exceptions import PossibleRuntimeError, PossibleFileNotFound
from possible.engine.utils import to_bytes, to_text
from possible.engine.transport import SSH


class Result:
    def __init__(self, returncode, stdout_bytes, stderr_bytes):
        self.returncode = returncode
        self.stdout_bytes = stdout_bytes
        self.stderr_bytes = stderr_bytes
        self.stdout_raw = stdout_bytes.decode(encoding="utf-8", errors="replace")
        self.stderr_raw = stderr_bytes.decode(encoding="utf-8", errors="replace")
        self.stdout = self.stdout_raw.strip()
        self.stderr = self.stderr_raw.strip()

    def __bool__(self):
        return self.returncode == 0


class Context:
    def __init__(self, hostname):
        if hostname not in runtime.inventory.hosts:
            raise PossibleRuntimeError(f"Host '{hostname}' not found.")
        self.max_hostname_len = len(max(runtime.hosts, key=len))
        self.host = runtime.inventory.hosts[hostname]
        self.ssh = SSH(self.host)
        self.hostname = hostname

    def name(self, *args, **kwargs):
        if not runtime.config.args.quiet:
            print(f"{self.hostname:{self.max_hostname_len}} *", *args, file=sys.stdout, flush=True, **kwargs)

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
        return self.run(f"""if [ -e {shlex.quote(remote_filename)} ]; then echo "True"; fi""").stdout == "True"

    def isfile(self, remote_filename):
        return self.run(f"""if [ -f {shlex.quote(remote_filename)} ]; then echo "True"; fi""").stdout == "True"

    def islink(self, remote_filename):
        return self.run(f"""if [ -L {shlex.quote(remote_filename)} ]; then echo "True"; fi""").stdout == "True"

    def isdir(self, remote_filename):
        return self.run(f"""if [ -d {shlex.quote(remote_filename)} ]; then echo "True"; fi""").stdout == "True"

    def is_reboot_required(self):
        if not self.isfile("/usr/bin/needs-restarting"):
            self.run("yum install yum-utils -y")
        result = self.run("/usr/bin/needs-restarting --reboothint", can_fail=True)
        return result.returncode == 1

    def reboot(self, *, wait_seconds=180, reboot_command="reboot"):
        assert wait_seconds > 30
        old_uptime = self.run('uptime -s').stdout
        self.run(reboot_command, can_fail=True)
        while wait_seconds > 0:
            time.sleep(1)
            result = self.run('uptime -s', can_fail=True)
            if result:
                current_uptime = result.stdout
                if old_uptime != current_uptime:
                    return
            wait_seconds = wait_seconds - 1
        raise PossibleRuntimeError(f"Reboot host {self.hostname} failed.")

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

    def put(self, content, remote_filename, mode='0644'):
        if not isinstance(mode, str):
            raise PossibleRuntimeError(f"Mode must be string, like '0644'.")
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
            os.chmod(temp_filename, int(mode))
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

    def edit(self, remote_filename, *editors):
        old_text = self.get(remote_filename)
        changed, new_text = _apply_editors(old_text, *editors)
        if changed:
            self.put(new_text, remote_filename)
        return changed

    def chown(self, remote_filename, *, owner='root', group='root'):
        if not os.path.isabs(remote_filename):
            raise PossibleRuntimeError(f"Remote filename must be absolute: {remote_filename}")
        stdout = self.run('chown --changes ' + owner.strip() + ':' + group.strip() + ' -- ' + remote_filename).stdout
        changed = stdout != ""
        return changed

    def chmod(self, remote_filename, *, mode='0644'):
        if not os.path.isabs(remote_filename):
            raise PossibleRuntimeError(f"Remote filename must be absolute: {remote_filename}")
        if not isinstance(mode, str):
            raise PossibleRuntimeError(f"Mode must be string, like '0644'.")
        stdout = self.run('chmod --changes ' + mode + ' -- ' + remote_filename).stdout
        changed = stdout != ""
        return changed

    def var(self, key):
        return self.host.vars[key]

    def fact(self, key):
        if key == 'virt':
            virtualization_type = None
            stdout = self.run('hostnamectl status').stdout
            virtualization_line_regexp = re.compile(r'^\s*Virtualization:\s(?P<virtualization_type>\w+)\s*$')
            for line in stdout.split('\n'):
                match = virtualization_line_regexp.match(line)
                if match:
                    virtualization_type = match.group('virtualization_type')
                    break
            return virtualization_type
        elif key == 'kvm':
            return self.fact('virt') == 'kvm'
        elif key == 'openvz':
            return self.fact('virt') == 'openvz'
        else:
            raise KeyError(f"Unknown fact key '{key}'.")
