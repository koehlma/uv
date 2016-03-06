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

from .. import base, common, dns, error, handle, library, request
from ..library import ffi, lib


class UDPFlags(common.Enumeration):
    """
    UDP configuration and status flags enumeration.
    """

    IPV6ONLY = lib.UV_UDP_IPV6ONLY
    """
    Disable dual stack support.

    :type: uv.UDPFlags
    """

    REUSEADDR = lib.UV_UDP_REUSEADDR
    """
    Enable `SO_REUSEADDR` when binding the handle. This sets the
    `SO_REUSEPORT` socket flag on the BSDs and OSX. On other Unix
    platforms, it sets the `SO_REUSEADDR` flag. This allows multiple
    threads or processes to bind to the same address without errors
    (provided that they all set the flag) but only the last one will
    receive any traffic, in effect "stealing" the port from the
    previous listener.

    :type: uv.UDPFlags
    """

    PARTIAL = lib.UV_UDP_PARTIAL
    """
    Indicates that the received message has been truncated because the
    read buffer was too small. The remainder was discarded by the OS.

    :type: uv.UDPFlags
    """


class UDPMembership(common.Enumeration):
    """
    Membership types enumeration for multicast addresses.
    """

    LEAVE_GROUP = lib.UV_LEAVE_GROUP
    """
    Leave multicast group.

    :type: uv.UDPMembership
    """

    JOIN_GROUP = lib.UV_JOIN_GROUP
    """
    Join multicast group.

    :type: uv.UDPMembership
    """


@base.request_callback('uv_udp_send_cb')
def uv_udp_send_cb(send_request, status):
    """
    :type send_request:
        uv.SendRequest
    :type status:
        int
    """
    send_request.on_send(send_request, status)


@request.RequestType.UDP_SEND
class UDPSendRequest(request.UVRequest):
    """
    Request to send a UDP datagram.

    :raises uv.UVError:
        error while initializing the request
    :raises uv.ClosedHandleError:
        udp handle has already been closed or is closing

    :param udp:
        udp handle the request should run on
    :param buffers:
        buffers or buffer to send
    :param address:
        address of the remote peer `(ip, port, flowinfo=0, scope_id=0)`
    :param on_send:
        callback called after all data has been sent

    :type udp:
        uv.UDP
    :type buffers:
        list[bytes] | bytes
    :type address:
        tuple | uv.Address
    :type on_send:
        ((uv.SendRequest, uv.StatusCode) -> None) |
        ((Any, uv.SendRequest, uv.StatusCode) -> None)
    """

    __slots__ = ['uv_send', 'uv_buffers', 'udp', 'on_send']

    uv_request_type = 'uv_udp_send_t*'
    uv_request_init = lib.uv_udp_send

    def __init__(self, udp, buffers, address, on_send=None):
        if udp.closing:
            raise error.ClosedHandleError()
        self.uv_buffers = library.make_uv_buffers(buffers)
        self.udp = udp
        """
        UDP handle the request belongs to.

        :readonly:
            True
        :type:
            uv.UDP
        """
        self.on_send = on_send or common.dummy_callback
        """
        Callback which should run after all data has been sent.


        .. function: on_send(send_request, status)

                :param send_request:
                    request the call originates from
                :param status:
                    status of the request

                :type send_request:
                    uv.UDPSendRequest
                :type status:
                    uv.StatusCode


        :readonly:
            False
        :type:
            ((uv.UDPSendRequest, uv.StatusCode) -> None) |
            ((Any, uv.UDPSendRequest, uv.StatusCode) -> None)
        """
        uv_udp = self.udp.uv_udp
        c_sockaddr = dns.make_c_sockaddr(*address)
        arguments = (self.uv_buffers, len(self.uv_buffers), c_sockaddr, uv_udp_send_cb)
        super(UDPSendRequest, self).__init__(udp.loop, arguments, uv_udp)


@base.handle_callback('uv_udp_recv_cb')
def uv_udp_recv_cb(udp_handle, length, uv_buffer, c_sockaddr, flags):
    """
    :type udp_handle:
        uv.UDP
    :type length:
        int
    :type uv_buffer:
        ffi.CData[uv_buf_t*]
    :type c_sockaddr:
        ffi.CData[struct sockaddr*]
    :type flags:
        int
    """
    data = udp_handle.loop.allocator.finalize(udp_handle, length, uv_buffer)
    if length < 0:  # pragma: no cover
        status = error.StatusCodes.get(length)
    else:
        status = error.StatusCodes.SUCCESS
    if c_sockaddr:
        address = dns.unpack_sockaddr(c_sockaddr)
    else:  # pragma: no cover
        address = None
    udp_handle.on_receive(udp_handle, status, address, data, flags)


