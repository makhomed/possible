
__all__ = ['Context', 'local_run']

import os
import sys
import subprocess
import time
import tempfile

from possible.engine import runtime
from possible.editors import _apply_editors, edit, append_line, replace_line, strip
from possible.engine.exceptions import PossibleRuntimeError, PossibleFileNotFound
from possible.engine.utils import to_bytes, to_text
from possible.engine.transport import SSH


LOCAL_COMMAND_TIMEOUT = 600


def local_run(command, *, stdin=None, can_fail=False):
    old_cwd = os.getcwd()
    os.chdir(runtime.config.files)
    try:
        command = command.replace("$FILES", str(runtime.config.files))
        command = ["/bin/bash", "-c", command]
        p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout_bytes, stderr_bytes = p.communicate(to_bytes(stdin), LOCAL_COMMAND_TIMEOUT)
        except subprocess.TimeoutExpired:
            p.kill()
            stdout_bytes, stderr_bytes = p.communicate()
        result = Result(p.returncode, stdout_bytes, stderr_bytes)
        if result or can_fail:
            return result
        else:
            raise PossibleRuntimeError(f"Unexpected returncode '{p.returncode}'\nlocal command: {command}\nstdout: {stdout_bytes}\nstderr: {stderr_bytes}")
    finally:
        os.chdir(old_cwd)


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

    def warn(self, *args, **kwargs):
        if not runtime.config.args.quiet:
            print(f"{self.hostname:{self.max_hostname_len}} $ WARNING!!!", *args, file=sys.stdout, flush=True, **kwargs)

    def fatal(self, *args, **kwargs):
        if not runtime.config.args.quiet:
            print(f"{self.hostname:{self.max_hostname_len}} & FATAL ERROR!!!", *args, file=sys.stdout, flush=True, **kwargs)
            raise PossibleRuntimeError(*args)

    def run(self, command, *, stdin=None, can_fail=False):
        returncode, stdout_bytes, stderr_bytes = self.ssh.run(command, stdin=stdin)
        result = Result(returncode, stdout_bytes, stderr_bytes)
        if result or can_fail:
            return result
        else:
            raise PossibleRuntimeError(f"Unexpected returncode '{returncode}'\ncommand: {command}\nstdout: {stdout_bytes}\nstderr: {stderr_bytes}")

    def is_file(self, remote_filename):
        return self.run(f"""if [ -f {remote_filename} ]; then echo "True"; fi""").stdout == "True"

    def is_executable_file(self, remote_filename):
        return self.run(f"""if [ -f {remote_filename} ] && [ -x {remote_filename} ]; then echo "True"; fi""").stdout == "True"

    def is_link(self, remote_filename):
        return self.run(f"""if [ -L {remote_filename} ]; then echo "True"; fi""").stdout == "True"

    def is_directory(self, remote_filename):
        return self.run(f"""if [ -d {remote_filename} ]; then echo "True"; fi""").stdout == "True"

    def is_reboot_required(self):
        if self.fact('systemd-nspawn'):
            # workaround of bug https://bugzilla.redhat.com/show_bug.cgi?id=1913962
            return False
        if not self.is_file("/usr/bin/needs-restarting"):
            self.run("yum install yum-utils -y")
        result = self.run("/usr/bin/needs-restarting --reboothint", can_fail=True)
        return result.returncode == 1

    def reboot(self, *, wait_seconds=180, reboot_command="reboot"):
        assert wait_seconds > 30
        old_uptime = self.run('stat --printf="%y" /proc/1/cmdline').stdout
        self.run(reboot_command, can_fail=True)
        while wait_seconds > 0:
            time.sleep(1)
            result = self.run('stat --printf="%y" /proc/1/cmdline', can_fail=True)
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
        if self.is_file(remote_filename):
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

    def put(self, content, remote_filename, *, mode='0644'):
        if not isinstance(mode, str) or not mode.isnumeric():
            raise PossibleRuntimeError(f"Mode must be string, like '0644'.")
        if not os.path.isabs(remote_filename):
            raise PossibleRuntimeError(f"Remote filename must be absolute: {remote_filename}")
        if self.is_file(remote_filename):
            local_content = to_bytes(content)
            remote_content = self.get(remote_filename, as_bytes=True)
            if local_content == remote_content:
                return False
        fd, temp_filename = tempfile.mkstemp(suffix='.tmp', prefix='possible-', dir='/tmp')
        try:
            temp_file = os.fdopen(fd, mode='wb')
            temp_file.write(to_bytes(content))
            temp_file.close()
            os.chmod(temp_filename, int(mode, 8))
            returncode, stdout_bytes, stderr_bytes = self.ssh.put(temp_filename, remote_filename)
            if returncode != 0:
                raise PossibleRuntimeError(f"Unexpected returncode '{returncode}'\ncommand: put('{content}', {remote_filename})\nstdout: {stdout_bytes}\nstderr: {stderr_bytes}")
            else:
                return True
        finally:
            os.remove(temp_filename)

    def get(self, remote_filename, default_value=None, *, as_bytes=False):
        if not os.path.isabs(remote_filename):
            raise PossibleRuntimeError(f"Remote filename must be absolute: {remote_filename}")
        if not self.is_file(remote_filename):
            if default_value is None:
                raise PossibleFileNotFound(f"Remote file does not exist: {remote_filename}")
            else:
                return default_value
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

    def read(self, local_filename, default_value=None, *, as_bytes=False):
        if os.path.isabs(local_filename):
            raise PossibleRuntimeError(f"Local filename must be relative: {local_filename}")
        local_filename = str(runtime.config.files / local_filename)
        if not os.path.isfile(local_filename):
            if default_value is None:
                raise PossibleFileNotFound(f"Local file does not exist: {local_filename}")
            else:
                return default_value
        local_file = open(local_filename, "rb")
        content = local_file.read()
        local_file.close()
        if as_bytes:
            return content
        else:
            return to_text(content)

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
        if not isinstance(mode, str) or not mode.isnumeric():
            raise PossibleRuntimeError(f"Mode must be string, like '0644'.")
        if not os.path.isabs(remote_filename):
            raise PossibleRuntimeError(f"Remote filename must be absolute: {remote_filename}")
        stdout = self.run('chmod --changes ' + mode + ' -- ' + remote_filename).stdout
        changed = stdout != ""
        return changed

    def var(self, key, default=None):
        return self.host.vars.get(key, default)

    def _MemTotal_KiB(self):
            #print(self.run("cat /proc/meminfo").stdout)
            string = self.run("cat /proc/meminfo").stdout.splitlines()[0].split()[1]
            result = int(string)
            assert result > 0
            return result

    def fact(self, key):
        if key == 'virt':
            """ https://www.freedesktop.org/software/systemd/man/systemd-detect-virt.html """
            return self.run('systemd-detect-virt', can_fail=True).stdout
        elif key == 'kvm':
            return self.fact('virt') == 'kvm'
        elif key == 'systemd-nspawn':
            return self.fact('virt') == 'systemd-nspawn'
        elif key == 'openvz':
            return self.fact('virt') == 'openvz'
        elif key == 'MemTotal_KiB':
            return int(self._MemTotal_KiB())
        elif key == 'MemTotal_MiB':
            return int(self._MemTotal_KiB() / 1024.0)
        elif key == 'MemTotal_GiB':
            return int(self._MemTotal_KiB() / 1024.0 / 1024.0)
        else:
            raise KeyError(f"Unknown fact key '{key}'.")

    def is_user_exists(self, name):
        """is user exists?

        Args:
            name: user name

        Returns:
            True if user exists, False if user not exists.
        """
        passwd = self.run("getent passwd").stdout
        for line in passwd.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.split(":")[0] == name:
                return True
        return False

    def is_group_exists(self, name):
        """is group exists?

        Args:
            name: group name

        Returns:
            True if group exists, False if group not exists.
        """
        group = self.run("getent group").stdout
        for line in group.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.split(":")[0] == name:
                return True
        return False

    def user_home_directory(self, name):
        """get user home directory

        Args:
            name: user name

        Returns:
            Home directory if user exists or None if user not exists.
        """
        passwd = self.run("getent passwd").stdout
        for line in passwd.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.split(":")[0] == name:
                return line.split(":")[5]
        raise PossibleRuntimeError(f"User '{name}' not found.")

    def add_to_authorized_keys(self, local_public_keys_filename, username, remote_authorized_keys_filename="~/.ssh/authorized_keys"):
        if os.path.isabs(local_public_keys_filename):
            raise PossibleRuntimeError(f"Local public keys filename must be relative: {local_public_keys_filename}")
        if remote_authorized_keys_filename.startswith('~'):
            home_directory = self.user_home_directory(username).rstrip('/')
            remote_authorized_keys_filename = remote_authorized_keys_filename.lstrip('~')
            remote_authorized_keys_filename = home_directory + remote_authorized_keys_filename
        if not os.path.isabs(remote_authorized_keys_filename):
            raise PossibleRuntimeError(f"Remote filename must be absolute: {remote_authorized_keys_filename}")
        dirname = os.path.dirname(remote_authorized_keys_filename)
        if not self.is_directory(dirname):
            self.run(f"mkdir {dirname}")
            if os.path.basename(dirname) == '.ssh':
                self.chown(dirname, owner=username, group=username)
                self.chmod(dirname, mode="0700")
            else:  # shared dir for authorized keys
                self.chown(dirname, owner="root", group="root")
                self.chmod(dirname, mode="0755")
        old_content = self.get(remote_authorized_keys_filename, "")
        new_content = old_content
        keys = self.read(local_public_keys_filename)
        for key in keys.split("\n"):
            key = key.strip()
            if not key:
                continue
            new_content = edit(new_content, append_line(key, insert_empty_line_before=True))
        if new_content != old_content:
            self.put(new_content, remote_authorized_keys_filename, mode="0600")
            self.chown(remote_authorized_keys_filename, owner=username, group=username)
            return True
        else:
            return False

    def disable_selinux(self):
        """Disable SELinux.

        Edit ``/etc/selinux/config`` and write ``SELINUX=disabled`` to it.
        Also call ``setenforce 0`` to switch SELinux into Permissive mode.

        Returns:
            True if ``/etc/selinux/config`` changed or if SELinux ``Enforcing`` mode switched into ``Permissive`` mode, False otherwise.

        """
        if self.is_file('/etc/selinux/config'):
            changed1 = self.edit('/etc/selinux/config', replace_line(r'\s*SELINUX\s*=\s*.*', 'SELINUX=disabled'))
        else:
            changed1 = False
        if self.run('if [ -f /usr/sbin/setenforce ] && [ -f /usr/sbin/getenforce ] ; then echo exists ; fi') == 'exists':
            changed2 = self.run('STATUS=$(getenforce) ; if [ "$STATUS" == "Enforcing" ] ; then setenforce 0 ; echo perm ; fi').stdout == 'perm'
        else:
            changed2 = False
        return changed1 or changed2

    def remove_file(self, remote_filename):
        """Remove remote file.

        Args:
            remote_filename: Remote file name, must be absolute.

        Returns:
            True if file removed, False if file not exists.
        """
        if not os.path.isabs(remote_filename):
            raise PossibleRuntimeError(f"Remote filename must be absolute: {remote_filename}")
        changed = self.run(f'if [ -f {remote_filename} ] ; then rm -f -- {remote_filename} ; echo removed ; fi').stdout == 'removed'
        return changed

    def create_directory(self, remote_dirname):
        """Create remote directory.

        .. note::
            Directory created only if no file exists with name ``remote_dirname``. Existing file will not be deleted.

        Args:
            remote_dirname: Remote directory name, must be absolute.

        Returns:
            True if directory created, False if directory already exists.
        """
        if not os.path.isabs(remote_dirname):
            raise PossibleRuntimeError(f"Remote dirname must be absolute: {remote_dirname}")
        changed = self.run(f'if [ ! -d {remote_dirname} ] ; then mkdir -- {remote_dirname} ; echo created ; fi').stdout == 'created'
        return changed

    def remove_directory(self, remote_dirname):
        """Remove remote directory.

        .. note::
            Remote directory must be empty. Recursive deletion of non-empty directories is not supported.

        Args:
            remote_dirname: Remote directory name, must be absolute.

        Returns:
            True if directory removed, False if directory already not exists.
        """
        if not os.path.isabs(remote_dirname):
            raise PossibleRuntimeError(f"Remote dirname must be absolute: {remote_dirname}")
        changed = self.run(f'if [ -d {remote_dirname} ] ; then rmdir -- {remote_dirname} ; echo removed ; fi').stdout == 'removed'
        return changed

    def systemctl_edit(self, name, override):
        """systemctl edit ``name``.

        Works like command ``systemctl edit name``. Creates directory ``/etc/systemd/system/${name}.d``
        and creates file ``override.conf`` inside it with contents from string override.

        Args:
            name: Name of systemd service to edit.
            override: Which text place inside ``override.conf`` file.
                Leading and trailing whitespace chars are stripped from override.

        Returns:
            True if file ``override.conf`` for service ``name`` changed, False otherwise.
        """
        if override is None:
            override = ''
        if not isinstance(override, str):
            PossibleRuntimeError("Override must be string type.")
        if '/' in name:
            PossibleRuntimeError(f"Invalid unit name '{name}'")
        if not name.endswith('.service'):
            name = name + '.service'
        override_dir = '/etc/systemd/system/' + name + '.d'
        override_conf = os.path.join(override_dir, 'override.conf')
        override = strip(override)
        if override:
            changed1 = self.create_directory(override_dir)
            changed2 = self.put(override, override_conf)
        else:
            changed1 = self.remove_file(override_conf)
            changed2 = self.remove_directory(override_dir)
        return changed1 or changed2
