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

from __future__ import print_function, unicode_literals, division, absolute_import

import errno
import io
import socket

from . import common
from .library import ffi, lib


class StatusCodes(common.Enumeration):
    """
    Status codes enumeration. Status codes are instances of this class
    and — beside SUCCESS — vary across platforms. Status codes other
    than SUCCESS are linked with a corresponding exception.
    """

    SUCCESS = 0
    """
    Success — no error occoured.

    :type: uv.StatusCodes
    """

    E2BIG = lib.UV_E2BIG
    """
    Argument list too long.

    :type: uv.StatusCodes
    """

    EACCES = lib.UV_EACCES
    """
    Permission denied.

    :type: uv.StatusCodes
    """

    EADDRINUSE = lib.UV_EADDRINUSE
    """
    Address already in use.

    :type: uv.StatusCodes
    """

    EADDRNOTAVAIL = lib.UV_EADDRNOTAVAIL
    """
    Address not available.

    :type: uv.StatusCodes
    """

    EAFNOSUPPORT = lib.UV_EAFNOSUPPORT
    """
    Address family not supported.

    :type: uv.StatusCodes
    """

    EAGAIN = lib.UV_EAGAIN
    """
    Resource temporarily unavailable.

    :type: uv.StatusCodes
    """

    EAI_ADDRFAMILY = lib.UV_EAI_ADDRFAMILY
    """
    Address family not supported.

    :type: uv.StatusCodes
    """

    EAI_AGAIN = lib.UV_EAI_AGAIN
    """
    Temporary failure.

    :type: uv.StatusCodes
    """

    EAI_BADFLAGS = lib.UV_EAI_BADFLAGS
    """
    Bad address flags value.

    :type: uv.StatusCodes
    """

    EAI_BADHINTS = lib.UV_EAI_BADHINTS
    """
    Invalid value for hints.

    :type: uv.StatusCodes
    """

    EAI_CANCELED = lib.UV_EAI_CANCELED
    """
    Request canceled.

    :type: uv.StatusCodes
    """

    EAI_FAIL = lib.UV_EAI_FAIL
    """
    Permanent failure.

    :type: uv.StatusCodes
    """

    EAI_FAMILY = lib.UV_EAI_FAMILY
    """
    Address family not supported.

    :type: uv.StatusCodes
    """

    EAI_MEMORY = lib.UV_EAI_MEMORY
    """
    Out of memory.

    :type: uv.StatusCodes
    """

    EAI_NODATA = lib.UV_EAI_NODATA
    """
    No address.

    :type: uv.StatusCodes
    """

    EAI_NONAME = lib.UV_EAI_NONAME
    """
    Unknown node or service.

    :type: uv.StatusCodes
    """

    EAI_OVERFLOW = lib.UV_EAI_OVERFLOW
    """
    Argument buffer overflow.

    :type: uv.StatusCodes
    """

    EAI_PROTOCOL = lib.UV_EAI_PROTOCOL
    """
    Resolved protocol is unknown.

    :type: uv.StatusCodes
    """

    EAI_SERVICE = lib.UV_EAI_SERVICE
    """
    Service not available for socket type.

    :type: uv.StatusCodes
    """

    EAI_SOCKTYPE = lib.UV_EAI_SOCKTYPE
    """
    Socket type not supported.

    :type: uv.StatusCodes
    """

    EALREADY = lib.UV_EALREADY
    """
    Connection already in progress.

    :type: uv.StatusCodes
    """

    EBADF = lib.UV_EBADF
    """
    Bad file descriptor.

    :type: uv.StatusCodes
    """

    EBUSY = lib.UV_EBUSY
    """
    Resource busy or locked.

    :type: uv.StatusCodes
    """

    ECANCELED = lib.UV_ECANCELED
    """
    Operation canceled.

    :type: uv.StatusCodes
    """

    ECHARSET = lib.UV_ECHARSET
    """
    Invalid Unicode character.

    :type: uv.StatusCodes
    """

    ECONNABORTED = lib.UV_ECONNABORTED
    """
    Software caused connection abort.

    :type: uv.StatusCodes
    """

    ECONNREFUSED = lib.UV_ECONNREFUSED
    """
    Connection refused.

    :type: uv.StatusCodes
    """

    ECONNRESET = lib.UV_ECONNRESET
    """
    Connection reset by peer.

    :type: uv.StatusCodes
    """

    EDESTADDRREQ = lib.UV_EDESTADDRREQ
    """
    Destination address required.

    :type: uv.StatusCodes
    """

    EEXIST = lib.UV_EEXIST
    """
    File already exists.

    :type: uv.StatusCodes
    """

    EFAULT = lib.UV_EFAULT
    """
    Bad address in system call argument.

    :type: uv.StatusCodes
    """

    EFBIG = lib.UV_EFBIG
    """
    File too large.

    :type: uv.StatusCodes
    """

    EHOSTUNREACH = lib.UV_EHOSTUNREACH
    """
    Host is unreachable.

    :type: uv.StatusCodes
    """

    EINTR = lib.UV_EINTR
    """
    Interrupted system call.

    :type: uv.StatusCodes
    """

    EINVAL = lib.UV_EINVAL
    """
    Invalid argument.

    :type: uv.StatusCodes
    """

    EIO = lib.UV_EIO
    """
    IO error.

    :type: uv.StatusCodes
    """

    EISCONN = lib.UV_EISCONN
    """
    Socket is already connected.

    :type: uv.StatusCodes
    """

    EISDIR = lib.UV_EISDIR
    """
    Illegal operation on a directory.

    :type: uv.StatusCodes
    """

    ELOOP = lib.UV_ELOOP
    """
    Too many symbolic links encountered.

    :type: uv.StatusCodes
    """

    EMFILE = lib.UV_EMFILE
    """
    Too many open files.

    :type: uv.StatusCodes
    """

    EMSGSIZE = lib.UV_EMSGSIZE
    """
    Message too long.

    :type: uv.StatusCodes
    """

    ENAMETOOLONG = lib.UV_ENAMETOOLONG
    """
    Name too long.

    :type: uv.StatusCodes
    """

    ENETDOWN = lib.UV_ENETDOWN
    """
    Network is down.

    :type: uv.StatusCodes
    """

    ENETUNREACH = lib.UV_ENETUNREACH
    """
    Network is unreachable.

    :type: uv.StatusCodes
    """

    ENFILE = lib.UV_ENFILE
    """
    File table overflow.

    :type: uv.StatusCodes
    """

    ENOBUFS = lib.UV_ENOBUFS
    """
    No buffer space available.

    :type: uv.StatusCodes
    """

    ENODEV = lib.UV_ENODEV
    """
    No such device.

    :type: uv.StatusCodes
    """

    ENOENT = lib.UV_ENOENT
    """
    No such file or directory.

    :type: uv.StatusCodes
    """

    ENOMEM = lib.UV_ENOMEM
    """
    Not enough memory.

    :type: uv.StatusCodes
    """

    ENONET = lib.UV_ENONET
    """
    Machine is not on the network.

    :type: uv.StatusCodes
    """

    ENOPROTOOPT = lib.UV_ENOPROTOOPT
    """
    Protocol not available.

    :type: uv.StatusCodes
    """

    ENOSPC = lib.UV_ENOSPC
    """
    No space left on device.

    :type: uv.StatusCodes
    """

    ENOSYS = lib.UV_ENOSYS
    """
    Function not implemented.

    :type: uv.StatusCodes
    """

    ENOTCONN = lib.UV_ENOTCONN
    """
    Socket is not connected.

    :type: uv.StatusCodes
    """

    ENOTDIR = lib.UV_ENOTDIR
    """
    Not a directory.

    :type: uv.StatusCodes
    """

    ENOTEMPTY = lib.UV_ENOTEMPTY
    """
    Directory not empty.

    :type: uv.StatusCodes
    """

    ENOTSOCK = lib.UV_ENOTSOCK
    """
    Socket operation on non-socket.

    :type: uv.StatusCodes
    """

    ENOTSUP = lib.UV_ENOTSUP
    """
    Operation not supported on socket.

    :type: uv.StatusCodes
    """

    EPERM = lib.UV_EPERM
    """
    Operation not permitted.

    :type: uv.StatusCodes
    """

    EPIPE = lib.UV_EPIPE
    """
    Broken pipe.

    :type: uv.StatusCodes
    """

    EPROTO = lib.UV_EPROTO
    """
    Protocol error.

    :type: uv.StatusCodes
    """

    EPROTONOSUPPORT = lib.UV_EPROTONOSUPPORT
    """
    Protocol not supported.

    :type: uv.StatusCodes
    """

    EPROTOTYPE = lib.UV_EPROTOTYPE
    """
    Protocol wrong type for socket.

    :type: uv.StatusCodes
    """

    ERANGE = lib.UV_ERANGE
    """
    Result too large.

    :type: uv.StatusCodes
    """

    EROFS = lib.UV_EROFS
    """
    Read-only file system.

    :type: uv.StatusCodes
    """

    ESHUTDOWN = lib.UV_ESHUTDOWN
    """
    Cannot send after transport endpoint shutdown.

    :type: uv.StatusCodes
    """

    ESPIPE = lib.UV_ESPIPE
    """
    Invalid seek.

    :type: uv.StatusCodes
    """

    ESRCH = lib.UV_ESRCH
    """
    No such process.

    :type: uv.StatusCodes
    """

    ETIMEDOUT = lib.UV_ETIMEDOUT
    """
    Connection timed out.

    :type: uv.StatusCodes
    """

    ETXTBSY = lib.UV_ETXTBSY
    """
    Text file is busy.

    :type: uv.StatusCodes
    """

    EXDEV = lib.UV_EXDEV
    """
    Cross-device link not permitted.

    :type: uv.StatusCodes
    """

    UNKNOWN = lib.UV_UNKNOWN
    """
    Unknown error.

    :type: uv.StatusCodes
    """

    EOF = lib.UV_EOF
    """
    End of file.

    :type: uv.StatusCodes
    """

    ENXIO = lib.UV_ENXIO
    """
    No such device or address.

    :type: uv.StatusCodes
    """
    EMLINK = lib.UV_EMLINK
    """
    Too many links.

    :type: uv.StatusCodes
    """

    EHOSTDOWN = lib.UV_EHOSTDOWN
    """
    Host is down.

    :type: uv.StatusCodes
    """

    def __call__(self, exception):
        assert self._exception is UVError
        self._exception = exception
        self._exception.code = self
        return self._exception

    @property
    def exception(self):
        """
        Corresponding exception (subclass of :class:`uv.error.UVError`).

        :readonly:
            True
        :rtype:
            Subclass[uv.error.UVError]
        """
        return self._exception

    @property
    def message(self):
        """
        Human readable error message.

        :readonly:
            True
        :rtype:
            unicode
        """
        return ffi.string(lib.uv_strerror(self)).decode()

    @classmethod
    def get(cls, code):
        """
        Look up the given status code und return the corresponding
        instance of :class:`uv.StatusCodes` or the original integer
        if there is no such status code.

        :param code:
            potential status code

        :type code:
            uv.StatusCodes | int | None

        :return:
            status code instance or original status code integer
        :rtype:
            uv.StatusCodes | int
        """
        if not code:
            # for performance
            return StatusCodes.SUCCESS
        try:
            return StatusCodes(code)
        except ValueError:
            return code

    @classmethod
    def from_error_number(cls, error_number):
        if not error_number:
            return StatusCodes.SUCCESS
        return getattr(cls, errno.errorcode[error_number], cls.UNKNOWN)


