# -*- coding: utf-8 -*-

# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
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

from __future__ import print_function, unicode_literals, division, absolute_import

from .library import ffi, lib

from .common import Enumeration

__all__ = ['StatusCode', 'UVError', 'HandleClosedError']


class StatusCode(Enumeration):
    """
    Status code enumeration. Codes (other than SUCCESS) are varying across platforms.
    """

    SUCCESS = 0
    """
    success
    """

    E2BIG = lib.UV_E2BIG
    """
    argument list too long
    """
    EACCES = lib.UV_EACCES
    """
    permission denied
    """
    EADDRINUSE = lib.UV_EADDRINUSE
    """
    address already in use
    """
    EADDRNOTAVAIL = lib.UV_EADDRNOTAVAIL
    """
    address not available
    """
    EAFNOSUPPORT = lib.UV_EAFNOSUPPORT
    """
    address family not supported
    """
    EAGAIN = lib.UV_EAGAIN
    """
    resource temporarily unavailable
    """
    EAI_ADDRFAMILY = lib.UV_EAI_ADDRFAMILY
    """
    address family not supported
    """
    EAI_AGAIN = lib.UV_EAI_AGAIN
    """
    temporary failure
    """
    EAI_BADFLAGS = lib.UV_EAI_BADFLAGS
    """
    bad ai_flags value
    """
    EAI_BADHINTS = lib.UV_EAI_BADHINTS
    """
    invalid value for hints
    """
    EAI_CANCELED = lib.UV_EAI_CANCELED
    """
    request canceled
    """
    EAI_FAIL = lib.UV_EAI_FAIL
    """
    permanent failure
    """
    EAI_FAMILY = lib.UV_EAI_FAMILY
    """
    ai_family not supported
    """
    EAI_MEMORY = lib.UV_EAI_MEMORY
    """
    out of memory
    """
    EAI_NODATA = lib.UV_EAI_NODATA
    """
    no address
    """
    EAI_NONAME = lib.UV_EAI_NONAME
    """
    unknown node or service
    """
    EAI_OVERFLOW = lib.UV_EAI_OVERFLOW
    """
    argument buffer overflow
    """
    EAI_PROTOCOL = lib.UV_EAI_PROTOCOL
    """
    resolved protocol is unknown
    """
    EAI_SERVICE = lib.UV_EAI_SERVICE
    """
    service not available for socket type
    """
    EAI_SOCKTYPE = lib.UV_EAI_SOCKTYPE
    """
    socket type not supported
    """
    EALREADY = lib.UV_EALREADY
    """
    connection already in progress
    """
    EBADF = lib.UV_EBADF
    """
    bad file descriptor
    """
    EBUSY = lib.UV_EBUSY
    """
    resource busy or locked
    """
    ECANCELED = lib.UV_ECANCELED
    """
    operation canceled
    """
    ECHARSET = lib.UV_ECHARSET
    """
    invalid Unicode character
    """
    ECONNABORTED = lib.UV_ECONNABORTED
    """
    software caused connection abort
    """
    ECONNREFUSED = lib.UV_ECONNREFUSED
    """
    connection refused
    """
    ECONNRESET = lib.UV_ECONNRESET
    """
    connection reset by peer
    """
    EDESTADDRREQ = lib.UV_EDESTADDRREQ
    """
    destination address required
    """
    EEXIST = lib.UV_EEXIST
    """
    file already exists
    """
    EFAULT = lib.UV_EFAULT
    """
    bad address in system call argument
    """
    EFBIG = lib.UV_EFBIG
    """
    file too large
    """
    EHOSTUNREACH = lib.UV_EHOSTUNREACH
    """
    host is unreachable
    """
    EINTR = lib.UV_EINTR
    """
    interrupted system call
    """
    EINVAL = lib.UV_EINVAL
    """
    invalid argument
    """
    EIO = lib.UV_EIO
    """
    io error
    """
    EISCONN = lib.UV_EISCONN
    """
    socket is already connected
    """
    EISDIR = lib.UV_EISDIR
    """
    illegal operation on a directory
    """
    ELOOP = lib.UV_ELOOP
    """
    too many symbolic links encountered
    """
    EMFILE = lib.UV_EMFILE
    """
    too many open files
    """
    EMSGSIZE = lib.UV_EMSGSIZE
    """
    message too long
    """
    ENAMETOOLONG = lib.UV_ENAMETOOLONG
    """
    name too long
    """
    ENETDOWN = lib.UV_ENETDOWN
    """
    network is down
    """
    ENETUNREACH = lib.UV_ENETUNREACH
    """
    network is unreachable
    """
    ENFILE = lib.UV_ENFILE
    """
    file table overflow
    """
    ENOBUFS = lib.UV_ENOBUFS
    """
    no buffer space available
    """
    ENODEV = lib.UV_ENODEV
    """
    no such device
    """
    ENOENT = lib.UV_ENOENT
    """
    no such file or directory
    """
    ENOMEM = lib.UV_ENOMEM
    """
    not enough memory
    """
    ENONET = lib.UV_ENONET
    """
    machine is not on the network
    """
    ENOPROTOOPT = lib.UV_ENOPROTOOPT
    """
    protocol not available
    """
    ENOSPC = lib.UV_ENOSPC
    """
    no space left on device
    """
    ENOSYS = lib.UV_ENOSYS
    """
    function not implemented
    """
    ENOTCONN = lib.UV_ENOTCONN
    """
    socket is not connected
    """
    ENOTDIR = lib.UV_ENOTDIR
    """
    not a directory
    """
    ENOTEMPTY = lib.UV_ENOTEMPTY
    """
    directory not empty
    """
    ENOTSOCK = lib.UV_ENOTSOCK
    """
    socket operation on non-socket
    """
    ENOTSUP = lib.UV_ENOTSUP
    """
    operation not supported on socket
    """
    EPERM = lib.UV_EPERM
    """
    operation not permitted
    """
    EPIPE = lib.UV_EPIPE
    """
    broken pipe
    """
    EPROTO = lib.UV_EPROTO
    """
    protocol error
    """
    EPROTONOSUPPORT = lib.UV_EPROTONOSUPPORT
    """
    protocol not supported
    """
    EPROTOTYPE = lib.UV_EPROTOTYPE
    """
    protocol wrong type for socket
    """
    ERANGE = lib.UV_ERANGE
    """
    result too large
    """
    EROFS = lib.UV_EROFS
    """
    read-only file system
    """
    ESHUTDOWN = lib.UV_ESHUTDOWN
    """
    cannot send after transport endpoint shutdown
    """
    ESPIPE = lib.UV_ESPIPE
    """
    invalid seek
    """
    ESRCH = lib.UV_ESRCH
    """
    no such process
    """
    ETIMEDOUT = lib.UV_ETIMEDOUT
    """
    connection timed out
    """
    ETXTBSY = lib.UV_ETXTBSY
    """
    text file is busy
    """
    EXDEV = lib.UV_EXDEV
    """
    cross-device link not permitted
    """
    UNKNOWN = lib.UV_UNKNOWN
    """
    unknown error
    """
    EOF = lib.UV_EOF
    """
    end of file
    """
    ENXIO = lib.UV_ENXIO
    """
    no such device or address
    """
    EMLINK = lib.UV_EMLINK
    """
    too many links
    """
    EHOSTDOWN = lib.UV_EHOSTDOWN
    """
    host is down
    """


def get_status_code(code):
    if not code: return StatusCode.SUCCESS
    try: return StatusCode(code)
    except ValueError: return code


class UVError(OSError):
    def __init__(self, code, message=None):
        try:
            self.code = StatusCode(code)
            self.name = ffi.string(lib.uv_err_name(code)).decode()
            message = message or ffi.string(lib.uv_strerror(code)).decode()
        except ValueError:
            self.code = code
            self.name = 'UNKNOWN'
            message = 'some unknown error occoured'
        super(UVError, self).__init__(code, '[%s] %s' % (self.name, message))


class ClosedError(UVError):
    def __init__(self):
        message = 'invalid operation on closed structure'
        super(ClosedError, self).__init__(StatusCode.EINVAL, message)


class HandleClosedError(ClosedError): pass


class LoopClosedError(ClosedError): pass
