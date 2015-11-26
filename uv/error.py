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

from .library import ffi, lib

__all__ = ['StatusCode', 'UVError']


class StatusCode(enum.IntEnum):
    SUCCESS = 0

    E2BIG = lib.UV_E2BIG
    EACCES = lib.UV_EACCES
    EADDRINUSE = lib.UV_EADDRINUSE
    EADDRNOTAVAIL = lib.UV_EADDRNOTAVAIL
    EAFNOSUPPORT = lib.UV_EAFNOSUPPORT
    EAGAIN = lib.UV_EAGAIN
    EAI_ADDRFAMILY = lib.UV_EAI_ADDRFAMILY
    EAI_AGAIN = lib.UV_EAI_AGAIN
    EAI_BADFLAGS = lib.UV_EAI_BADFLAGS
    EAI_BADHINTS = lib.UV_EAI_BADHINTS
    EAI_CANCELED = lib.UV_EAI_CANCELED
    EAI_FAIL = lib.UV_EAI_FAIL
    EAI_FAMILY = lib.UV_EAI_FAMILY
    EAI_MEMORY = lib.UV_EAI_MEMORY
    EAI_NODATA = lib.UV_EAI_NODATA
    EAI_NONAME = lib.UV_EAI_NONAME
    EAI_OVERFLOW = lib.UV_EAI_OVERFLOW
    EAI_PROTOCOL = lib.UV_EAI_PROTOCOL
    EAI_SERVICE = lib.UV_EAI_SERVICE
    EAI_SOCKTYPE = lib.UV_EAI_SOCKTYPE
    EALREADY = lib.UV_EALREADY
    EBADF = lib.UV_EBADF
    EBUSY = lib.UV_EBUSY
    ECANCELED = lib.UV_ECANCELED
    ECHARSET = lib.UV_ECHARSET
    ECONNABORTED = lib.UV_ECONNABORTED
    ECONNREFUSED = lib.UV_ECONNREFUSED
    ECONNRESET = lib.UV_ECONNRESET
    EDESTADDRREQ = lib.UV_EDESTADDRREQ
    EEXIST = lib.UV_EEXIST
    EFAULT = lib.UV_EFAULT
    EFBIG = lib.UV_EFBIG
    EHOSTUNREACH = lib.UV_EHOSTUNREACH
    EINTR = lib.UV_EINTR
    EINVAL = lib.UV_EINVAL
    EIO = lib.UV_EIO
    EISCONN = lib.UV_EISCONN
    EISDIR = lib.UV_EISDIR
    ELOOP = lib.UV_ELOOP
    EMFILE = lib.UV_EMFILE
    EMSGSIZE = lib.UV_EMSGSIZE
    ENAMETOOLONG = lib.UV_ENAMETOOLONG
    ENETDOWN = lib.UV_ENETDOWN
    ENETUNREACH = lib.UV_ENETUNREACH
    ENFILE = lib.UV_ENFILE
    ENOBUFS = lib.UV_ENOBUFS
    ENODEV = lib.UV_ENODEV
    ENOENT = lib.UV_ENOENT
    ENOMEM = lib.UV_ENOMEM
    ENONET = lib.UV_ENONET
    ENOPROTOOPT = lib.UV_ENOPROTOOPT
    ENOSPC = lib.UV_ENOSPC
    ENOSYS = lib.UV_ENOSYS
    ENOTCONN = lib.UV_ENOTCONN
    ENOTDIR = lib.UV_ENOTDIR
    ENOTEMPTY = lib.UV_ENOTEMPTY
    ENOTSOCK = lib.UV_ENOTSOCK
    ENOTSUP = lib.UV_ENOTSUP
    EPERM = lib.UV_EPERM
    EPIPE = lib.UV_EPIPE
    EPROTO = lib.UV_EPROTO
    EPROTONOSUPPORT = lib.UV_EPROTONOSUPPORT
    EPROTOTYPE = lib.UV_EPROTOTYPE
    ERANGE = lib.UV_ERANGE
    EROFS = lib.UV_EROFS
    ESHUTDOWN = lib.UV_ESHUTDOWN
    ESPIPE = lib.UV_ESPIPE
    ESRCH = lib.UV_ESRCH
    ETIMEDOUT = lib.UV_ETIMEDOUT
    ETXTBSY = lib.UV_ETXTBSY
    EXDEV = lib.UV_EXDEV
    UNKNOWN = lib.UV_UNKNOWN
    EOF = lib.UV_EOF
    ENXIO = lib.UV_ENXIO
    EMLINK = lib.UV_EMLINK
    EHOSTDOWN = lib.UV_EHOSTDOWN


def get_status_code(code: int):
    if not code: return StatusCode.SUCCESS
    try: return StatusCode(code)
    except ValueError: return code


class UVError(OSError):
    def __init__(self, code: int):
        try:
            self.code = StatusCode(code)
            self.name = ffi.string(lib.uv_err_name(code)).decode()
            message = ffi.string(lib.uv_strerror(code)).decode()
        except ValueError:
            self.code = code
            self.name = 'UNKNOWN'
            message = 'some unknown error occoured'
        super().__init__(code, '[%s] %s' % (self.name, message))
