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

from ..dns import c_create_sockaddr, unpack_sockaddr
from ..error import UVError, HandleClosedError
from ..handle import HandleType
from ..common import Enumeration

from .stream import Stream, ConnectRequest, uv_connect_cb

__all__ = ['TCPFlags', 'TCP']


class TCPFlags(Enumeration):
    """ """
    IPV6ONLY = lib.UV_TCP_IPV6ONLY
    """
    Disable dual stack support.

    :type: int
    """


@HandleType.TCP
class TCP(Stream):
    """
    TCP handles are used to represent both TCP clients and servers.

    :raises uv.UVError: error while initializing the handle

    :param flags: tcp flags to be used
    :param loop: event loop the handle should run on

    :type flags: int
    :type loop: uv.Loop
    """

    __slots__ = ['uv_tcp', '_family']

    def __init__(self, flags=0, loop=None):
        self.uv_tcp = ffi.new('uv_tcp_t*')
        super(TCP, self).__init__(self.uv_tcp, False, loop)
        code = lib.uv_tcp_init_ex(self.loop.uv_loop, self.uv_tcp, flags)
        if code < 0:
            self.destroy()
            raise UVError(code)
        self._family = socket.AF_INET

    def open(self, fd):
        """
        Open an existing file descriptor as a tcp handle.

        :raises uv.UVError: error while opening the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param fd: file descriptor
        :type fd: int
        """
        if self.closing: raise HandleClosedError()
        code = lib.cross_uv_tcp_open(self.uv_tcp, fd)
        if code < 0: raise UVError(code)

    def set_nodelay(self, enable):
        """
        Enable / disable Nagle’s algorithm.

        :raises uv.UVError: error enabling / disabling the algorithm
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param enable: enable / disable
        :type enable: bool
        """
        if self.closing: raise HandleClosedError()
        code = lib.uv_tcp_nodelay(self.uv_tcp, int(enable))
        if code < 0: raise UVError(code)

    def set_keepalive(self, enable, delay=0):
        """
        Enable / disable TCP keep-alive.

        :raises uv.UVError: error enabling / disabling tcp keep-alive
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param enable: enable / disable
        :param delay: initial delay in seconds

        :type enable: bool
        :type delay: int
        """
        if self.closing: raise HandleClosedError()
        code = lib.uv_tcp_keepalive(self.uv_tcp, int(enable), delay)
        if code < 0: raise UVError(code)

    def set_simultaneous_accepts(self, enable):
        """
        Enable / disable simultaneous asynchronous accept requests that are queued
        by the operating system when listening for new TCP connections.

        This setting is used to tune a TCP server for the desired performance.
        Having simultaneous accepts can significantly improve the rate of accepting
        connections (which is why it is enabled by default) but may lead to uneven
        load distribution in multi-process setups.

        :raises uv.UVError: error enabling / disabling simultaneous accepts
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param enable: enable / disable
        :type enable: bool
        """
        if self.closing: raise HandleClosedError()
        code = lib.uv_tcp_simultaneous_accepts(self.uv_tcp, int(enable))
        if code < 0: raise UVError(code)

    @property
    def family(self):
        return self._family

    @property
    def sockname(self):
        """
        The current address to which the handle is bound to.

        :raises uv.UVError: error while receiving sockname
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :readonly: True
        :rtype: uv.Address4 | uv.Address6
        """
        if self.closing: raise HandleClosedError()
        c_storage = ffi.new('struct sockaddr_storage*')
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        c_size = ffi.new('int*', ffi.sizeof('struct sockaddr_storage'))
        code = lib.uv_tcp_getsockname(self.uv_tcp, c_sockaddr, c_size)
        if code < 0: raise UVError(code)
        return unpack_sockaddr(c_sockaddr)

    @property
    def peername(self):
        """
        The address of the peer connected to the handle.

        :raises uv.UVError: error while receiving peername
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :readonly: True
        :rtype: uv.Address4 | uv.Address6
        """
        if self.closing: raise HandleClosedError()
        c_storage = ffi.new('struct sockaddr_storage*')
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        c_size = ffi.new('int*', ffi.sizeof('struct sockaddr_storage'))
        code = lib.uv_tcp_getpeername(self.uv_tcp, c_sockaddr, c_size)
        if code < 0: raise UVError(code)
        return unpack_sockaddr(c_sockaddr)

    def bind(self, address, flags=0):
        """
        Bind the handle to an address. When the port is already taken, you
        can expect to see an :class:`uv.StatusCode.EADDRINUSE` error from
        either `bind()`, `listen()` or `connect()`. That is, a successful
        call to this function does not guarantee that the call to `listen()`
        or `connect()` will succeed as well.

        :raises uv.UVError: error while binding to `address`
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param address: address tuple `(ip, port, flowinfo=0, scope_id=0)`
        :param flags: bind flags to be used (mask of :class:`uv.TCPFlags`)

        :type address: tuple | uv.Address
        :type flags: int
        """
        if self.closing: raise HandleClosedError()
        c_storage = c_create_sockaddr(*address)
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        self._family = c_sockaddr.sa_family
        code = lib.uv_tcp_bind(self.uv_tcp, c_sockaddr, flags)
        if code < 0: raise UVError(code)

    def connect(self, address, on_connect=None):
        """
        Establish an IPv4 or IPv6 TCP connection.

        :raises uv.UVError: error while connecting to `address`
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param address: address tuple `(ip, port, flowinfo=0, scope_id=0)`
        :param on_connect: callback called after connection has been established

        :type address: tuple | uv.Address
        :type on_connect: ((uv.ConnectRequest, uv.StatusCode) -> None) |
                          ((Any, uv.ConnectRequest, uv.StatusCode) -> None)

        :returns: connect request
        :rtype: uv.ConnectRequest
        """
        if self.closing: raise HandleClosedError()
        request = ConnectRequest(stream, on_connect)
        c_storage = c_create_sockaddr(*address)
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        self._family = c_sockaddr.sa_family
        uv_tcp = self.uv_tcp
        code = lib.uv_tcp_connect(request.uv_connect, uv_tcp, c_sockaddr, uv_connect_cb)
        if code < 0:
            request.destroy()
            raise UVError(code)
        return request