class UVError(OSError):
    """ Base class of all uv-related exceptions. """

    code = None

    def __new__(cls, code=None, message=''):
        if cls is UVError:
            try:
                # replace generic uv error with a specialized one if possible
                code = StatusCodes(code)
                if code.exception is not UVError:
                    return code.exception(code, message or code.message)
            except ValueError:
                pass
        return super(UVError, cls).__new__(cls, code, message)
    
    def __init__(self, code=None, message=''):
        """
        :param code:
            Error-Code
        :param message:
            Error-Message

        :type code:
            uv.StatusCodes | int | None
        :type message:
            unicode
        """
        try:
            code = StatusCodes(code or self.code)
            name = code.name
            message = message or code.message
        except ValueError:
            code = code
            name = 'UNKNOWN'
            message = message or 'some unknown error occoured'
        self.code = code
        """
        Error-Code

        :readonly:
            True
        :type:
            uv.StatusCodes | int | None
        """
        self.name = name
        """
        Error-Name

        :readonly:
            True
        :type:
            unicode
        """
        self.message = message
        """
        Error-Message

        :readonly:
            True
        :type:
            unicode
        """
        super(UVError, self).__init__(self.code, '[%s] %s' % (self.name, self.message))


def _get_builtin(name, default=None):
    return getattr(common.builtins, name, default)


