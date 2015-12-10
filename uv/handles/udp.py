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

from ..library import ffi, lib, detach

from ..common import Enumeration, dummy_callback
from ..dns import c_create_sockaddr, unpack_sockaddr
from ..error import UVError, HandleClosedError, StatusCode
from ..handle import HandleType, Handle
from ..request import RequestType, Request
from ..buffers import Buffers

__all__ = ['UDPFlags', 'UDPMembership', 'UDP', 'SendRequest']


class UDPFlags(Enumeration):
    """ """
    IPV6ONLY = lib.UV_UDP_IPV6ONLY
    """
    Disable dual stack support.

    :type: int
    """
    PARTIAL = lib.UV_UDP_PARTIAL
    """
    Indicates message was truncated because read buffer was too small. The
    remainder was discarded by the OS.

    :type: int
    """
    REUSEADDR = lib.UV_UDP_REUSEADDR
    """
    Indicates if `SO_REUSEADDR` will be set when binding the handle. This sets
    the `SO_REUSEPORT` socket flag on the BSDs and OSX. On other Unix platforms,
    it sets the `SO_REUSEADDR` flag. What that means is that multiple threads or
    processes can bind to the same address without error (provided they all set
    the flag) but only the last one to bind will receive any traffic, in effect
    "stealing" the port from the previous listener.

    :type: int
    """


class UDPMembership(Enumeration):
    """ """
    LEAVE_GROUP = lib.UV_LEAVE_GROUP
    """
    Leave group.
    """
    JOIN_GROUP = lib.UV_JOIN_GROUP
    """
    Join group.
    """


@ffi.callback('uv_udp_send_cb')
def uv_udp_send_cb(uv_request, status):
    request = detach(uv_request)
    request.destroy()
    with request.loop.callback_context:
        request.on_send(request, status)


@RequestType.SEND
class SendRequest(Request):
    """
    UDP send request.

    :raises uv.UVError: error while initializing the request
    :raises uv.HandleClosedError: udp handle has already been closed or is closing

    :param udp: udp handle the request should run on
    :param buffers: buffers or buffer to send
    :param address: address of the remote peer `(ip, port, flowinfo=0, scope_id=0)`
    :param on_send: callback called after all data has been sent

    :type udp: uv.UDP
    :type buffers: list[bytes] | bytes
    :type address: tuple | uv.Address
    :type on_send: ((uv.SendRequest, uv.StatusCode) -> None) |
                   ((Any, uv.SendRequest, uv.StatusCode) -> None)
    """

    __slots__ = ['uv_send', 'buffers', 'udp', 'on_send']

    def __init__(self, udp, buffers, address, on_send=None):
        if stream.closing: raise HandleClosedError()
        self.uv_send = ffi.new('uv_udp_send_t*')
        super(SendRequest, self).__init__(self.uv_send, udp.loop)
        self.buffers = Buffers(buffers)
        self.udp = udp
        """
        UDP handle this request belongs to.

        :readonly: True
        :type: uv.UDP
        """
        self.on_send = on_send or dummy_callback
        """
        Callback called after all data has been sent.

        .. function: on_write(Send-Request, Status)

        :readonly: False
        :type: ((uv.SendRequest, uv.StatusCode) -> None) |
               ((Any, uv.SendRequest, uv.StatusCode) -> None)
        """
        uv_udp = self.udp.uv_udp
        c_buffers, uv_buffers = self.buffers
        c_storage = c_create_sockaddr(*address)
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        code = lib.uv_udp_send(self.uv_send, uv_udp, uv_buffers, len(self.buffers),
                               c_sockaddr, uv_udp_send_cb)
        if code < 0:
            self.destroy()
            raise UVError(code)


@ffi.callback('uv_udp_recv_cb')
def uv_udp_recv_cb(uv_udp, length, uv_buf, c_sockaddr, flags):
    udp = detach(uv_udp)
    data = udp.loop.allocator.finalize(uv_udp, length, uv_buf)
    length, status = (0, length) if length < 0 else (length, StatusCode.SUCCESS)
    address = unpack_sockaddr(c_sockaddr)
    with udp.loop.callback_context:
        udp.on_receive(udp, status, address, length, data, flags)


