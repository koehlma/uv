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
import warnings

from collections import namedtuple

from .library import ffi, lib, detach, str_c2py, dummy_callback

from .error import UVError, get_status_code
from .loop import Loop
from .request import RequestType, Request

__all__ = ['AddrInfo', 'NameInfo', 'Address4', 'Address6', 'GetAddrInfo',
           'getaddrinfo', 'GetNameInfo', 'getnameinfo']

AddrInfo = namedtuple('AddrInfo', ['family', 'type', 'protocol', 'canonname', 'address'])
NameInfo = namedtuple('NameInfo', ['host', 'service'])

Address4 = namedtuple('Address4', ['host', 'port'])
Address6 = namedtuple('Address6', ['host', 'port', 'flowinfo', 'scope_id'])


def unpack_addrinfo(c_addrinfo) -> list:
    items, c_next = [], c_addrinfo

    while c_next:
        family = c_next.ai_family
        socktype = c_next.ai_socktype
        protocol = c_next.ai_protocol
        canonname = str_c2py(c_next.ai_canonname) if c_next.ai_canonname else None
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

        return Address4(str_c2py(c_host), port)
    elif c_sockaddr.sa_family == socket.AF_INET6:
        c_sockaddr_in6 = ffi.cast('struct sockaddr_in6*', c_sockaddr)
        c_additional = lib.cross_get_ipv6_additional(c_sockaddr_in6)
        c_host = ffi.new('char[40]')

        port = socket.ntohs(c_sockaddr_in6.sin6_port)
        flowinfo = c_additional.flowinfo
        scope_id = c_additional.scope_id
        lib.uv_ip6_name(c_sockaddr_in6, c_host, 40)

        return Address6(str_c2py(c_host), port, flowinfo, scope_id)
    warnings.warn('unable to unpack sockaddr - unknown family')
    return None


@ffi.callback('uv_getaddrinfo_cb')
def uv_getaddrinfo_cb(uv_getaddrinfo, status, _):
    request = detach(uv_getaddrinfo)
    request.finish()
    if status == 0: request.populate()
    with request.loop.callback_context:
        request.callback(request, get_status_code(status), request.addrinfo)


@RequestType.GETADDRINFO
class GetAddrInfo(Request):
    __slots__ = ['uv_getaddrinfo', 'c_hints', 'callback', 'host',
                 'port', 'hints', 'flags', 'addrinfo']

    def __init__(self, host: str, port: int, family: int=0, socktype: int=0,
                 protocol: int=0, flags: int=0, callback: callable=None, loop: Loop=None):
        self.uv_getaddrinfo = ffi.new('uv_getaddrinfo_t*')
        super().__init__(self.uv_getaddrinfo, loop)
        self.c_hints = ffi.new('struct addrinfo*')
        self.c_hints = ffi.new('struct addrinfo*')
        self.c_hints.ai_family = family
        self.c_hints.ai_socktype = socktype
        self.c_hints.ai_protocol = protocol
        self.c_hints.ai_flags = flags

        self.callback = callback or dummy_callback
        self.host = host
        self.port = port
        self.hints = AddrInfo(family, socktype, protocol, None, None)
        self.flags = flags
        self.addrinfo = []

        uv_callback = ffi.NULL if callback is None else uv_getaddrinfo_cb
        code = lib.uv_getaddrinfo(self.loop.uv_loop, self.uv_getaddrinfo, uv_callback,
                                  host.encode(), str(port).encode(), self.c_hints)

        if code < 0: raise UVError(code)
        if callback is None: self.populate()

    def populate(self):
        if self.uv_getaddrinfo.addrinfo:
            self.addrinfo = unpack_addrinfo(self.uv_getaddrinfo.addrinfo)
            self.uv_getaddrinfo.addrinfo = ffi.NULL
        self.finish()


def getaddrinfo(host: str, port: int, family: int=0, socktype: int=0, protocol: int=0,
                flags: int=0, callback: callable=None, loop: Loop=None):
    request = GetAddrInfo(host, port, family, socktype, protocol, flags, callback, loop)
    return request.addrinfo if callback is None else request


@ffi.callback('uv_getnameinfo_cb')
def uv_getnameinfo_cb(uv_getnameinfo, status, c_hostname, c_service):
    request = detach(uv_getnameinfo)
    request.finish()
    with request.loop.callback_context:
        request.callback(request, status, str_c2py(c_hostname), str_c2py(c_service))


@RequestType.GETNAMEINFO
class GetNameInfo(Request):
    __slots__ = ['uv_getnameinfo', 'c_sockaddr', 'callback', 'ip', 'port', 'flags']

    def __init__(self, ip: str, port: int, flags: int=0, callback: callable=None,
                 loop: Loop=None):
        self.uv_getnameinfo = ffi.new('uv_getnameinfo_t*')
        super().__init__(self.uv_getnameinfo, loop)
        self.c_sockaddr = c_create_sockaddr(ip, port)

        self.callback = callback
        self.ip = ip
        self.port = port
        self.flags = flags

        uv_callback = ffi.NULL if callback is None else uv_getnameinfo_cb
        code = lib.uv_getnameinfo(self.loop.uv_loop, self.uv_getnameinfo, uv_callback,
                                  self.c_sockaddr, flags)

        if code < 0: raise UVError(code)

    @property
    def host(self):
        return ffi.string(self.uv_getnameinfo.host).decode()

    @property
    def service(self):
        return ffi.string(self.uv_getnameinfo.service).decode()


def getnameinfo(ip: str, port: int, flags: int=0, callback: callable=None,
                loop: Loop=None):
    request = GetNameInfo(ip, port, flags, callback, loop)
    return NameInfo(request.host, request.service) if callback is None else request


def c_create_sockaddr(ip: str, port: int, flowinfo: int=0, scope_id: int=0):
    c_sockaddr = ffi.new('struct sockaddr *')
    c_ip = ip.encode()
    code = lib.uv_ip4_addr(c_ip, port, ffi.cast('struct sockaddr_in*', c_sockaddr))
    if not code: return c_sockaddr
    c_sockaddr_in6 = ffi.cast('struct sockaddr_in6*', c_sockaddr)
    code = lib.uv_ip6_addr(c_ip, port, c_sockaddr_in6)
    if code < 0: raise UVError(code)
    lib.cross_set_ipv6_additional(c_sockaddr_in6, flowinfo, scope_id)
    return c_sockaddr
