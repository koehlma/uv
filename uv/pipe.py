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

import socket

from .library import ffi, lib, is_posix

from .error import UVError
from .handle import HandleType
from .loop import Loop
from .stream import Stream, ConnectRequest, uv_connect_cb

__all__ = ['Pipe']


@HandleType.PIPE
class Pipe(Stream):
    __slots__ = ['uv_pipe']

    def __init__(self, loop: Loop=None, ipc=False):
        self.uv_pipe = ffi.new('uv_pipe_t*')
        super().__init__(self.uv_pipe, loop, ipc)
        lib.uv_pipe_init(self.loop.uv_loop, self.uv_pipe, int(ipc))

    def open(self, fd: int):
        code = lib.cross_uv_pipe_open(self.uv_pipe, fd)
        if code < 0: raise UVError(code)

    @property
    def pending_count(self):
        return lib.uv_pipe_pending_count(self.uv_pipe)

    @property
    def pending_type(self):
        return HandleType(lib.uv_pipe_pending_type(self.uv_pipe)).cls

    @property
    def family(self):
        return socket.AF_UNIX if is_posix else None

    def bind(self, path):
        code = lib.uv_pipe_bind(self.uv_pipe, path.encode())
        if code < 0: raise UVError(code)

    def connect(self, path: str, callback: callable=None):
        request = ConnectRequest(callback)
        self.requests.add(request)
        c_path = path.encode()
        lib.uv_pipe_connect(request.uv_connect, self.uv_pipe, c_path, uv_connect_cb)
        return request
