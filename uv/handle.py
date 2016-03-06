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

import warnings

from . import abstract, base, common, error, library
from .library import ffi, lib
from .loop import Loop


class HandleTypes(common.Enumeration):
    """
    Internal handle types enumeration. Handle types are exposed as
    subclasses of :class:`uv.Handle` to user code. This enumeration
    is only for internal purposes.
    """

    UNKNOWN = lib.UV_UNKNOWN_HANDLE
    HANDLE = lib.UV_HANDLE
    ASYNC = lib.UV_ASYNC
    CHECK = lib.UV_CHECK
    FILE = lib.UV_FILE
    IDLE = lib.UV_IDLE
    PIPE = lib.UV_NAMED_PIPE
    POLL = lib.UV_POLL
    PREPARE = lib.UV_PREPARE
    PROCESS = lib.UV_PROCESS
    SIGNAL = lib.UV_SIGNAL
    STREAM = lib.UV_STREAM
    TCP = lib.UV_TCP
    TIMER = lib.UV_TIMER
    TTY = lib.UV_TTY
    UDP = lib.UV_UDP

    FS_EVENT = lib.UV_FS_EVENT
    FS_POLL = lib.UV_FS_POLL

    def __call__(self, cls):
        """
        Associate the class which implements the handle type with
        the corresponding enumeration object. Allows the usage of
        enumeration fields as class decorators.
        """
        self.cls = cls
        return cls


@ffi.callback('uv_alloc_cb')
def uv_alloc_cb(uv_handle, suggested_size, uv_buf):
    handle = base.BaseHandle.detach(uv_handle)
    """ :type: uv.Handle """
    if handle is None:  # pragma: no cover
        library.uv_buffer_set(uv_buf, ffi.NULL, 0)
    else:
        try:
            handle.allocator.allocate(handle, suggested_size, uv_buf)
        except Exception:  # pragma: no cover
            warnings.warn('exception in lib uv allocator')
            library.uv_buffer_set(uv_buf, ffi.NULL, 0)


