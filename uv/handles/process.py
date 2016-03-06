# -*- coding: utf-8 -*-

# Copyright (C) 2016, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function, unicode_literals

import sys

from .. import base, common, error, handle
from ..library import ffi, lib

from . import pipe, signal, stream


def disable_stdio_inheritance():
    """
    Disables inheritance for file descriptors / handles that this
    process inherited from its parent. The effect is that child
    processes spawned by this process don’t accidentally inherit
    these handles.

    It is recommended to call this function as early in your program
    as possible, before the inherited file descriptors can be closed
    or duplicated.

    .. note::
        This function works on a best-effort basis: which means there
        is no guarantee that libuv can discover all file descriptors
        that were inherited. In general it does a better job on Windows
        than it does on Unix.
    """
    lib.uv_disable_stdio_inheritance()  # pragma: no cover


class StandardIOFlags(common.Enumeration):
    """
    Standard IO flags enumeration.

    .. warning::
        These flags are used internally to specify which file
        descriptors should be exposed to a new child process.
    """

    IGNORE = lib.UV_IGNORE

    INHERIT_FD = lib.UV_INHERIT_FD
    INHERIT_STREAM = lib.UV_INHERIT_STREAM

    CREATE_PIPE = lib.UV_CREATE_PIPE
    READABLE_PIPE = lib.UV_READABLE_PIPE
    WRITABLE_PIPE = lib.UV_WRITABLE_PIPE


class CreatePipe(object):
    """
    Passed to one of the standard IO arguments of :class:`Process`, it
    tells the library to create a new pipe to communicate with the
    child process.

    :param readable:
        pipe should be readable
    :param writable:
        pipe should be writable
    :param ipc:
        pipe should support inter process communication

    :type readable:
        bool
    :type writable:
        bool
    :type ipc:
        bool
    """

    __slots__ = ['ipc', 'flags']

    def __init__(self, readable=False, writable=False, ipc=False):
        self.ipc = ipc
        self.flags = StandardIOFlags.CREATE_PIPE
        if readable:
            self.flags |= StandardIOFlags.READABLE_PIPE
        if writable:
            self.flags |= StandardIOFlags.WRITABLE_PIPE

    def __repr__(self):
        readable = bool(self.flags & StandardIOFlags.READABLE_PIPE)
        writable = bool(self.flags & StandardIOFlags.READABLE_PIPE)
        string = '<CreatePipe readable={}, writable={}, ipc={}>'
        return string.format(readable, writable, self.ipc)


# subclass int for documentation purposes
class _FD(int):
    def __repr__(self):
        return '<FileDescriptor: {}>'.format(self)


def _get_fileno(fileobj):
    try:
        return _FD(fileobj.fileno())
    except Exception:  # pragma: no cover
        return None


PIPE = CreatePipe(readable=True, writable=True, ipc=True)
"""
Create a readable and writable inter process communication pipe.
"""
STDIN = _get_fileno(sys.stdin)
"""
Standard input file descriptor.
"""
STDOUT = _get_fileno(sys.stdout)
"""
Standard output file descriptor.
"""
STDERR = _get_fileno(sys.stderr)
"""
Standard error file descriptor.
"""


class ProcessFlags(common.Enumeration):
    """
    Process configuration flags enumeration.
    """

    # set implicitly by uid and gid parameters
    SETUID = lib.UV_PROCESS_SETUID
    SETGID = lib.UV_PROCESS_SETGID

    DETACHED = lib.UV_PROCESS_DETACHED
    """
    Spawn the child process in a detached state – this will make it a
    process group leader, and will effectively enable the child to keep
    running after the parent exits. Note that the child process will
    still keep the parent's event loop alive unless the parent process
    calls :func:`uv.Handle.dereference` on the child's process handle.

    :type: uv.ProcessFlags
    """

    WINDOWS_HIDE = lib.UV_PROCESS_WINDOWS_HIDE
    """
    Hide the subprocess console window that would normally be created.
    This option is only meaningful on Windows systems. By default it is
    enabled, to disable this flag pass `0` to :class:`uv.Process`'s
    flag parameter. On Unix it is ignored.

    :type: uv.ProcessFlags
    """

    WINDOWS_VERBATIM = lib.UV_PROCESS_WINDOWS_VERBATIM_ARGUMENTS
    """
    Do not wrap any arguments in quotes, or perform any other escaping,
    when converting the argument list into a command line string. This
    option is only meaningful on Windows systems. On Unix it is
    ignored.

    :type: uv.ProcessFlags
    """


@base.handle_callback('uv_exit_cb')
def uv_exit_cb(process_handle, returncode, signum):
    """
    :type process_handle:
        uv.Process
    :type returncode:
        int
    :type signum:
        int
    """
    process_handle.clear_pending()
    process_handle.on_exit(process_handle, returncode, signum)


def populate_stdio_container(uv_stdio, file_base=None):
    """
    Used internally to populate `uv_stdio_t` with data based on a given
    file like base object.

    :type uv_stdio:
        ffi.CData[uv_stdio_t]
    :type file_base:
        uv.UVStream | uv.CreatePipe | int | file-like
    """
    fileobj = file_base
    if isinstance(file_base, stream.UVStream):
        uv_stdio.data.stream = file_base.uv_stream
        uv_stdio.flags = StandardIOFlags.INHERIT_STREAM
    elif isinstance(file_base, CreatePipe):
        fileobj = pipe.Pipe(ipc=file_base.ipc)
        uv_stdio.data.stream = fileobj.uv_stream
        uv_stdio.flags = file_base.flags
    else:
        try:
            if isinstance(file_base, int):
                uv_stdio.data.fd = file_base
            else:
                uv_stdio.data.fd = file_base.fileno()
            uv_stdio.flags = StandardIOFlags.INHERIT_FD
        except AttributeError:
            uv_stdio.flags = StandardIOFlags.IGNORE
            if file_base is not None:
                raise error.ArgumentError(message='unknown file object type')
    return fileobj


