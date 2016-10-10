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
import warnings

from . import base, common, error, library, request
from .library import ffi, lib


class AddressFamilies(common.Enumeration):
    """
    Address Families
    """

    UNKNOWN = socket.AF_UNSPEC
    """
    Unknown or unspecified family.

    :type: uv.AddressFamilies
    """

    INET4 = socket.AF_INET
    """
    Internet protocol version 4 family.

    :type: uv.AddressFamilies
    """

    INET6 = socket.AF_INET6
    """
    Internet protocol version 6 family.

    :type: uv.AddressFamilies
    """

    UNIX = getattr(socket, 'AF_UNIX', -1)
    """
    Unix domain sockets family.

    :type: uv.AddressFamilies
    """


class SocketTypes(common.Enumeration):
    """
    Socket Types
    """

    STREAM = socket.SOCK_STREAM
    """
    Stream socket type.

    :type: uv.SocketTypes
    """

    DRGAM = socket.SOCK_DGRAM
    """
    Datagram socket type.

    :type: uv.SocketTypes
    """

    RAW = socket.SOCK_RAW
    """
    Raw socket type.

    :type: uv.SocketTypes
    """

    RDM = socket.SOCK_RDM
    """
    Pragmatic general multicast socket type.

    :type: uv.SocketTypes
    """

    SEQPACKET = socket.SOCK_SEQPACKET
    """
    Sequence packet socket type.

    :type: uv.SocketTypes
    """


class SocketProtocols(common.Enumeration):
    """
    Socket Protocols
    """

    TCP = getattr(socket, 'IPPROTO_TCP', 6)
    """
    Transmission control protocol.

    :type: uv.SocketProtocols
    """

    UDP = getattr(socket, 'IPPROTO_UDP', 17)
    """
    User datagram protocol.

    :type: uv.SocketProtocols
    """

    RAW = getattr(socket, 'IPPROTO_RAW', 255)
    """
    Raw socket protocol.

    :type: uv.SocketProtocols
    """

    ICMP4 = getattr(socket, 'IPPROTO_ICMP', 1)
    """
    Internet version 4 control message protocol.

    :type: uv.SocketProtocols
    """

    ICMP6 = getattr(socket, 'IPPROTO_ICMPV6', 58)
    """
    Internet version 6 control message protocol.

    :type: uv.SocketProtocols
    """


class Address(tuple):
    """
    Internet Protocol Address
    """

    __slots__ = []

    def __new__(cls, host, port):
        return tuple.__new__(cls, (host, port))

    @property
    def host(self):
        """
        Address Host

        :rtype:
            unicode
        """
        return self[0]

    @property
    def port(self):
        """
        Address Port

        :rtype:
            int
        """
        return self[1]


class Address4(Address):
    """
    Internet protocol version 4 address.
    """

    __slots__ = []

    family = AddressFamilies.INET4
    """
    Address Family
    """

    def __repr__(self):
        return '<Address4 host="{self.host}", port={self.port}>'.format(self=self)


class Address6(Address):
    """
    Internet protocol version 6 address.
    """

    __slots__ = []

    family = AddressFamilies.INET6
    """
    Address Family
    """

    def __new__(cls, host, port, flowinfo=0, scope_id=0):
        return tuple.__new__(cls, (host, port, flowinfo, scope_id))

    def __repr__(self):
        return ('<Address6 host="{self.host}", port={self.port}, '
                'flowinfo={self.flowinfo}, scope_id={self.scope_id}>').format(self=self)

    @property
    def flowinfo(self):
        """
        Address Flow Information

        :rtype:
            int
        """
        return self[2]

    @property
    def scope_id(self):
        """
        Address Scope Id

        :rtype:
            int
        """
        return self[3]


class AddrInfo(tuple):
    """
    Address Information
    """

    __slots__ = []

    def __new__(cls, family, socktype, protocol, canonname, address):
        return tuple.__new__(cls, (AddressFamilies.get(family),
                                   SocketTypes.get(socktype),
                                   SocketProtocols.get(protocol),
                                   canonname, address))

    def __repr__(self):
        return ('<AddressInfo family={self.family!r}, type={self.type!r}, '
                'protocol={self.protocol!r}, canonname="{self.canonname}", '
                'address={self.address!r}>').format(self=self)

    @property
    def family(self):
        """
        Address Family

        :rtype:
            uv.AddressFamilies | int
        """
        return self[0]

    @property
    def socktype(self):
        """
        Socket Type

        :rtype:
            uv.SocketTypes | int
        """
        return self[1]

    @property
    def protocol(self):
        """
        Socket Protocol

        :rtype:
            uv.SocketProtocols | int
        """
        return self[2]

    @property
    def canonname(self):
        """
        Canonical Name

        :rtype:
            unicode | None
        """

        return self[3]

    @property
    def address(self):
        """
        Address

        :rtype:
            uv.Address | tuple | None
        """
        return self[4]


