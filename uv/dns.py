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

from . import common, error, library, request
from .library import ffi, lib

__all__ = ['AddrInfo', 'NameInfo', 'Address', 'Address4', 'Address6', 'GetAddrInfo',
           'getaddrinfo', 'GetNameInfo', 'getnameinfo']


class AddrInfo(tuple):
    """
    Address information.
    """

    __slots__ = []

    def __new__(cls, family, socktype, protocol, canonname, address):
        return tuple.__new__(cls, (family, socktype, protocol, canonname, address))

    def __init__(self, family, socktype, protocol, canonname, address):
        tuple.__init__(self, (family, socktype, protocol, canonname, address))

    @property
    def family(self):
        return self[0]

    @property
    def type(self):
        return self[1]

    @property
    def protocol(self):
        return self[2]

    @property
    def canonname(self):
        return self[3]

    @property
    def address(self):
        return self[4]


class NameInfo(tuple):
    """
    Name information.
    """

    __slots__ = []

    def __new__(cls, host, service):
        return tuple.__new__(cls, (host, service))

    def __init__(self, host, service):
        tuple.__init__(self, (host, service))

    @property
    def host(self):
        return self[0]

    @property
    def service(self):
        return self[1]


class Address(tuple):
    """
    Socket address.
    """

    __slots__ = []

    def __new__(cls, host, port):
        return tuple.__new__(cls, (host, port))

    def __init__(self, host, port):
        tuple.__init__(self, (host, port))

    @property
    def host(self):
        """
        address host

        :rtype: unicode
        """
        return self[0]

    @property
    def port(self):
        """
        address port

        :rtype: int
        """
        return self[1]


class Address4(Address):
    """
    Socket IPv4 address.
    """


class Address6(Address):
    """
    Socket IPv6 address.
    """
    def __new__(cls, host, port, flowinfo=0, scope_id=0):
        return tuple.__new__(cls, (host, port, flowinfo, scope_id))

    def __init__(self, host, port, flowinfo=0, scope_id=0):
        tuple.__init__(self, (host, port, flowinfo, scope_id))

    @property
    def flowinfo(self):
        """
        address flow information

        :rtype: int
        """
        return self[2]

    @property
    def scope_id(self):
        """
        address scope id

        :rtype: int
        """
        return self[3]


def unpack_addrinfo(c_addrinfo):
    items, c_next = [], c_addrinfo

    while c_next:
        family = c_next.ai_family
        socktype = c_next.ai_socktype
        protocol = c_next.ai_protocol
        canonname = library.str_c2py(c_next.ai_canonname) if c_next.ai_canonname else None
        address = unpack_sockaddr(c_next.ai_addr) if c_next.ai_addr else None
        items.append(AddrInfo(family, socktype, protocol, canonname, address))
        c_next = c_next.ai_next

    if c_addrinfo: lib.uv_freeaddrinfo(c_addrinfo)

    return items


def unpack_sockaddr(c_sockaddr):
    if c_sockaddr.sa_family == socket.AF_INET:
        c_sockaddr_in = ffi.cast('struct sockaddr_in*', c_sockaddr)
        c_host = ffi.new('char[16]')

        port = socket.ntohs(c_sockaddr_in.sin_port)
        lib.uv_ip4_name(c_sockaddr_in, c_host, 16)

        return Address4(library.str_c2py(c_host), port)
    elif c_sockaddr.sa_family == socket.AF_INET6:
        c_sockaddr_in6 = ffi.cast('struct sockaddr_in6*', c_sockaddr)
        c_additional = lib.cross_get_ipv6_additional(c_sockaddr_in6)
        c_host = ffi.new('char[40]')

        port = socket.ntohs(c_sockaddr_in6.sin6_port)
        flowinfo = c_additional.flowinfo
        scope_id = c_additional.scope_id
        lib.uv_ip6_name(c_sockaddr_in6, c_host, 40)

        return Address6(library.str_c2py(c_host), port, flowinfo, scope_id)
    warnings.warn('unable to unpack sockaddr - unknown family')
    return None


@ffi.callback('uv_getaddrinfo_cb')
def uv_getaddrinfo_cb(uv_getaddrinfo, status, _):
    addrinfo_request = library.detach(uv_getaddrinfo)
    """ :type: uv.dns.GetAddrInfo """
    if status == error.StatusCodes.SUCCESS:
        addrinfo_request.populate()
    try:
        addrinfo_request.callback(addrinfo_request, error.StatusCodes.get(status),
                                  addrinfo_request.addrinfo)
    except:
        addrinfo_request.loop.handle_exception()
    addrinfo_request.destroy()