@HandleType.UDP
class UDP(Handle):
    """
    UDP handles encapsulate UDP communication for both clients and servers.

    :raises uv.UVError: error while initializing the handle

    :param flags: udp flags to be used
    :param loop: event loop the handle should run on
    :param on_receive: callback called after package has been received

    :type flags: int
    :type loop: uv.Loop
    :type on_receive: ((uv.UDP, uv.StatusCode, uv.Address, int, bytes, int) -> None) |
                      ((Any, uv.UDP, uv.StatusCode, uv.Address, int, bytes, int) -> None)
    """

    __slots__ = ['uv_udp', 'on_receive']

    def __init__(self, flags=0, loop=None, on_receive=None):
        self.uv_udp = ffi.new('uv_tcp_t*')
        super(UDP, self).__init__(self.uv_udp, loop)
        self.on_receive = on_receive or dummy_callback
        """
        Callback called after package has been received.

        .. function:: on_receive(UDP, Status, Address, Length, Data, Flags)

        :readonly: False
        :type: ((uv.UDP, uv.StatusCode, uv.Address, int, bytes, int) -> None) |
               ((Any, uv.UDP, uv.StatusCode, uv.Address, int, bytes, int) -> None)
        """
        code = lib.uv_udp_init_ex(self.loop.uv_loop, self.uv_udp, flags)
        if code < 0:
            self.destroy()
            raise UVError(code)

    def open(self, fd):
        """
        Open an existing file descriptor as a udp handle.

        :raises uv.UVError: error while opening the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param fd: file descriptor
        :type fd: int
        """
        if self.closing: raise HandleClosedError()
        code = lib.cross_uv_udp_open(self.uv_udp, fd)
        if code < 0: raise UVError(code)

    def set_membership(self, multicast_address, interface_address, membership):
        """
        Set membership for a multicast address

        raises uv.UVError: error while setting membership
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param multicast_address: multicast address to set membership for
        :param interface_address: interface address
        :param membership: membership operation

        :type multicast_address: str
        :type interface_address: str
        :type membership: uv.UDPMembership
        """
        if self.closing: raise HandleClosedError()
        c_m_addr = multicast_address.encode()
        c_i_addr = interface_address.encode()
        code = lib.uv_udp_set_membership(self.uv_udp, c_m_addr, c_i_addr, membership)
        if code < 0: raise UVError(code)

    def set_multicast_loop(self, enable):
        """
        Set IP multicast loop flag. Makes multicast packets loop back to local sockets.

        :raises uv.UVError: error enabling / disabling multicast loop
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param enable: enable / disable multicast loop
        :type enable: bool
        """
        if self.closing: raise HandleClosedError()
        code = lib.uv_udp_set_multicast_loop(self.uv_udp, int(enable))
        if code < 0: raise UVError(code)

    def set_multicast_ttl(self, ttl):
        """
        Set the multicast ttl.

        :raises uv.UVError: error while setting ttl
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param ttl: multicast ttl (1 trough 255)
        :type ttl: int
        """
        if self.closing: raise HandleClosedError()
        code = lib.uv_udp_set_multicast_ttl(self.uv_udp, ttl)
        if code < 0: raise UVError(code)

    def set_multicast_interface(self, interface):
        """
        Set the multicast interface to send or receive data on.

        :raises uv.UVError: error while setting multicast interface
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param interface: multicast interface address
        :type interface: str
        """
        if self.closing: raise HandleClosedError()
        code = lib.uv_udp_set_multicast_interface(self.uv_udp, interface.encode())
        if code < 0: raise UVError(code)

    def set_broadcast(self, enable):
        """
        Set broadcast on or off.

        :raises uv.UVError: error enabling / disabling broadcast
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param enable: enable / disable broadcast
        :type enable: bool
        """
        if self.closing: raise HandleClosedError()
        code = lib.uv_udp_set_broadcast(self.uv_udp, int(enable))
        if code < 0: raise UVError(code)

    @property
    def family(self):
        """
        Address family UDP handle, may be None.

        :type: int | None
        """
        if self.closing: return None
        c_storage = ffi.new('struct sockaddr_storage*')
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        c_size = ffi.new('int*', ffi.sizeof('struct sockaddr_storage'))
        code = lib.uv_udp_getsockname(self.uv_udp, c_sockaddr, c_size)
        if code < 0: return None
        return c_sockaddr.sa_family

    @property
    def sockname(self):
        """
        The local IP and port of the UDP handle.

        :raises uv.UVError: error while receiving sockname
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :readonly: True
        :rtype: uv.Address4 | uv.Address6
        """
        if self.closing: raise HandleClosedError()
        c_storage = ffi.new('struct sockaddr_storage*')
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        c_size = ffi.new('int*', ffi.sizeof('struct sockaddr_storage'))
        code = lib.uv_udp_getsockname(self.uv_udp, c_sockaddr, c_size)
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
        :param flags: bind flags to be used (mask of :class:`uv.TCPBindFlags`)

        :type address: tuple | uv.Address
        :type flags: int
        """
        if self.closing: raise HandleClosedError()
        c_storage = c_create_sockaddr(*address)
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        code = lib.uv_udp_bind(self.uv_udp, c_sockaddr, flags)
        if code < 0: raise UVError(code)

    def send(self, buffers, address, on_send=None):
        """
        Send data over the UDP socket. If the socket has not previously been
        bound with `bind()` it will be bound to 0.0.0.0 (the "all interfaces"
        IPv4 address) and a random port number.

        :raises uv.UVError: error while initializing the request
        :raises uv.HandleClosedError: udp handle has already been closed or is closing

        :param buffers: buffers or buffer to send
        :param address: address of the remote peer `(ip, port, flowinfo=0, scope_id=0)`
        :param on_send: callback called after all data has been sent

        :type buffers: list[bytes] | bytes
        :type address: tuple | uv.Address
        :type on_send: ((uv.SendRequest, uv.StatusCode) -> None) |
                       ((Any, uv.SendRequest, uv.StatusCode) -> None)

        :returns: send request
        :rtype: uv.SendRequest
        """
        return SendRequest(self, buffers, address, on_send)

    def try_send(self, buffers, address):
        """
        Same as `send()`, but won’t queue a write request if it
        cannot be completed immediately.

        :raises uv.UVError: error while sending data
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param buffers: buffers or buffer to send
        :param address: address tuple `(ip, port, flowinfo=0, scope_id=0)`

        :type buffers: list[bytes] | bytes
        :type address: tuple | uv.Address

        :return: number of bytes sent
        :rtype: int
        """
        if self.closing: raise HandleClosedError()
        c_storage = c_create_sockaddr(*address)
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        c_buffers, uv_buffers = Buffers(buffers)
        code = lib.uv_udp_try_send(self.uv_udp, uv_buffers, len(buffers), c_sockaddr)
        if code < 0: raise UVError(code)
        return code

    def receive_start(self, on_receive=None):
        """
        Prepare for receiving data. If the socket has not previously been bound
        with `bind()` it is bound to 0.0.0.0 (the "all interfaces" IPv4 address)
        and a random port number.

        :raises uv.UVError: error while start receiving datagrams
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param on_receive: callback called after package has been received
        :type on_receive:
            ((uv.UDP, uv.StatusCode, uv.Address, int, bytes, int) -> None) |
            ((Any, uv.UDP, uv.StatusCode, uv.Address, int, bytes, int) -> None)
        """
        if self.closing: raise HandleClosedError()
        self.on_receive = on_receive or self.on_receive
        uv_alloc_cb = self.loop.allocator.uv_alloc_cb
        code = lib.uv_udp_recv_start(self.uv_udp, uv_alloc_cb, uv_udp_recv_cb)
        if code < 0: raise UVError(code)

    def receive_stop(self):
        """
        Stop listening for incoming datagrams.

        :raises uv.UVError: error while stop listening for incoming datagrams
        """
        if self.closing: return
        code = lib.uv_udp_recv_stop(self.uv_udp)
        if code < 0: raise UVError(code)