class _DummyClass(object):
    pass


# support for PEP 3151 exception hierarchy
_ConnectionError = _get_builtin('ConnectionError', common.builtins.IOError)
_BrokenPipeError = _get_builtin('BrokenPipeError', common.builtins.IOError)
_ConnectionAbortedError = _get_builtin('ConnectionAbortedError', socket.error)
_ConnectionRefusedError = _get_builtin('ConnectionRefusedError', socket.error)
_ConnectionResetError = _get_builtin('ConnectionResetError', socket.error)
_FileExistsError = _get_builtin('FileExistsError', common.builtins.IOError)
_FileNotFoundError = _get_builtin('FileNotFoundError', common.builtins.IOError)
_InterruptedError = _get_builtin('InterruptedError', _DummyClass)
_IsADirectoryError = _get_builtin('IsADirectoryError', common.builtins.IOError)
_NotADirectoryError = _get_builtin('NotADirectoryError', common.builtins.IOError)
_PermissionError = _get_builtin('PermissionError', common.builtins.IOError)
_ProcessLookupError = _get_builtin('ProcessLookupError', _DummyClass)
_TimeoutError = _get_builtin('TimeoutError', socket.timeout)

# assign default exception
StatusCodes._exception = UVError


@StatusCodes.EINVAL
@StatusCodes.E2BIG
@StatusCodes.EAI_OVERFLOW
@StatusCodes.EFAULT
class ArgumentError(UVError, ValueError):
    """ Invalid arguments. """


