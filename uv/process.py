# -*- coding: utf-8 -*-
#
# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import enum
import warnings

from .error import UVError
from .handle import HandleType, Handle
from .library import ffi, lib, detach, str_py2c, dummy_callback
from .loop import Loop
from .pipe import Pipe
from .signal import Signals
from .stream import Stream

__all__ = ['disable_stdio_inheritance', 'PIPE', 'ProcessFlags', 'Process']


def disable_stdio_inheritance():
    lib.uv_disable_stdio_inheritance()


class StandardIOFlags(enum.IntEnum):
    IGNORE = lib.UV_IGNORE

    INHERIT_FD = lib.UV_INHERIT_FD
    INHERIT_STREAM = lib.UV_INHERIT_STREAM

    CREATE_PIPE = lib.UV_CREATE_PIPE
    READABLE_PIPE = lib.UV_READABLE_PIPE
    WRITABLE_PIPE = lib.UV_WRITABLE_PIPE

    RW_PIPE = READABLE_PIPE | WRITABLE_PIPE


PIPE = StandardIOFlags.CREATE_PIPE


class ProcessFlags(enum.IntEnum):
    SETUID = lib.UV_PROCESS_SETUID
    SETGID = lib.UV_PROCESS_SETGID
    DETACHED = lib.UV_PROCESS_DETACHED

    WINDOWS_HIDE = lib. UV_PROCESS_WINDOWS_HIDE
    WINDOWS_VERBATIM_ARGUMENTS = lib.UV_PROCESS_WINDOWS_VERBATIM_ARGUMENTS


@ffi.callback('uv_exit_cb')
def uv_exit_cb(uv_process, exit_status, term_signal):
    process = detach(uv_process)
    process.on_exit(process, exit_status, term_signal)


def populate_stdio_container(uv_stdio, fileobj=None):
    if isinstance(fileobj, Stream):
        uv_stdio.data.stream = fileobj.uv_stream
        flags = StandardIOFlags.INHERIT_STREAM
    elif fileobj is PIPE:
        fileobj = Pipe()
        uv_stdio.data.stream = fileobj.uv_stream
        flags = StandardIOFlags.CREATE_PIPE | StandardIOFlags.RW_PIPE
    elif isinstance(fileobj, int):
        uv_stdio.data.fd = fileobj
        flags = StandardIOFlags.INHERIT_FD
    else:
        try:
            uv_stdio.data.fd = fileobj.fileno()
            flags = StandardIOFlags.INHERIT_FD
        except AttributeError:
            flags = StandardIOFlags.IGNORE
            if fileobj is not None:
                warnings.warn('ignoring unknown file object (%s)' % str(fileobj))
    uv_stdio.flags = flags
    return fileobj


@HandleType.PROCESS
class Process(Handle):
    def __init__(self, arguments, uid: int=None, gid: int=None, cwd: str=None,
                 env: dict=None, flags: int=0, loop: Loop=None, stdin=None,
                 stdout=None, stderr=None, stdio: list=None, on_exit: callable=None):
        self.uv_options = ffi.new('uv_process_options_t*')

        self.c_file = str_py2c(arguments[0])
        self.uv_options.file = self.c_file

        self.c_args_list = list(map(str_py2c, arguments))
        self.c_args_list.append(ffi.NULL)
        self.c_args = ffi.new('char*[]', self.c_args_list)
        self.uv_options.args = self.c_args

        stdio_count = 3
        if stdio is not None: stdio_count += len(stdio)
        self.uv_options.stdio_count = stdio_count

        self.c_stdio = ffi.new('uv_stdio_container_t[]', stdio_count)
        self.stdin = populate_stdio_container(self.c_stdio[0], stdin)
        self.stdout = populate_stdio_container(self.c_stdio[1], stdout)
        self.stderr = populate_stdio_container(self.c_stdio[2], stderr)
        if stdio is not None:
            self.stdio = [populate_stdio_container(self.c_stdio[3 + i], stdio[i])
                          for i in range(len(stdio))]
        self.uv_options.stdio = self.c_stdio

        if cwd is not None:
            self.c_cwd = str_py2c(cwd)
            self.uv_options.cwd = self.c_cwd

        if env is not None:
            self.c_env_list = [str_py2c('%s=%s' % item) for item in env.items()]
            self.c_env_list.append(ffi.NULL)
            self.c_env = ffi.new('char*[]', self.c_env_list)
            self.uv_options.env = self.c_env

        if uid is not None:
            flags |= ProcessFlags.SETUID
        if gid is not None:
            flags |= ProcessFlags.SETGID

        lib.cross_set_process_uid_gid(self.uv_options, uid or 0, gid or 0)

        self.uv_options.flags = flags
        self.uv_options.exit_cb = uv_exit_cb

        self.process = ffi.new('uv_process_t*')
        self.on_exit = on_exit or dummy_callback
        super().__init__(self.process, loop)
        code = lib.uv_spawn(self.loop.uv_loop, self.process, self.uv_options)
        if code < 0: raise UVError(code)

    @property
    def pid(self) -> int:
        return self.process.pid

    def kill(self, signum: int=Signals.SIGINT):
        code = lib.uv_process_kill(self.process, signum)
        if code < 0: raise UVError(code)