@request.RequestType.GETADDRINFO
class GetAddrInfo(request.Request):
    __slots__ = ['uv_getaddrinfo', 'c_hints', 'callback', 'host',
                 'port', 'hints', 'flags', 'addrinfo']

    def __init__(self, host, port, family=0, socktype=0, protocol=0,
                 flags=0, callback=None, loop=None):
        self.uv_getaddrinfo = ffi.new('uv_getaddrinfo_t*')
        super(GetAddrInfo, self).__init__(self.uv_getaddrinfo, loop)
        self.c_hints = ffi.new('struct addrinfo*')
        self.c_hints = ffi.new('struct addrinfo*')
        self.c_hints.ai_family = family
        self.c_hints.ai_socktype = socktype
        self.c_hints.ai_protocol = protocol
        self.c_hints.ai_flags = flags

        self.callback = callback or common.dummy_callback
        self.host = host
        self.port = port
        self.hints = AddrInfo(family, socktype, protocol, None, None)
        self.flags = flags
        self.addrinfo = []

        uv_callback = ffi.NULL if callback is None else uv_getaddrinfo_cb
        code = lib.uv_getaddrinfo(self.loop.uv_loop, self.uv_getaddrinfo, uv_callback,
                                  host.encode(), str(port).encode(), self.c_hints)

        if code < 0: raise error.UVError(code)
        if callback is None: self.populate()

    def populate(self):
        if self.uv_getaddrinfo.addrinfo:
            self.addrinfo = unpack_addrinfo(self.uv_getaddrinfo.addrinfo)
            self.uv_getaddrinfo.addrinfo = ffi.NULL
        self.destroy()


def getaddrinfo(host, port, family=0, socktype=0, protocol=0,
                flags=0, callback=None, loop=None):
    addrinfo_request = GetAddrInfo(host, port, family, socktype, protocol, flags,
                                   callback, loop)
    return addrinfo_request.addrinfo if callback is None else addrinfo_request


@ffi.callback('uv_getnameinfo_cb')
def uv_getnameinfo_cb(uv_getnameinfo, status, c_hostname, c_service):
    nameinfo_request = library.detach(uv_getnameinfo)
    """ :type: uv.dns.GetNameInfo """
    try:
        nameinfo_request.callback(nameinfo_request, status, library.str_c2py(c_hostname),
                                  library.str_c2py(c_service))
    except:
        nameinfo_request.loop.handle_exception()
    nameinfo_request.destroy()


@request.RequestType.GETNAMEINFO
class GetNameInfo(request.Request):
    __slots__ = ['uv_getnameinfo', 'c_sockaddr', 'callback', 'ip', 'port', 'flags']

    def __init__(self, ip, port, flags=0, callback=None, loop=None):
        self.uv_getnameinfo = ffi.new('uv_getnameinfo_t*')
        super(GetNameInfo, self).__init__(self.uv_getnameinfo, loop)
        self.c_sockaddr = c_create_sockaddr(ip, port)

        self.callback = callback
        self.ip = ip
        self.port = port
        self.flags = flags

        uv_callback = ffi.NULL if callback is None else uv_getnameinfo_cb
        code = lib.uv_getnameinfo(self.loop.uv_loop, self.uv_getnameinfo, uv_callback,
                                  self.c_sockaddr, flags)

        if code < 0: raise error.UVError(code)

    @property
    def host(self):
        return ffi.string(self.uv_getnameinfo.host).decode()

    @property
    def service(self):
        return ffi.string(self.uv_getnameinfo.service).decode()


def getnameinfo(ip, port, flags=0, callback=None, loop=None):
    nameinfo_request = GetNameInfo(ip, port, flags, callback, loop)
    return (NameInfo(nameinfo_request.host, nameinfo_request.service)
            if callback is None else request)


def c_create_sockaddr(ip, port, flowinfo=0, scope_id=0):
    c_sockaddr = ffi.new('struct sockaddr_storage*')
    c_ip = ip.encode()
    code = lib.uv_ip4_addr(c_ip, port, ffi.cast('struct sockaddr_in*', c_sockaddr))
    if not code: return c_sockaddr
    c_sockaddr_in6 = ffi.cast('struct sockaddr_in6*', c_sockaddr)
    code = lib.uv_ip6_addr(c_ip, port, c_sockaddr_in6)
    if code < 0: raise error.UVError(code)
    lib.cross_set_ipv6_additional(c_sockaddr_in6, flowinfo, scope_id)
    return c_sockaddr