class NameInfo(tuple):
    """
    Name Information
    """

    __slots__ = []

    def __new__(cls, hostname, service):
        return tuple.__new__(cls, (hostname, service))

    def __repr__(self):
        return ('<NameInfo hostname="{self.hostname}", service="{self.service}">'
                ).format(self=self)

    @property
    def hostname(self):
        """
        Hostname

        :rtype:
            unicode
        """
        return self[0]

    @property
    def service(self):
        """
        Service-Name

        :rtype:
            unicode
        """
        return self[1]


def unpack_addrinfo(c_addrinfo):
    """
    :type c_addrinfo:
        ffi.CDate[struct  addrinfo*]
    """
    items, c_next = [], c_addrinfo

    while c_next:
        family = c_next.ai_family
        socktype = c_next.ai_socktype
        protocol = c_next.ai_protocol
        if c_next.ai_canonname:
            canonname = ffi.string(c_next.ai_canonname).decode()
        else:
            canonname = None
        address = unpack_sockaddr(c_next.ai_addr) if c_next.ai_addr else None
        items.append(AddrInfo(family, socktype, protocol, canonname, address))
        c_next = c_next.ai_next

    if c_addrinfo:
        lib.uv_freeaddrinfo(c_addrinfo)

    return items


def unpack_sockaddr(c_sockaddr):
    """
    :type c_sockaddr:
        ffi.CData[struct sockaddr*]
    """
    if c_sockaddr.sa_family == socket.AF_INET:
        c_sockaddr_in4 = ffi.cast('struct sockaddr_in*', c_sockaddr)

        c_host = ffi.new('char[16]')

        port = socket.ntohs(c_sockaddr_in4.sin_port)
        lib.uv_ip4_name(c_sockaddr_in4, c_host, 16)

        return Address4(ffi.string(c_host).decode(), port)
    elif c_sockaddr.sa_family == socket.AF_INET6:
        c_sockaddr_in6 = ffi.cast('struct sockaddr_in6*', c_sockaddr)

        c_additional = lib.cross_get_ipv6_additional(c_sockaddr_in6)
        c_host = ffi.new('char[40]')

        flowinfo = c_additional.flowinfo
        scope_id = c_additional.scope_id
        port = socket.ntohs(c_sockaddr_in6.sin6_port)
        lib.uv_ip6_name(c_sockaddr_in6, c_host, 40)

        return Address6(ffi.string(c_host).decode(), port, flowinfo, scope_id)


@base.request_callback('uv_getaddrinfo_cb')
def uv_getaddrinfo_cb(addrinfo_request, status, _):
    """
    :type addrinfo_request:
        uv.GetAddrInfo
    :type status:
        int
    :type _:
        Any
    """
    if status == error.StatusCodes.SUCCESS:
        addrinfo_request.populate()
    code = error.StatusCodes.get(status)
    addrinfo = addrinfo_request.addrinfo
    addrinfo_request.callback(addrinfo_request, code, addrinfo)


