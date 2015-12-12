# -*- coding: utf-8 -*-
#
# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals, division

import socket

from ..library import ffi, lib

from ..common import is_posix
from ..error import StatusCode, UVError, HandleClosedError
from ..handle import HandleType

from .stream import Stream, ConnectRequest, uv_connect_cb

__all__ = ['Pipe']


@HandleType.PIPE
class Pipe(Stream):
    """
    Pipe handles provide an abstraction over local domain sockets
    on Unix and named pipes on Windows.

    :raises uv.UVError: error while initializing the handle

    :param loop: event loop the handle should run on
    :param ipc: pipe should have inter process communication support not

    :type loop: uv.Loop
    :type ipc: bool
    """

    __slots__ = ['uv_pipe']

    def __init__(self, loop=None, ipc=False):
        self.uv_pipe = ffi.new('uv_pipe_t*')
        super(Pipe, self).__init__(self.uv_pipe, ipc, loop)
        code = lib.uv_pipe_init(self.loop.uv_loop, self.uv_pipe, int(ipc))
        if code < 0:
            self.destroy()
            raise UVError(code)

    def open(self, fd):
        """
        Open an existing file descriptor as a pipe.

        :raises uv.UVError: error while opening the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param fd: file descriptor
        :type fd: int
        """
        if self.closing: raise HandleClosedError()
        code = lib.cross_uv_pipe_open(self.uv_pipe, fd)
        if code < 0: raise UVError(code)

    @property
    def pending_count(self):
        """
        Number of pending streams to receive.

        :readonly: True
        :rtype: int
        """
        if self.closing: return 0
        return lib.uv_pipe_pending_count(self.uv_pipe)

    @property
    def pending_type(self):
        """
        Type of first pending stream. This returns a subclass of :class:`uv.Stream`.

        :raises uv.HandleClosedError: handle has already been closed or is closing

        :readonly: True
        :rtype: type
        """
        if self.closing: raise HandleClosedError()
        return HandleType(lib.uv_pipe_pending_type(self.uv_pipe)).cls

    def pending_accept(self):
        """
        Accept a pending stream.

        :raises uv.UVError: error while accepting stream
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :rtype: uv.Stream
        """
        return self.accept(cls=self.pending_type)

    def pending_instances(self, amount):
        """
        Set the number of pending pipe instance handles when the pipe server is
        waiting for connections.

        :param amount: amount of pending instances
        :type amount: int
        """
        lib.uv_pipe_pending_instances(self.uv_pipe, amount)

    @property
    def family(self):
        return socket.AF_UNIX if is_posix else None

    @property
    def sockname(self):
        """
        Name of the Unix domain socket or the named pipe.

        :raises uv.UVError: error while receiving sockname
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :readonly: True
        :rtype: unicode
        """
        if self.closing: raise HandleClosedError()
        c_buffer = ffi.new('char[]', 255)
        c_size = ffi.new('size_t*', 255)
        code = lib.uv_pipe_getsockname(self.uv_pipe, c_buffer, c_size)
        if code == StatusCode.ENOBUFS:
            c_buffer = ffi.new('char[]', c_size[0])
            code = lib.uv_pipe_getsockname(self.uv_pipe, c_buffer, c_size)
        if code < 0: raise UVError(code)
        return ffi.string(c_buffer, c_size[0]).decode()

    @property
    def peername(self):
        """
        Name of the Unix domain socket or the named pipe to which the handle is connected.

        :raises uv.UVError: error while receiving peername
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :readonly: True
        :rtype: unicode
        """
        if self.closing: raise HandleClosedError()
        c_buffer = ffi.new('char[]', 255)
        c_size = ffi.new('size_t*', 255)
        code = lib.uv_pipe_getpeername(self.uv_pipe, c_buffer, c_size)
        if code == StatusCode.ENOBUFS:
            c_buffer = ffi.new('char[]', c_size[0])
            code = lib.uv_pipe_getpeername(self.uv_pipe, c_buffer, c_size)
        if code < 0: raise UVError(code)
        return ffi.string(c_buffer, c_size[0]).decode()

    def bind(self, path):
        """
        Bind the pipe to a file path (Unix) or a name (Windows).

        :raises uv.UVError: error while binding to `path`
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param path: path to bind to
        :type path: unicode
        """
        if self.closing: raise HandleClosedError()
        code = lib.uv_pipe_bind(self.uv_pipe, path.encode())
        if code < 0: raise UVError(code)

    def connect(self, path, on_connect=None):
        """
        Connect to the given Unix domain socket or named pipe.

        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param path: path to connect to
        :param on_connect: callback called after connection has been established

        :type path: unicode
        :type on_connect: ((uv.ConnectRequest, uv.StatusCode) -> None) |
                          ((Any, uv.ConnectRequest, uv.StatusCode) -> None)

        :returns: connect request
        :rtype: uv.ConnectRequest
        """
        if self.closing: raise HandleClosedError()
        request = ConnectRequest(self, on_connect)
        c_path = path.encode()
        lib.uv_pipe_connect(request.uv_connect, self.uv_pipe, c_path, uv_connect_cb)
        return request
