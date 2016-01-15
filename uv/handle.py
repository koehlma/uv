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

from . import common, error, library, request
from .library import ffi, lib
from .loop import Loop

__all__ = ['Handle']


class HandleType(common.Enumeration):
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
        self.cls = cls
        return cls


@ffi.callback('uv_close_cb')
def uv_close_cb(uv_handle):
    handle = library.detach(uv_handle)
    """ :type: uv.Handle """
    try:
        handle.on_closed(handle)
    except:
        handle.loop.handle_exception()
    handle.destroy()


@HandleType.UNKNOWN
@HandleType.HANDLE
class Handle(object):
    """
    Handles represent long-lived objects capable of performing certain
    operations while active. This is the base class of all handles except
    the file and SSL handle, which are pure Python.

    :raises uv.LoopClosedError: loop has already been closed

    :param uv_handle: allocated c struct for this handle
    :param loop: loop where the handle should run on

    :type uv_handle: ffi.CData
    :type loop: Loop
    """

    __slots__ = ['uv_handle', 'attachment', 'loop', 'on_closed',
                 'closed', 'closing', 'data']

    def __init__(self, uv_handle, loop=None):
        self.uv_handle = ffi.cast('uv_handle_t*', uv_handle)
        self.attachment = library.attach(self.uv_handle, self)
        self.loop = loop or Loop.get_current()
        """
        Loop where the handle is running on.

        :readonly: True
        :type: Loop
        """
        self.on_closed = common.dummy_callback
        """
        Callback which should be called after the handle has been closed.

        .. function:: on_closed(Handle)

        :readonly: False
        :type: (uv.Handle) -> None
        """
        self.closed = False
        """
        Handle has been closed. This is `True` right after the close callback
        has been called. It means all internal resources are freed and this
        handle is ready to be garbage collected.

        :readonly: True
        :type: bool
        """
        self.closing = False
        """
        Handle is already closed or is closing. This is `True` right after
        close has been called. Operations on a closed or closing handle will
        raise :class:`uv.HandleClosedError`.

        :readonly: True
        :type: bool
        """
        self.data = None
        """
        User-specific data of any type (necessary because we are using slots).

        :readonly: False
        """
        if self.loop.closed: raise error.ClosedLoopError()
        self.loop.handles.add(self)

    @property
    def active(self):
        """
        Handle is active or not. What "active" means depends on the handle:

        - :class:`uv.Async`: is always active and cannot be deactivated

        - :class:`uv.Pipe`, :class:`uv.TCP`, :class:`uv.UDP`, ...: basically
          any handle dealing with IO is active when it is doing something
          involves IO like reading, writing, connecting or listening

        - :class:`uv.Check`, :class:`uv.Idle`, :class:`uv.Timer`, ...: handle
          is active when it has been started and not yet stopped

        :readonly: True
        :type: bool
        """
        if self.closed: return False
        return bool(lib.uv_is_active(self.uv_handle))

    @property
    def referenced(self):
        """
        Handle is referenced or not. If the event loop runs in default mode it
        will exit when there are no more active and referenced handles left. This
        has nothing to do with CPython's reference counting.

        :readonly: False
        :type: bool
        """
        if self.closed: return False
        return bool(lib.uv_has_ref(self.uv_handle))

    @referenced.setter
    def referenced(self, referenced):
        """
        :param referenced: referenced status which should be set
        :type referenced: bool
        """
        if referenced: self.reference()
        else: self.dereference()

    @property
    def send_buffer_size(self):
        """
        Size of the send buffer that the operating system uses for the
        socket. The following handles are supported: TCP and UDP handles
        on Unix and Windows, Pipe handles only on Unix. On all unsupported
        handles this will raise :class:`uv.UVError` with `StatusCode.EINVAL`.

        .. note::

            Unlike libuv this library abstracts the different behaviours on Linux
            and other operating systems. This means, the size set is divided by
            two on Linux because Linux internally multiplies it by two.

        :raises uv.UVError: error while getting/setting the send buffer size
        :raises uv.HandleClosedError: handle has already been closed or is closing
        :readonly: False
        :type: int
        """
        if self.closing: raise error.ClosedHandleError()
        c_buffer_size = ffi.new('int*')
        code = lib.uv_send_buffer_size(self.uv_handle, c_buffer_size)
        if code < 0: raise error.UVError(code)
        return c_buffer_size[0]

    @send_buffer_size.setter
    def send_buffer_size(self, size):
        """
        :raises uv.UVError: error while getting/setting the send buffer size
        :raises uv.HandleClosedError: handle has already been closed or is closing
        :param size: size of the send buffer
        :type size: int
        """
        if self.closing: raise error.ClosedHandleError()
        c_buffer_size = ffi.new('int*', int(size / 2) if is_linux else size)
        code = lib.uv_send_buffer_size(self.uv_handle, c_buffer_size)
        if code < 0: raise error.UVError(code)

    @property
    def receive_buffer_size(self):
        """
        Size of the receive buffer that the operating system uses for the
        socket. The following handles are supported: TCP and UDP handles
        on Unix and Windows, Pipe handles only on Unix. On all unsupported
        handles this will raise :class:`uv.UVError` with `StatusCode.EINVAL`.

        .. note::

            Unlike libuv this library abstracts the different behaviours on Linux
            and other operating systems. This means, the size set is divided by
            two on Linux because Linux internally multiplies it by two.

        :raises uv.UVError: error while getting/setting the receive buffer size
        :raises uv.HandleClosedError: handle has already been closed or is closing
        :readonly: False
        :type: int
        """
        if self.closing: raise error.ClosedHandleError()
        c_buffer_size = ffi.new('int*')
        code = lib.uv_recv_buffer_size(self.uv_handle, c_buffer_size)
        if code < 0: raise error.UVError(code)
        return c_buffer_size[0]

    @receive_buffer_size.setter
    def receive_buffer_size(self, size):
        """
        :raises uv.UVError: error while getting/setting the receive buffer size
        :raises uv.HandleClosedError: handle has already been closed or is closing
        :param size: size of the receive buffer
        :type size: int
        """
        if self.closing: raise error.ClosedHandleError()
        c_buffer_size = ffi.new('int*', int(size / 2) if is_linux else size)
        code = lib.uv_recv_buffer_size(self.uv_handle, c_buffer_size)
        if code < 0: raise error.UVError(code)

    def fileno(self):
        """
        Gets the platform dependent file descriptor equivalent. The following
        handles are supported: TCP, UDP, TTY, Pipes and Poll. On all other
        handles this will raise :class:`uv.UVError` with `StatusCode.EINVAL`.

        If a handle does not have an attached file descriptor yet this method
        will raise :class:`uv.UVError` with `StatusCode.EBADF`.

        .. warning::

            Be very careful when using this method. Libuv assumes it
            is in control of the file descriptor so any change to it
            may result in unpredictable malfunctions.

        :raises uv.UVError: error while receiving fileno
        :raises uv.HandleClosedError: handle has already been closed or is closing
        :return: platform dependent file descriptor equivalent
        :rtype: int
        """
        if self.closing: raise error.ClosedHandleError()
        uv_fd = ffi.new('uv_os_fd_t*')
        code = lib.uv_fileno(self.uv_handle, uv_fd)
        if code < 0: raise error.UVError(code)
        return ffi.cast('int*', uv_fd)[0]

    def reference(self):
        """
        References the handle. If the event loop runs in default mode it will
        exit when there are no more active and referenced handles left. This
        has nothing to do with CPython's reference counting. References are
        idempotent, that is, if a handle is already referenced calling this
        method again will have not effect.

        :raises uv.HandleClosedError: handle has already been closed or is closing
        """
        if self.closing: raise error.ClosedHandleError()
        lib.uv_ref(self.uv_handle)

    def dereference(self):
        """
        Dereferences the handle. If the event loop runs in default mode it
        will exit when there are no more active and referenced handles left.
        This has nothing to do with CPython's reference counting. References
        are idempotent, that is, if a handle is not referenced calling this
        method again will have not effect.

        :raises uv.HandleClosedError: handle has already been closed or is closing
        """
        if self.closing: raise error.ClosedHandleError()
        lib.uv_unref(self.uv_handle)

    def close(self, on_closed=None):
        """
        Closes the handle and frees all resources afterwards. Please make sure
        to call this method on any handle you do not need anymore. Handles do
        not close automatically and are also not garbage collected unless you
        have closed them exlicitly (explicit is better than implicit). This
        method is idempotent, that is, if the handle is already closed or is
        closing calling this method will have no effect.

        In-progress requests, like :class:`uv.ConnectRequest` or
        :class:`uv.WriteRequest`, are cancelled and have their callbacks
        called asynchronously with :class:`StatusCode.ECANCELED`

        After this method has been called on a handle no other operations can be
        performed on it, they will raise :class:`uv.HandleClosedError`.

        :param on_closed: callback called after the handle has been closed
        :type on_closed: (Handle) -> None
        """
        if self.closing: return
        self.closing = True
        self.on_closed = on_closed or self.on_closed
        lib.uv_close(self.uv_handle, uv_close_cb)

    def destroy(self):
        """
        .. warning::

            This method is used internally to free all allocated C resources and
            make sure there are no references from Python anymore to those objects
            after the handle has been closed. You should never call it directly!
        """
        self.closing = True
        self.closed = True
        self.loop.handles.remove(self)


HandleType.cls = Handle