@request.RequestType.GETADDRINFO
class GetAddrInfo(request.UVRequest):
    """
    Request to get address information for specified host and port
    (service). If no callback is provided the request is executed
    synchronously.

    :raises uv.UVError:
        error while initializing the handle

    :param host:
        host to get address information for
    :param port:
        port (service) to get address information for
    :param family:
        address family hint
    :param socktype:
        socket type hint
    :param protocol:
        protocol type hint
    :param flags:
        flags to configure the behavior of `getaddrinfo()`
    :param callback:
        callback which should be called after address information
        has been fetched or on error
    :param loop:
        event loop the request should run on

    :type host:
        unicode
    :type port:
        int
    :type family:
        uv.AddressFamilies | int
    :type socktype:
        uv.SocketTypes | int
    :type protocol:
        uv.SocketProtocols | int
    :type flags:
        int
    :type callback:
        ((uv.GetAddrInfo, uv.StatusCodes, list[uv.AddrInfo])
         -> None) |
        ((Any, uv.GetAddrInfo, uv.StatusCodes, list[uv.AddrInfo])
         -> None) | None
    :type loop:
        uv.Loop
    """

    __slots__ = ['uv_getaddrinfo', 'callback', 'host', 'port', 'hints',
                 'flags', 'addrinfo']

    uv_request_type = 'uv_getaddrinfo_t*'
    uv_request_init = lib.uv_getaddrinfo

    def __init__(self, host, port, family=0, socktype=0, protocol=0,
                 flags=0, callback=None, loop=None):
        c_hints = ffi.new('struct addrinfo*')
        c_hints.ai_family = family
        c_hints.ai_socktype = socktype
        c_hints.ai_protocol = protocol
        c_hints.ai_flags = flags

        self.callback = callback or common.dummy_callback
        """
        Callback which should be called after address information has
        been fetched or on error.


        .. function:: callback(request, code, addrinfo)

            :param request:
                request the call originates from
            :param code:
                status of the request
            :param addrinfo:
                list of fetched address information objects

            :type request:
                uv.GetAddrInfo
            :type code:
                uv.StatusCodes
            :type addrinfo:
                list[uv.AddrInfo]


        :readonly:
            False
        :type:
            ((uv.GetAddrInfo, uv.StatusCodes, list[uv.AddrInfo])
             -> None) |
            ((Any, uv.GetAddrInfo, uv.StatusCodes, list[uv.AddrInfo])
             -> None)
        """
        self.host = host
        """
        Host to get address information for.

        :readonly:
            True
        :type:
            unicode
        """
        self.port = port
        """
        Port (service) to get address information for.

        :readonly:
            True
        :type:
            int
        """
        self.hints = AddrInfo(family, socktype, protocol, None, None)
        """
        Address information hints.

        :readonly:
            True
        :type:
            uv.AddrInfo
        """
        self.flags = flags
        """
        Flags to configure the behavior of `getaddrinfo()`.

        :readonly:
            True
        :type:
            int
        """
        self.addrinfo = []
        """
        Resulting list with address information. Is populated with
        address information objects after the request has been
        successfully completed.

        :readonly:
            True
        :type:
            list[uv.AddrInfo]
        """

        uv_callback = ffi.NULL if callback is None else uv_getaddrinfo_cb
        arguments = uv_callback, host.encode(), str(port).encode(), c_hints
        super(GetAddrInfo, self).__init__(loop, arguments)

        self.uv_getaddrinfo = self.base_request.uv_object
        if callback is None:
            self.populate()
            base.finalize_request(self)

    def populate(self):
        """
        Populate the address information list.

        .. warning::
            Only for internal purposes!
        """
        if self.uv_getaddrinfo.addrinfo:
            self.addrinfo = unpack_addrinfo(self.uv_getaddrinfo.addrinfo)
            self.uv_getaddrinfo.addrinfo = ffi.NULL


def getaddrinfo(host, port, family=0, socktype=0, protocol=0, flags=0,
                callback=None, loop=None):
    """
    Get address information for specified host and port (service).

    See :class:`uv.dns.GetAddrInfo` for parameter descriptions.

    :type host:
        unicode
    :type port:
        int
    :type family:
        uv.AddressFamilies | int
    :type socktype:
        uv.SocketTypes | int
    :type protocol:
        uv.SocketProtocols | int
    :type flags:
        int
    :type callback:
        ((uv.GetAddrInfo, uv.StatusCodes, list[uv.AddrInfo])
         -> None) |
        ((Any, uv.GetAddrInfo, uv.StatusCodes, list[uv.AddrInfo])
         -> None) | None
    :type loop:
        uv.Loop

    :rtype:
        uv.GetAddrInfo | list[uv.AddrInfo]
    """
    addrinfo = GetAddrInfo(host, port, family, socktype, protocol, flags, callback, loop)
    return addrinfo.addrinfo if callback is None else addrinfo


@base.request_callback('uv_getnameinfo_cb')
def uv_getnameinfo_cb(nameinfo_request, status, c_hostname, c_service):
    """
    :param nameinfo_request:
        uv.GetNameInfo
    :param status:
        int
    :param c_hostname:
        ffi.CData[char*]
    :param c_service:
        ffi.CData[char*]
    """
    hostname = ffi.string(c_hostname).decode()
    service = ffi.string(c_service).decode()
    code = error.StatusCodes.get(status)
    nameinfo_request.callback(nameinfo_request, code, hostname, service)


