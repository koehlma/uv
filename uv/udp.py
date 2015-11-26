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
from .dns import c_create_sockaddr
from .error import UVError
from .handle import HandleType, Handle
from .library import ffi, lib, c_require
from .loop import Loop


class UDPFlags(enum.IntEnum):
    IPV6ONLY = lib.UV_UDP_IPV6ONLY
    PARTIAL = lib.UV_UDP_PARTIAL
    REUSEADDR = lib.UV_UDP_REUSEADDR


class Membership(enum.IntEnum):
    LEAVE_GROUP = lib.UV_LEAVE_GROUP
    JOIN_GROUP = lib.UV_JOIN_GROUP


@HandleType.UDP
class UDP(Handle):
    __slots__ = ['uv_udp']

    def __init__(self, flags: int=0, loop: Loop=None):
        self.uv_udp = ffi.new('uv_tcp_t*')
        super().__init__(self.uv_udp, loop)
        code = lib.uv_udp_init_ex(self.loop.uv_loop, self.uv_udp, flags)
        if code < 0: raise UVError(code)

    def open(self, fd: int):
        code = lib.uv_udp_open(self.uv_udp, lib.sock_from_int(fd))
        if code < 0: raise UVError(code)

    def bind(self, ip, port, flags: int=0):
        code = lib.uv_tcp_bind(self.uv_udp, c_create_sockaddr(ip, port), flags)
        if code < 0: raise UVError(code)

    def connect(self, ip, port, callback=None):
        request = ConnectRequest(callback)
        sockaddr = c_create_sockaddr(ip, port)
        c_require(request.connect, sockaddr)
        self.requests.add(request)
        code = lib.uv_tcp_connect(request.connect, self.uv_udp, sockaddr, connect_callback)
        if code < 0: raise UVError(code)
        return request
