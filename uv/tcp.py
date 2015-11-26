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
import socket

from .dns import c_create_sockaddr
from .error import UVError
from .handle import HandleType
from .library import ffi, lib, c_require
from .loop import Loop
from .stream import Stream, ConnectRequest, uv_connect_cb


class TCPFlags(enum.IntEnum):
    IPV6ONLY = lib.UV_TCP_IPV6ONLY


@HandleType.TCP
class TCP(Stream):
    __slots__ = ['tcp', 'sockaddr']

    def __init__(self, loop: Loop=None, ipc=False):
        self.tcp = ffi.new('uv_tcp_t*')
        super().__init__(self.tcp, loop, ipc)
        lib.uv_tcp_init(self.loop.uv_loop, self.tcp)
        self.sockaddr = None

    @property
    def family(self):
        return socket.AF_INET

    def bind(self, ip, port, flags: int=0):
        self.sockaddr = c_create_sockaddr(ip, port)
        code = lib.uv_tcp_bind(self.tcp, self.sockaddr, flags)
        if code < 0: raise UVError(code)

    def connect(self, ip, port, callback=None):
        request = ConnectRequest(callback)
        self.sockaddr = c_create_sockaddr(ip, port)
        c_require(request.uv_connect, self.sockaddr)
        self.requests.add(request)
        code = lib.uv_tcp_connect(request.uv_connect, self.tcp, self.sockaddr, uv_connect_cb)
        if code < 0: raise UVError(code)
        return request
