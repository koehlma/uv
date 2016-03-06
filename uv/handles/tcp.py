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

import socket

from .. import common, dns, error, handle
from ..library import ffi, lib

from . import stream


class TCPFlags(common.Enumeration):
    """
    TCP configuration enumeration.
    """

    IPV6ONLY = lib.UV_TCP_IPV6ONLY
    """
    Disable dual stack support.

    :type: uv.TCPFlags
    """


class TCPConnectRequest(stream.ConnectRequest):
    """
    TCP specific connect request.

    :param tcp:
        TCP socket to establish a connection on
    :param address:
        address to connect to
    :param on_connect:
        callback which should run after a connection has been
        established or on error

    :type tcp:
        uv.TCP
    :type address:
        uv.Address4 | uv.Address6 | tuple
    :type on_connect:
        ((uv.TCPConnectRequest, uv.StatusCode) -> None) |
        ((Any, uv.TCPConnectRequest, uv.StatusCode) -> None)

    """

    uv_request_init = lib.uv_tcp_connect

    def __init__(self, tcp, address, on_connect=None):
        arguments = (dns.make_c_sockaddr(*address), )
        super(TCPConnectRequest, self).__init__(tcp, arguments, on_connect=on_connect)


@handle.HandleTypes.TCP
class TCP(stream.UVStream):
    """
    Stream interface to TCP sockets for clients and servers.

    :raises uv.UVError:
        error while initializing the handle

    :param flags:
        tcp flags to be used
    :param loop:
        event loop the handle should run on
    :param on_read:
        callback which should be called when data has been read
    :param on_connection:
        callback which should run after a new connection has been made
        or on error (if stream is in listen mode)

    :type flags:
        int
    :type loop:
        uv.Loop
    :type on_read:
        ((uv.TCP, uv.StatusCodes, bytes) -> None) |
        ((Any, uv.TCP, uv.StatusCodes, bytes) -> None)
    :type on_connection:
        ((uv.TCP, uv.StatusCodes, bytes) -> None) |
        ((Any, uv.TCP, uv.StatusCodes, bytes) -> None)
    """

    __slots__ = ['uv_tcp', '_family']

    uv_handle_type = 'uv_tcp_t*'
    uv_handle_init = lib.uv_tcp_init_ex

    def __init__(self, flags=0, loop=None, on_read=None, on_connection=None):
        super(TCP, self).__init__(loop, False, (flags, ), on_read, on_connection)
        self.uv_tcp = self.base_handle.uv_object

    def open(self, fd):
        """
        Open an existing file descriptor as a tcp handle.

        :raises uv.UVError:
            error while opening the handle
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param fd:
            file descriptor

        :type fd:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        code = lib.cross_uv_tcp_open(self.uv_tcp, fd)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def bind(self, address, flags=0):
        """
        Bind the handle to an address. When the port is already taken,
        you can expect to see an :class:`uv.StatusCode.EADDRINUSE`
        error from either `bind()`, `listen()` or `connect()`. That is,
        a successful call to this function does not guarantee that the
        call to `listen()` or `connect()` will succeed as well.

        :raises uv.UVError:
            error while binding to `address`
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param address:
            address to bind to `(ip, port, flowinfo=0, scope_id=0)`
        :param flags:
            bind flags to be used (mask of :class:`uv.TCPFlags`)

        :type address:
            uv.Address4 | uv.Address6 | tuple
        :type flags:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        code = lib.uv_tcp_bind(self.uv_tcp, dns.make_c_sockaddr(*address), flags)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def connect(self, address, on_connect=None):
        """
        Establish an IPv4 or IPv6 TCP connection.

        :raises uv.UVError:
            error while connecting to `address`
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param address:
            address to connect to
        :param on_connect:
            callback which should run after a connection has been
            established or on error

        :type address:
            uv.Address4 | uv.Address6 | tuple
        :type on_connect:
            ((uv.TCPConnectRequest, uv.StatusCode) -> None) |
            ((Any, uv.TCPConnectRequest, uv.StatusCode) -> None)

        :rtype:
            uv.TCPConnectRequest
        """
        return TCPConnectRequest(self, address, on_connect)

    @property
    def sockname(self):
        """
        The current address to which the handle is bound to.

        :raises uv.UVError:
            error while receiving sockname
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :readonly:
            True
        :rtype:
            uv.Address4 | uv.Address6
        """
        if self.closing:
            raise error.ClosedHandleError()
        c_storage = ffi.new('struct sockaddr_storage*')
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        c_size = ffi.new('int*', ffi.sizeof('struct sockaddr_storage'))
        code = lib.uv_tcp_getsockname(self.uv_tcp, c_sockaddr, c_size)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        return dns.unpack_sockaddr(c_sockaddr)

    @property
    def peername(self):
        """
        The address of the peer connected to the handle.

        :raises uv.UVError:
            error while receiving peername
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :readonly:
            True
        :rtype:
            uv.Address4 | uv.Address6
        """
        if self.closing:
            raise error.ClosedHandleError()
        c_storage = ffi.new('struct sockaddr_storage*')
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        c_size = ffi.new('int*', ffi.sizeof('struct sockaddr_storage'))
        code = lib.uv_tcp_getpeername(self.uv_tcp, c_sockaddr, c_size)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        return dns.unpack_sockaddr(c_sockaddr)

    def set_nodelay(self, enable):
        """
        Enable / disable Nagle’s algorithm.

        :raises uv.UVError:
            error enabling / disabling the algorithm
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param enable:
            enable / disable

        :type enable:
            bool
        """
        if self.closing:
            raise error.ClosedHandleError()
        code = lib.uv_tcp_nodelay(self.uv_tcp, int(enable))
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def set_keepalive(self, enable, delay=0):
        """
        Enable / disable TCP keep-alive.

        :raises uv.UVError:
            error enabling / disabling tcp keep-alive
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param enable:
            enable / disable
        :param delay:
            initial delay in seconds

        :type enable:
            bool
        :type delay:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        code = lib.uv_tcp_keepalive(self.uv_tcp, int(enable), delay)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def set_simultaneous_accepts(self, enable):
        """
        Enable / disable simultaneous asynchronous accept requests that
        are queued by the operating system when listening for new TCP
        connections.

        This setting is used to tune a TCP server for the desired
        performance. Having simultaneous accepts can significantly
        improve the rate of accepting connections (which is why it is
        enabled by default) but may lead to uneven load distribution
        in multi-process setups.

        :raises uv.UVError:
            error enabling / disabling simultaneous accepts
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param enable:
            enable / disable

        :type enable:
            bool
        """
        if self.closing:
            raise error.ClosedHandleError()
        code = lib.uv_tcp_simultaneous_accepts(self.uv_tcp, int(enable))
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    @property
    def family(self):
        try:
            sockname = self.sockname
            if isinstance(sockname, dns.Address4):
                return socket.AF_INET
            elif isinstance(sockname, dns.Address6):
                return socket.AF_INET6
        except error.UVError:
            pass