@handle.HandleTypes.PROCESS
class Process(handle.UVHandle):
    """
    Process handles will spawn a new process and allow the user to
    control it and establish communication channels with it using
    streams.

    :raises uv.UVError:
        error while initializing the handle

    :param arguments:
        program path and command line arguments
    :param uid:
        spawn as user with user id `uid`
    :param gid:
        spawn as group with group id `gid`
    :param cwd:
        child process working directory
    :param env:
        child process environment variables
    :param flags:
        process spawn flags to be used
    :param stdin:
        standard input of the child process
    :param stdout:
        standard output of the child process
    :param stderr:
        standard error of the child process
    :param stdio:
        other standard file descriptors of the child process
    :param loop:
        event loop the handle should run on
    :param on_exit:
        callback which should be called after process exited

    :type arguments:
        list[unicode]
    :type uid:
        int
    :type gid:
        int
    :type cwd:
        unicode
    :type env:
        dict[unicode,unicode]
    :type flags:
        int
    :type stdin:
        int | uv.UVStream | uv.CreatePipe | file-like | None
    :type stdout:
        int | uv.UVStream | uv.CreatePipe | file-like | None
    :type stderr:
        int | uv.UVStream | uv.CreatePipe | file-like | None
    :type stdio:
        list[int | uv.UVStream | uv.CreatePipe | file-like]
    :type loop:
        uv.Loop
    :type on_exit:
        ((uv.Process, int, int) -> None) |
        ((Any, uv.Process, int, int) -> None)
    """

    uv_handle_type = 'uv_process_t*'
    uv_handle_init = lib.uv_spawn

    def __init__(self, arguments, uid=None, gid=None, cwd=None, env=None, stdin=None,
                 stdout=None, stderr=None, stdio=None, flags=ProcessFlags.WINDOWS_HIDE,
                 loop=None, on_exit=None):
        uv_options = ffi.new('uv_process_options_t*')

        c_file = ffi.new('char[]', arguments[0].encode())
        uv_options.file = c_file

        c_args_list = [ffi.new('char[]', argument.encode()) for argument in arguments]
        c_args_list.append(ffi.NULL)
        c_args = ffi.new('char*[]', c_args_list)
        uv_options.args = c_args

        stdio_count = 3
        if stdio is not None:
            stdio_count += len(stdio)
        uv_options.stdio_count = stdio_count

        c_stdio_containers = ffi.new('uv_stdio_container_t[]', stdio_count)
        self.stdin = populate_stdio_container(c_stdio_containers[0], stdin)
        """
        Standard input of the child process.

        :readonly:
            True
        :type:
            int | uv.UVStream | file-like | None
        """
        self.stdout = populate_stdio_container(c_stdio_containers[1], stdout)
        """
        Standard output of the child process.

        :readonly:
            True
        :type:
            int | uv.UVStream | file-like | None
        """
        self.stderr = populate_stdio_container(c_stdio_containers[2], stderr)
        """
        Standard error of the child process.

        :readonly:
            True
        :type:
            int | uv.UVStream | file-like | None
        """
        self.stdio = []
        """
        Other standard file descriptors of the child process.

        :readonly:
            True
        :type:
            list[int | uv.UVStream | file-like]
        """
        if stdio is not None:
            for number in range(len(stdio)):
                c_stdio = c_stdio_containers[3 + number]
                fileobj = populate_stdio_container(c_stdio, stdio[number])
                self.stdio.append(fileobj)
        uv_options.stdio = c_stdio_containers

        if cwd is not None:
            c_cwd = ffi.new('char[]', cwd.encode())
            uv_options.cwd = c_cwd

        if env is not None:
            c_env_list = [ffi.new('char[]', ('%s=%s' % item).encode())
                          for item in env.items()]
            c_env_list.append(ffi.NULL)
            c_env = ffi.new('char*[]', c_env_list)
            uv_options.env = c_env

        if uid is not None:
            flags |= ProcessFlags.SETUID
        if gid is not None:
            flags |= ProcessFlags.SETGID

        lib.cross_set_process_uid_gid(uv_options, uid or 0, gid or 0)

        uv_options.flags = flags
        uv_options.exit_cb = uv_exit_cb

        self.on_exit = on_exit or common.dummy_callback
        """
        Callback which should be called after process exited.


        .. function:: on_exit(process_handle, returncode, signum)

            :param process_handle:
                handle the call originates from
            :param returncode:
                status code returned by the process on termination
            :param signum:
                signal number caused the process to exit

            :type process_handle:
                uv.Process
            :type returncode:
                int
            :type signum:
                int



        :readonly:
            False
        :type:
            ((uv.Process, int, int) -> None) |
            ((Any, uv.Process, int, int) -> None)
        """
        super(Process, self).__init__(loop, (uv_options, ))
        self.uv_process = self.base_handle.uv_object
        self.set_pending()

    @property
    def pid(self):
        """
        PID of the spawned process.

        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :readonly:
            True
        :rtype:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        return self.uv_process.pid

    def kill(self, signum=signal.Signals.SIGINT):
        """
        Send the specified signal to the process.

        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param signum:
            signal number

        :type signum:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        code = lib.uv_process_kill(self.uv_process, signum)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