@handle.HandleTypes.UDP
class UDP(handle.UVHandle):
    """
    Abstraction of UDP sockets for servers and clients.

    :raises uv.UVError:
        error while initializing the handle

    :param flags:
        udp flags to be used
    :param loop:
        event loop the handle should run on
    :param on_receive:
        callback called after package has been received

    :type flags:
        int
    :type loop:
        uv.Loop
    :type on_receive:
        ((uv.UDP, uv.StatusCode, uv.Address, bytes, int) -> None) |
        ((Any, uv.UDP, uv.StatusCode, uv.Address, bytes, int) -> None)
    """

    __slots__ = ['uv_udp', 'on_receive']

    uv_handle_type = 'uv_udp_t*'
    uv_handle_init = lib.uv_udp_init_ex

    def __init__(self, flags=0, loop=None, on_receive=None):
        super(UDP, self).__init__(loop, (flags, ))
        self.uv_udp = self.base_handle.uv_object
        self.on_receive = on_receive or common.dummy_callback
        """
        Callback called after package has been received.


        .. function:: on_receive(udp_handle, status, addr, data, flags)

            :param udp_handle:
                handle the call originates from
            :param status:
                status of the handle (indicate any errors)
            :param addr:
                address the data originates from
            :param data:
                data which has been received
            :param flags:
                udp status flags (e.g. partial read)

            :type udp_handle:
                uv.UDP
            :type status:
                uv.StatusCode
            :type addr:
                uv.Address4 | uv.Address6 | tuple
            :type flags:
                int


        :readonly:
            False
        :type:
            ((uv.UDP, uv.StatusCode, uv.Address, bytes,
              int) -> None) |
            ((Any, uv.UDP, uv.StatusCode, uv.Address, bytes,
              int) -> None)
        """

    def open(self, fd):
        """
        Open an existing file descriptor as an udp handle.

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
        code = lib.cross_uv_udp_open(self.uv_udp, fd)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def bind(self, address, flags=0):
        """
        Bind the socket to the specified address.

        :raises uv.UVError:
            error while binding to `address`
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param address:
            address to bind to `(ip, port, flowinfo=0, scope_id=0)`
        :param flags
            bind flags to be used (mask of :class:`uv.UDPFlags`)

        :type address:
            uv.Address4 | uv.Address6 | tuple
        :type flags:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        code = lib.uv_udp_bind(self.uv_udp, dns.make_c_sockaddr(*address), flags)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def send(self, buffers, address, on_send=None):
        """
        Send data over the UDP socket. If the socket has not previously
        been bound with `bind()` it will be bound to 0.0.0.0 (the "all
        interfaces" IPv4 address) and a random port number.

        :raises uv.UVError:
            error while initializing the request
        :raises uv.ClosedHandleError:
            udp handle has already been closed or is closing

        :param buffers:
            data which should be send
        :param address:
            address tuple `(ip, port, flowinfo=0, scope_id=0)`
        :param on_send:
            callback called after all data has been sent

        :type buffers:
            tuple[bytes] | list[bytes] | bytes
        :type address:
            tuple | uv.Address4 | uv.Address6
        :type on_send:
            ((uv.UDPSendRequest, uv.StatusCode) -> None) |
            ((Any, uv.UDPSendRequest, uv.StatusCode) -> None)

        :rtype:
            uv.UDPSendRequest
        """
        return UDPSendRequest(self, buffers, address, on_send)

    def try_send(self, buffers, address):
        """
        Same as `send()`, but won’t queue a write request if it cannot
        be completed immediately.

        :raises uv.UVError:
            error while sending data
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param buffers:
            data which should be send
        :param address:
            address tuple `(ip, port, flowinfo=0, scope_id=0)`

        :type buffers:
            tuple[bytes] | list[bytes] | bytes
        :type address:
            tuple | uv.Address4 | uv.Address6

        :return:
            number of bytes sent
        :rtype:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        c_sockaddr = dns.make_c_sockaddr(*address)
        uv_buffers = library.make_uv_buffers(buffers)
        code = lib.uv_udp_try_send(self.uv_udp, uv_buffers, len(uv_buffers), c_sockaddr)
        if code < 0:  # pragma: no cover
            raise error.UVError(code)
        return code

    def receive_start(self, on_receive=None):
        """
        Prepare for receiving data. If the socket has not previously
        been bound with `bind()` it is bound to 0.0.0.0 (the "all
        interfaces" IPv4 address) and a random port number.

        :raises uv.UVError:
            error while start receiving datagrams
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param on_receive:
            callback called after package has been received

        :type on_receive:
            ((uv.UDP, uv.StatusCode, uv.Address, bytes,
              int) -> None) |
            ((Any, uv.UDP, uv.StatusCode, uv.Address, bytes,
              int) -> None)
        """
        if self.closing:
            raise error.ClosedHandleError()
        self.on_receive = on_receive or self.on_receive
        code = lib.uv_udp_recv_start(self.uv_udp, handle.uv_alloc_cb, uv_udp_recv_cb)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.set_pending()

    def receive_stop(self):
        """
        Stop listening for incoming datagrams.

        :raises uv.UVError:
            error while stop listening for incoming datagrams
        """
        if self.closing:
            return
        code = lib.uv_udp_recv_stop(self.uv_udp)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.clear_pending()

    def set_membership(self, multicast_address, membership, interface_address=None):
        """
        Set membership for a multicast address

        raises uv.UVError:
            error while setting membership
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param multicast_address:
            multicast address to set membership for
        :param membership:
            membership operation
        :param interface_address:
            interface address

        :type multicast_address:
            unicode
        :type membership:
            uv.UDPMembership
        :type interface_address:
            unicode
        """
        if self.closing:
            raise error.ClosedHandleError()
        c_m_addr = multicast_address.encode()
        c_i_addr = interface_address.encode() if interface_address else ffi.NULL
        code = lib.uv_udp_set_membership(self.uv_udp, c_m_addr, c_i_addr, membership)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def set_multicast_loop(self, enable):
        """
        Set IP multicast loop flag. Makes multicast packets loop bac
        to local sockets.

        :raises uv.UVError:
            error enabling / disabling multicast loop
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param enable:
            enable / disable multicast loop

        :type enable:
            bool
        """
        if self.closing:
            raise error.ClosedHandleError()
        code = lib.uv_udp_set_multicast_loop(self.uv_udp, int(enable))
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def set_multicast_ttl(self, ttl):
        """
        Set the multicast ttl.

        :raises uv.UVError:
            error while setting ttl
        :raises uv.ClosedHandleError
            handle has already been closed or is closing

        :param ttl:
            multicast ttl (between 1 and 255)

        :type ttl:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        code = lib.uv_udp_set_multicast_ttl(self.uv_udp, ttl)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def set_multicast_interface(self, interface):
        """
        Set the multicast interface to send or receive data on.

        :raises uv.UVError:
            error while setting multicast interface
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param interface:
            multicast interface address

        :type interface:
            unicode
        """
        if self.closing:
            raise error.ClosedHandleError()
        code = lib.uv_udp_set_multicast_interface(self.uv_udp, interface.encode())
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def set_broadcast(self, enable):
        """
        Set broadcast on or off.

        :raises uv.UVError:
            error enabling / disabling broadcast
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param enable:
            enable / disable broadcast

        :type enable:
            bool
        """
        if self.closing:
            raise error.ClosedHandleError()
        code = lib.uv_udp_set_broadcast(self.uv_udp, int(enable))
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    @property
    def family(self):
        """
        Address family of UDP handle, may be None.

        :readonly:
            True
        :rtype:
            int | None
        """
        if self.closing:
            return None
        c_storage = ffi.new('struct sockaddr_storage*')
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        c_size = ffi.new('int*', ffi.sizeof('struct sockaddr_storage'))
        code = lib.uv_udp_getsockname(self.uv_udp, c_sockaddr, c_size)
        if code != error.StatusCodes.SUCCESS:
            return None
        return c_sockaddr.sa_family

    @property
    def sockname(self):
        """
        The local IP and port of the UDP handle.

        :raises uv.UVError:
            error while receiving sockname

        :readonly:
            True
        :rtype:
            uv.Address4 | uv.Address6
        """
        if self.closing:
            return '0.0.0.0', 0
        c_storage = ffi.new('struct sockaddr_storage*')
        c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
        c_size = ffi.new('int*', ffi.sizeof('struct sockaddr_storage'))
        code = lib.uv_udp_getsockname(self.uv_udp, c_sockaddr, c_size)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        return dns.unpack_sockaddr(c_sockaddr)