@StatusCodes.EAGAIN
@StatusCodes.EAI_AGAIN
class TemporaryUnavailableError(UVError, io.BlockingIOError):
    """ Resource temporary unavailable. """


@StatusCodes.ECANCELED
@StatusCodes.EAI_CANCELED
class CanceledError(UVError):
    """ Request canceled. """


@StatusCodes.EAI_FAIL
class PermanentError(UVError):
    """ Permanent failure. """


@StatusCodes.EACCES
@StatusCodes.EPERM
@StatusCodes.EROFS
class PermissionError(UVError, _PermissionError):
    """ Permission denied. """


@StatusCodes.EBADF
class BadFileDescriptorError(UVError, common.builtins.IOError):
    """ Bad file descriptor. """


@StatusCodes.EBUSY
@StatusCodes.ETXTBSY
class ResourceBusyError(UVError, common.builtins.IOError):
    """ Resource busy or locked. """


@StatusCodes.ECHARSET
class CharsetError(UVError, UnicodeError):
    """ Invalid unicode character. """


@StatusCodes.EEXIST
class FileExistsError(UVError, _FileExistsError):
    """ File already exists. """


@StatusCodes.EFBIG
class FileTooLargeError(UVError):
    """ File too large. """


@StatusCodes.EINTR
class InterruptedError(UVError, _InterruptedError):
    """ Interrupted system call. """


