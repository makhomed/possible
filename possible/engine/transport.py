
__all__ = ['SSH']

import errno
import os
import os.path
import shlex
import subprocess

from possible.engine.exceptions import PossibleError, PossibleRuntimeError, PossibleFileNotFound
from possible.engine.utils import debug, to_bytes, to_str


SSH_COMMON_ARGS = (b'-o', b'ControlMaster=auto', b'-o', b'ControlPersist=60s')

CONTROL_PATH_DIR = '~/.cache/possible'

SSH_COMMAND_TIMEOUT = 30

SSHPASS_AVAILABLE = None


class SSH:
    def __init__(self, host):
        self._host = host
        self.host = self._host.host
        self.port = self._host.port
        self.user = self._host.user
        self.password = self._host.password

    @staticmethod
    def _sshpass_available():
        global SSHPASS_AVAILABLE
        # We test once if sshpass is available, and remember the result. It
        # would be nice to use distutils.spawn.find_executable for this, but
        # distutils isn't always available; shutils.which() is Python3-only.
        if SSHPASS_AVAILABLE is None:
            try:
                p = subprocess.Popen(["sshpass"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate()
                SSHPASS_AVAILABLE = True
            except OSError:
                SSHPASS_AVAILABLE = False
        return SSHPASS_AVAILABLE

    @staticmethod
    def _get_control_path(host, port, user):
        pstring = '%s-%s-%s' % (host, port, user)
        return os.path.join(os.path.expanduser(CONTROL_PATH_DIR), pstring)

    def _build_command(self, binary, *other_args):
        '''
        Takes a binary (ssh, scp, sftp) and optional extra arguments and returns
        a command line as an array that can be passed to subprocess.Popen.
        '''

        b_command = []

        #
        # First, the command to invoke
        #

        # If we want to use password authentication, we have to set up a pipe to
        # write the password to sshpass.

        if self.password:
            if not self._sshpass_available():
                raise PossibleError("to use the 'ssh' connection type with passwords, you must install the sshpass program")
            self.sshpass_pipe = os.pipe()
            b_command += [b'sshpass', b'-d' + to_bytes(self.sshpass_pipe[0])]

        b_command += [to_bytes(binary)]

        b_command += SSH_COMMON_ARGS

        if self.port is not None:
            b_command += (b"-o", b"Port=" + to_bytes(self.port))

        if self.password:
            b_command += (b"-o", b"StrictHostKeyChecking=no")

        if not self.password:
            b_command += (
                    b"-o", b"KbdInteractiveAuthentication=no",
                    b"-o", b"PreferredAuthentications=publickey",
                    b"-o", b"PasswordAuthentication=no"
                )

        if self.user:
            b_command += (b"-o", b'User="%s"' % to_bytes(self.user))

        cpdir = os.path.expanduser(CONTROL_PATH_DIR)
        os.makedirs(cpdir, mode=0o700, exist_ok=True)
        os.chmod(cpdir, mode=0o700)
        if not os.access(cpdir, os.W_OK):
            raise PossibleError("Cannot write to ControlPath %s" % to_str(cpdir))
        b_command += (b"-o", b"ControlPath=" + to_bytes(SSH._get_control_path(self.host, self.port, self.user)))

        # Finally, we add any caller-supplied extras.
        if other_args:
            b_command += [to_bytes(a) for a in other_args]

        return b_command

    def _run(self, cmd, stdin):
        '''
        Starts the command and communicates with it until it ends.
        '''
        # Start the given command. If we don't need to pipeline data, we can try
        # to use a pseudo-tty (ssh will have been invoked with -tt). If we are
        # pipelining data, or can't create a pty, we fall back to using plain
        # old pipes.

        p = None

        if self.password:
            # pylint: disable=unexpected-keyword-arg
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=self.sshpass_pipe)
        else:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # If we are using SSH password authentication, write the password into
        # the pipe we opened in _build_command.

        if self.password:
            os.close(self.sshpass_pipe[0])
            try:
                os.write(self.sshpass_pipe[1], to_bytes(self.password) + b'\n')
            except OSError as e:
                # Ignore broken pipe errors if the sshpass process has exited.
                if e.errno != errno.EPIPE or p.poll() is None:
                    raise
            os.close(self.sshpass_pipe[1])

        try:
            b_stdout, b_stderr = p.communicate(to_bytes(stdin), SSH_COMMAND_TIMEOUT)
        except subprocess.TimeoutExpired:
            p.kill()
            b_stdout, b_stderr = p.communicate()

        return (p.returncode, b_stdout, b_stderr)

    def _file_transport_command(self, in_path, out_path, action):
        if not os.path.isabs(in_path):
            raise PossibleRuntimeError(f"File name must be absolute, not '{in_path}'")
        if not os.path.isabs(out_path):
            raise PossibleRuntimeError(f"File name must be absolute, not '{out_path}'")
        # scp require square brackets for IPv6 addresses,
        # but accept them for hostnames and IPv4 addresses too.
        host = '[%s]' % self.host
        if action == 'get':
            cmd = self._build_command('scp', u'{0}:{1}'.format(host, shlex.quote(in_path)), out_path)
        else:
            cmd = self._build_command('scp', in_path, u'{0}:{1}'.format(host, shlex.quote(out_path)))
        debug.print(f"SCP command: {cmd}")
        (returncode, stdout, stderr) = self._run(cmd, stdin=None)
        if returncode == 0:
            return (returncode, stdout, stderr)
        elif returncode == 255:
            raise PossibleError("Failed to connect to the host %s via scp" % (to_str(stderr)))
        else:
            raise PossibleError("Failed to transfer file %s to %s:\n%s\n%s" %
                                (to_str(in_path), to_str(out_path), to_str(stdout), to_str(stderr)))

    #
    # Main public methods
    #
    def run(self, cmd, *, stdin=None):
        ''' run a command on the remote host '''
        if not stdin:
            args = ('ssh', '-tt', self.host, cmd)
        else:
            args = ('ssh', self.host, cmd)
        cmd = self._build_command(*args)
        debug.print(f"SSH command: {cmd}")
        (returncode, stdout, stderr) = self._run(cmd, stdin)
        return (returncode, stdout, stderr)

    def put(self, local_filename, remote_filename):
        ''' transfer a file from local to remote '''
        if not os.path.exists(to_bytes(local_filename)):
            raise PossibleFileNotFound("file does not exist: {0}".format(to_str(local_filename)))
        return self._file_transport_command(local_filename, remote_filename, 'put')

    def get(self, remote_filename, local_filename):
        ''' fetch a file from remote to local '''
        return self._file_transport_command(remote_filename, local_filename, 'get')