@request.RequestType.GETNAMEINFO
class GetNameInfo(request.UVRequest):
    """
    Request to get name information for specified ip and port. If no
    callback is provided the request is executed synchronously.

    :param ip:
        IP to get name information for
    :param port:
        port to get name information for
    :param flags:
        flags to configure the behavior of `getnameinfo()`
    :param callback:
        callback which should be called after name information has been
        fetched or on error
    :param loop:
        event loop the request should run on

    :type ip:
        unicode
    :type port:
        int
    :type flags:
        int
    :type callback:
        ((uv.GetNameInfo, uv.StatusCodes, unicode, unicode)
         -> None) |
        ((Any, uv.GetAddrInfo, uv.StatusCodes, unicode, unicode)
         -> None) | None
    :type loop:
        uv.Loop
    """

    __slots__ = ['uv_getnameinfo', 'c_sockaddr', 'callback', 'ip', 'port', 'flags']

    uv_request_type = 'uv_getnameinfo_t*'
    uv_request_init = lib.uv_getnameinfo

    def __init__(self, ip, port, flags=0, callback=None, loop=None):
        self.callback = callback
        """
        Callback which should be called after name information has been
        fetched or on error.


        .. function:: callback(request, code, hostname, service)

            :param request:
                request the call originates from
            :param code:
                status of the request
            :param hostname:
                hostname corresponding to the given IP
            :param service:
                service name corresponding to the given port

            :type request:
                uv.GetNameInfo
            :type code:
                uv.StatusCodes
            :type hostname:
                unicode
            :type service:
                unicode


        :readonly:
            False
        :type:
            ((uv.GetNameInfo, uv.StatusCodes, unicode, unicode)
             -> None) |
            ((Any, uv.GetAddrInfo, uv.StatusCodes, unicode, unicode)
             -> None)
        """
        self.ip = ip
        """
        Ip to get name information for.

        :readonly:
            True
        :type:
            unicode
        """
        self.port = port
        """
        Port to get name information for.

        :readonly:
            True
        :type:
            int
        """
        self.flags = flags
        """
        Flags to configure the behavior of `getnameinfo()`.

        :readonly:
            True
        :type:
            int
        """

        uv_callback = ffi.NULL if callback is None else uv_getnameinfo_cb

        arguments = (uv_callback, make_c_sockaddr(ip, port), flags)
        super(GetNameInfo, self).__init__(loop, arguments)

        self.uv_getnameinfo = self.base_request.uv_object

        if callback is None:
            base.finalize_request(self)

    @property
    def hostname(self):
        """
        Hostname corresponding to the given IP.

        :readonly:
            True
        :type:
            unicode
        """
        if self.uv_getnameinfo.host:
            return ffi.string(self.uv_getnameinfo.host).decode()

    @property
    def service(self):
        """
        Service name corresponding to the given port.

        :readonly:
            True
        :return:
            unicode
        """
        if self.uv_getnameinfo.service:
            return ffi.string(self.uv_getnameinfo.service).decode()


def getnameinfo(ip, port, flags=0, callback=None, loop=None):
    """
    Get name information for specified IP and port.

    See :class:`uv.dns.GetNameInfo` for parameter descriptions.

    :type ip:
        unicode
    :type port:
        int
    :type flags:
        int
    :type callback:
        ((uv.GetNameInfo, uv.StatusCodes, unicode, unicode)
         -> None) |
        ((Any, uv.GetAddrInfo, uv.StatusCodes, unicode, unicode)
         -> None) | None
    :type loop:
        uv.Loop

    :rtype:
        uv.GetNameInfo | uv.NameInfo
    """
    nameinfo = GetNameInfo(ip, port, flags, callback, loop)
    if callback is None:
        return NameInfo(nameinfo.hostname, nameinfo.service)
    return nameinfo


def make_c_sockaddr(ip, port, flowinfo=0, scope_id=0):
    """
    Create a C sockaddr struct form the given information.

    :type ip:
        unicode
    :type port:
        int
    :type flowinfo:
        int
    :type scope_id:
        int
    """
    c_storage = ffi.new('struct sockaddr_storage*')
    c_sockaddr = ffi.cast('struct sockaddr*', c_storage)
    library.c_require(c_sockaddr, c_storage)

    c_ip = ip.encode()

    c_sockaddr_in4 = ffi.cast('struct sockaddr_in*', c_storage)
    code = lib.uv_ip4_addr(c_ip, port, c_sockaddr_in4)
    if code == error.StatusCodes.SUCCESS:
        return c_sockaddr

    c_sockaddr_in6 = ffi.cast('struct sockaddr_in6*', c_storage)
    code = lib.uv_ip6_addr(c_ip, port, c_sockaddr_in6)
    if code != error.StatusCodes.SUCCESS:
        raise error.UVError(code)

    lib.cross_set_ipv6_additional(c_sockaddr_in6, flowinfo, scope_id)
    return c_sockaddr