@StatusCodes.EIO
class IOError(UVError, common.builtins.IOError):
    """ Generic IO related error. """


@StatusCodes.EISCONN
class IsConnectedError(ArgumentError):
    """ Socket is already connected. """


@StatusCodes.EISDIR
class IsADirectoryError(UVError, _IsADirectoryError):
    """ Illegal operation on a directory. """


@StatusCodes.ENOTDIR
class NotADirectoryError(UVError, _NotADirectoryError):
    """ Not a directory. """


@StatusCodes.ENOTEMPTY
class NotEmptyError(UVError):
    """ Directory is not empty. """


@StatusCodes.EMSGSIZE
class MassageTooLongError(UVError):
    """ Message too long. """


@StatusCodes.ENAMETOOLONG
class NameTooLongError(UVError):
    """ Name too long. """


@StatusCodes.ENOBUFS
class BufferSpaceError(UVError):
    """ No buffer space available. """


@StatusCodes.ENOSPC
class NoSpaceError(UVError):
    """ No space left on the device. """


@StatusCodes.ENOSYS
class NotImplementedError(UVError, common.builtins.NotImplementedError):
    """ Function not implemented. """


@StatusCodes.ENOTCONN
class NotConnectedError(UVError):
    """ Socket is not connected. """


@StatusCodes.EHOSTUNREACH
class HostUnreachableError(UVError):
    """ Host is unreachable. """


@StatusCodes.ERANGE
class ResultTooLargeError(UVError):
    """ Result too large. """


@StatusCodes.ESPIPE
class SeekError(UVError):
    """ Invalid seek. """


@StatusCodes.ESRCH
class ProcessLookupError(UVError, _ProcessLookupError):
    """ No such progress. """


@StatusCodes.ETIMEDOUT
class TimeoutError(UVError, _TimeoutError):
    """ Operation timed out. """


@StatusCodes.EXDEV
class CrossDeviceError(UVError):
    """ Cross device link not permitted. """


@StatusCodes.EOF
class EOFError(UVError, common.builtins.EOFError):
    """ End of file error. """


class UnsupportedOperation(UVError):
    """ Base class of all unsupported operation related errors. """


class ClosedStructureError(UnsupportedOperation):
    """ Invalid operation on closed structure. """

    def __init__(self):
        message = 'invalid operation on closed structure'
        super(ClosedStructureError, self).__init__(StatusCodes.EINVAL, message)


class ClosedHandleError(ClosedStructureError):
    """ Invalid operation on closed handle. """


class ClosedLoopError(ClosedStructureError):
    """ Invalid operation on closed loop. """


@StatusCodes.ENOTSOCK
class NotSocketError(UnsupportedOperation):
    """ Socket operation on non-socket. """


@StatusCodes.ENOTSUP
class NotSupportedError(UnsupportedOperation):
    """ Operation not supported on socket. """


@StatusCodes.EPROTO
class ProtocolError(UVError):
    """ Protocol error. """


@StatusCodes.ENOPROTOOPT
class ProtocolNoOptionError(UVError):
    """ Protocol option unavailable. """


@StatusCodes.EPROTONOSUPPORT
class ProtocolNotSupportedError(UVError):
    """ Protocol not supported. """


@StatusCodes.EPROTOTYPE
class ProtocolTypeError(UVError):
    """ Protocol wrong type for socket. """


class AddressError(UVError):
    """ Base class of all address related errors. """


@StatusCodes.EADDRNOTAVAIL
class AddressUnavailableError(AddressError):
    """ Address not available. """