@HandleTypes.UNKNOWN
@HandleTypes.HANDLE
class UVHandle(object):
    """
    Base class of all internal libuv based handles.

    :raises uv.LoopClosedError:
        loop has already been closed

    :param loop:
        loop where the handle should run on
    :param arguments:
        arguments passed to the libuv handle init function

    :type loop:
        uv.Loop
    :type arguments:
        tuple
    """

    __slots__ = ['__weakref__', 'loop', 'base_handle', 'uv_handle',
                 'on_closed', 'data', 'allocator']

    uv_handle_type = None
    uv_handle_init = None

    def __init__(self, loop, arguments=()):
        self.loop = loop or Loop.get_current()
        if self.loop.closed:
            raise error.ClosedLoopError()

        self.base_handle = base.BaseHandle(self, self.loop.base_loop,
                                           self.__class__.uv_handle_type,
                                           self.__class__.uv_handle_init, arguments)

        self.uv_handle = self.base_handle.uv_handle

        self.on_closed = common.dummy_callback
        """
        Callback which should run after the handle has been closed.


        .. function:: on_closed(handle)

            :param handle:
                handle which has been closed

            :type handle:
                uv.Handle


        :readonly:
            False
        :type:
            ((uv.Handle) -> None) | ((Any, uv.Handle) -> None)
        """

        self.data = None
        """
        User-specific data of any type. This is necessary because of
        the usage of slots.

        :readonly:
            False
        :type:
            Any
        """
        self.allocator = self.loop.allocator
        """
        Allocator used to allocate new read buffers for this handle.

        :readonly:
            False
        :type:
            uv.loop.Allocator
        """

    @property
    def closing(self):
        """
        :readonly:
            True
        :type:
            bool
        """
        return self.base_handle.closing

    @property
    def closed(self):
        """
        :readonly:
            True
        :type:
            bool
        """
        return self.base_handle.closed

    @property
    def active(self):
        """
        :readonly:
            True
        :type:
            bool
        """
        if self.closed:
            return False
        return bool(lib.uv_is_active(self.uv_handle))

    @property
    def referenced(self):
        """
        :readonly:
            False
        :type:
            bool
        """
        if self.closed:
            return False
        return bool(lib.uv_has_ref(self.uv_handle))

    @referenced.setter
    def referenced(self, referenced):
        """
        :param referenced:
            referenced status which should be set
        :type referenced:
            bool
        """
        if referenced:
            self.reference()
        else:
            self.dereference()

    @property
    def send_buffer_size(self):
        """
        Size of the send buffer that the operating system uses for the
        socket. The following handles are supported: TCP and UDP
        handles on Unix and Windows, Pipe handles only on Unix. On all
        unsupported handles this will raise :class:`uv.UVError` with
        error code `EINVAL` (:class:`uv.error.ArgumentError`).

        .. note::
            Unlike libuv this library abstracts the different
            behaviours on Linux and other operating systems. This
            means, the size set is divided by two on Linux because
            Linux internally multiplies it by two.

        :raises uv.UVError:
            error while getting/setting the send buffer size
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :readonly:
            False
        :type:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        c_buffer_size = ffi.new('int*')
        code = lib.uv_send_buffer_size(self.uv_handle, c_buffer_size)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        return c_buffer_size[0]

    @send_buffer_size.setter
    def send_buffer_size(self, size):
        """
        :raises uv.UVError:
            error while getting/setting the send buffer size
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param size:
            size of the send buffer

        :type size:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        c_buffer_size = ffi.new('int*', int(size / 2) if common.is_linux else size)
        code = lib.uv_send_buffer_size(self.uv_handle, c_buffer_size)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    @property
    def receive_buffer_size(self):
        """
        Size of the receive buffer that the operating system uses for
        the socket. The following handles are supported: TCP and UDP
        handles on Unix and Windows, Pipe handles only on Unix. On all
        unsupported handles this will raise :class:`uv.UVError` with
        error code `EINVAL` (:class:`uv.error.ArgumentError`).

        .. note::
            Unlike libuv this library abstracts the different
            behaviours on Linux and other operating systems. This
            means, the size set is divided by two on Linux because
            Linux internally multiplies it by two.

        :raises uv.UVError:
            error while getting/setting the receive buffer size
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :readonly:
            False
        :type:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        c_buffer_size = ffi.new('int*')
        code = lib.uv_recv_buffer_size(self.uv_handle, c_buffer_size)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        return c_buffer_size[0]

    @receive_buffer_size.setter
    def receive_buffer_size(self, size):
        """
        :raises uv.UVError:
            error while getting/setting the receive buffer size
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param size:
            size of the receive buffer

        :type size:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        c_buffer_size = ffi.new('int*', int(size / 2) if common.is_linux else size)
        code = lib.uv_recv_buffer_size(self.uv_handle, c_buffer_size)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def fileno(self):
        """
        Get the platform dependent file descriptor equivalent. The
        following handles are supported: TCP, UDP, TTY, Pipes and Poll.
        On all other handles this will raise :class:`uv.UVError` with
        error code `EINVAL` (:class:`uv.error.ArgumentError`).

        If a handle does not have an attached file descriptor yet this
        method will raise :class:`uv.UVError` with error code `EBADF`
        (:class:`uv.error.BadFileDescriptorError`).

        .. warning::
            Be very careful when using this method. Libuv assumes it is
            in control of the file descriptor so any change to it may
            result in unpredictable malfunctions.

        :raises uv.UVError:
            error while receiving fileno
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :return:
            platform dependent file descriptor equivalent
        :rtype:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        uv_fd = ffi.new('uv_os_fd_t*')
        code = lib.uv_fileno(self.uv_handle, uv_fd)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        return ffi.cast('int*', uv_fd)[0]

    def reference(self):
        """
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing
        """
        if self.closing:
            raise error.ClosedHandleError()
        lib.uv_ref(self.uv_handle)

    def dereference(self):
        """
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing
        """
        if self.closing:
            raise error.ClosedHandleError()
        lib.uv_unref(self.uv_handle)

    def close(self, on_closed=None):
        """
        :param on_closed:
            callback which should run after the handle has been closed
            (overrides the current callback if specified)

        :type on_closed:
            ((uv.Handle) -> None) | ((Any, uv.Handle) -> None)
        """
        if self.closing:
            return
        self.on_closed = on_closed or self.on_closed
        self.set_pending()
        self.base_handle.close()

    def set_pending(self):
        """
        .. warning::
            This method is only for internal purposes and is not part
            of the official API. It deactivates the garbage collection
            for the handle which means the handle and the corresponding
            loop are excluded from garbage collection. You should never
            call it directly!
        """
        self.loop.structure_set_pending(self)

    def clear_pending(self):
        """
        .. warning::
            This method is only for internal purposes and is not part
            of the official API. It reactivates the garbage collection
            for the handle. You should never call it directly!
        """
        self.loop.structure_clear_pending(self)


HandleTypes.cls = UVHandle

abstract.Handle.register(UVHandle)