@StatusCodes.EADDRINUSE
class AddressInUseError(AddressUnavailableError):
    """ Address already in use. """


@StatusCodes.EAFNOSUPPORT
@StatusCodes.EAI_ADDRFAMILY
@StatusCodes.EAI_FAMILY
class AddressFamilyError(AddressError, socket.gaierror):
    """ Address family not supported. """


@StatusCodes.EAI_BADFLAGS
class AddressFlagsError(ArgumentError, AddressError, socket.gaierror):
    """ Bad address flags value. """


@StatusCodes.EAI_BADHINTS
class AddressHintsError(ArgumentError, AddressError, socket.gaierror):
    """ Bad address hints value. """


@StatusCodes.EAI_NODATA
class AddressDataError(ArgumentError, AddressError, socket.gaierror):
    """ No address given. """


@StatusCodes.EAI_NONAME
class AddressNameError(AddressError, socket.gaierror):
    """ Unknown node or service. """


@StatusCodes.EAI_PROTOCOL
class AddressProtocolError(AddressError, ProtocolError, socket.gaierror):
    """ Resolved protocol is unknown. """


@StatusCodes.EAI_SERVICE
class AddressServiceError(AddressError, socket.gaierror):
    """ Service not available for socket type. """


@StatusCodes.EAI_SOCKTYPE
class AddressSocketTypeError(AddressError, socket.gaierror):
    """ Socket type not supported. """


@StatusCodes.EDESTADDRREQ
class DestinationAddressError(AddressError):
    """ Destination address required. """


class ConnectionError(UVError):
    """ Base class of all connection related errors. """


@StatusCodes.EPIPE
@StatusCodes.ESHUTDOWN
class BrokenPipeError(ConnectionError, _BrokenPipeError):
    """ Broken pipe. """


@StatusCodes.ECONNABORTED
class ConnectionAbortedError(ConnectionError, _ConnectionAbortedError):
    """ Software caused connection abort. """


@StatusCodes.ECONNREFUSED
class ConnectionRefusedError(ConnectionError, _ConnectionRefusedError):
    """ Connection refused. """


@StatusCodes.ECONNRESET
class ConnectionResetError(ConnectionError, _ConnectionResetError):
    """ Connection reset by peer. """


@StatusCodes.EALREADY
class ConnectionInProgressError(ConnectionError, io.BlockingIOError):
    """ Connection already in progress. """


class NotFoundError(UVError):
    """ Base class of all not found related errors. """


@StatusCodes.ENODEV
@StatusCodes.ENXIO
class DeviceNotFoundError(NotFoundError):
    """ No such device or address. """


@StatusCodes.ENOENT
class FileNotFoundError(NotFoundError, _FileNotFoundError):
    """ No such file or directory. """


class NetworkError(UVError):
    """ Base class of all network related errors. """


@StatusCodes.ENETDOWN
class NetworkDownError(NetworkError):
    """ Network is down. """


@StatusCodes.ENETUNREACH
class NetworkUnreachableError(NetworkError):
    """ Network is unreachable. """


@StatusCodes.ENONET
class NoNetworkError(NetworkError):
    """ Machine is not on the network. """


class SystemFailureError(UVError):
    """ Base class of all system related errors. """


@StatusCodes.ENOMEM
@StatusCodes.EAI_MEMORY
class MemoryError(SystemFailureError, common.builtins.MemoryError):
    """ Not enough memory. """


@StatusCodes.EMLINK
class TooManyLinksError(SystemFailureError):
    """ Too many links encountered. """


@StatusCodes.ELOOP
class TooManySymbolicLinksError(TooManyLinksError):
    """ Too many symbolic links encountered. """


@StatusCodes.EMFILE
class TooManyOpenFilesError(SystemFailureError):
    """ Too many open files. """


@StatusCodes.ENFILE
class FileTableOverflowError(SystemFailureError):
    """ File table overflow. """
