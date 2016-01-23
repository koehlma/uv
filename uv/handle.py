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

from . import common, error, library
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


@ffi.callback('uv_close_cb')
def uv_close_cb(uv_handle):
    handle = library.detach(uv_handle)
    """ :type: uv.Handle """
    try:
        handle.on_closed(handle)
    except:
        handle.loop.handle_exception()
    handle.set_closed()


# the following code is considered free of data races because of the
# GIL; if we introduce locking here this might deadlock because the
# GC could perform a collection cycle within the with statement
# TODO: this is a really nasty and ugly hack of course
_finalizing = set()


@ffi.callback('uv_close_cb')
def uv_close_cb_finalize(uv_handle):
    _finalizing.remove(uv_handle)


def handle_finalizer(uv_handle):
    # do not garbage collect the handle until it has been closed
    _finalizing.add(uv_handle)
    # remove attached garbage collected handle
    uv_handle.data = ffi.NULL
    # TODO: this might lead to data races
    lib.uv_close(ffi.cast('uv_handle_t*', uv_handle), uv_close_cb_finalize)


@HandleTypes.UNKNOWN
@HandleTypes.HANDLE
class Handle(object):
    """
    Handles represent long-lived objects capable of performing certain
    operations while active. This is the base class of all handles
    except the file and SSL handle, which are pure Python.

    .. note::
        Handles underlie a special garbage collection strategy which
        means they are not garbage collected as other objects. If a
        handle is able to do anything in the program for example
        calling a callback it is excluded from garbage collection as
        well as the corresponding event loop.

    :raises uv.LoopClosedError:
        loop has already been closed

    :param uv_handle:
        allocated c struct for this handle (with CFFI ownership)
    :param loop:
        loop where the handle should run on

    :type uv_handle:
        ffi.CData
    :type loop:
        uv.Loop
    """

    __slots__ = ['__weakref__', 'loop', 'uv_handle', 'attachment', 'on_closed',
                 'closed', 'closing', 'data', 'allocator']

    def __init__(self, uv_handle, loop=None):
        self.loop = loop or Loop.get_current()
        if self.loop.closed:
            raise error.ClosedLoopError()
        self.uv_handle = ffi.cast('uv_handle_t*', uv_handle)
        self.attachment = library.attach(self.uv_handle, self)
        """
        Loop the handle is running on.

        :readonly:
            True
        :type:
            uv.Loop
        """
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
        self.closed = False
        """
        Handle has been closed. This is `True` right after the close
        callback has been called. It means all internal resources are
        freed and this handle is ready to be garbage collected.

        :readonly:
            True
        :type:
            bool
        """
        self.closing = False
        """
        Handle is already closed or is closing. This is `True` right
        after close has been called. Operations on a closed or closing
        handle will raise :class:`uv.HandleClosedError`.

        :readonly:
            True
        :type:
            bool
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
        common.attach_finalizer(self, handle_finalizer, uv_handle)

    @property
    def active(self):
        """
        Handle is active or not. What "active" means depends on the
        handle type:

        - :class:`uv.Async`:
            is always active and cannot be deactivated

        - :class:`uv.Pipe`, :class:`uv.TCP`, :class:`uv.UDP`, …:
            basically any handle dealing with IO is active when it is
            doing something involves IO like reading, writing,
            connecting or listening

        - :class:`uv.Check`, :class:`uv.Idle`, :class:`uv.Timer`, …:
            handle is active when it has been started and not yet
            stopped

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
        Handle is referenced or not. If the event loop runs in default
        mode it will exit when there are no more active and referenced
        handles left. This has nothing to do with CPython's reference
        counting.

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
        error code `EINVAL` (:class:`uv.error.InvalidTypeError`).

        .. note::
            Unlike libuv this library abstracts the different
            behaviours on Linux and other operating systems. This
            means, the size set is divided by two on Linux because
            Linux internally multiplies it by two.

        :raises uv.UVError:
            error while getting/setting the send buffer size
        :raises uv.HandleClosedError:
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
        if code < 0:
            raise error.UVError(code)
        return c_buffer_size[0]

    @send_buffer_size.setter
    def send_buffer_size(self, size):
        """
        :raises uv.UVError:
            error while getting/setting the send buffer size
        :raises uv.HandleClosedError:
            handle has already been closed or is closing

        :param size:
            size of the send buffer

        :type size:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        c_buffer_size = ffi.new('int*', int(size / 2) if is_linux else size)
        code = lib.uv_send_buffer_size(self.uv_handle, c_buffer_size)
        if code < 0:
            raise error.UVError(code)

    @property
    def receive_buffer_size(self):
        """
        Size of the receive buffer that the operating system uses for
        the socket. The following handles are supported: TCP and UDP
        handles on Unix and Windows, Pipe handles only on Unix. On all
        unsupported handles this will raise :class:`uv.UVError` with
        error code `EINVAL` (:class:`uv.error.InvalidTypeError`).

        .. note::
            Unlike libuv this library abstracts the different
            behaviours on Linux and other operating systems. This
            means, the size set is divided by two on Linux because
            Linux internally multiplies it by two.

        :raises uv.UVError:
            error while getting/setting the receive buffer size
        :raises uv.HandleClosedError:
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
        if code < 0:
            raise error.UVError(code)
        return c_buffer_size[0]

    @receive_buffer_size.setter
    def receive_buffer_size(self, size):
        """
        :raises uv.UVError:
            error while getting/setting the receive buffer size
        :raises uv.HandleClosedError:
            handle has already been closed or is closing

        :param size:
            size of the receive buffer

        :type size:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        c_buffer_size = ffi.new('int*', int(size / 2) if is_linux else size)
        code = lib.uv_recv_buffer_size(self.uv_handle, c_buffer_size)
        if code < 0:
            raise error.UVError(code)

    def fileno(self):
        """
        Get the platform dependent file descriptor equivalent. The
        following handles are supported: TCP, UDP, TTY, Pipes and Poll.
        On all other handles this will raise :class:`uv.UVError` with
        error code `EINVAL` (:class:`uv.error.InvalidTypeError`).

        If a handle does not have an attached file descriptor yet this
        method will raise :class:`uv.UVError` with error code `EBADF`
        (:class:`uv.error.BadFileDescriptorError`).

        .. warning::
            Be very careful when using this method. Libuv assumes it is
            in control of the file descriptor so any change to it may
            result in unpredictable malfunctions.

        :raises uv.UVError:
            error while receiving fileno
        :raises uv.HandleClosedError:
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
        if code < 0:
            raise error.UVError(code)
        return ffi.cast('int*', uv_fd)[0]

    def reference(self):
        """
        Reference the handle. If the event loop runs in default mode
        it will exit when there are no more active and referenced
        handles left. This has nothing to do with CPython's reference
        counting. References are idempotent, that is, if a handle is
        referenced calling this method again will have not effect.

        :raises uv.HandleClosedError:
            handle has already been closed or is closing
        """
        if self.closing:
            raise error.ClosedHandleError()
        lib.uv_ref(self.uv_handle)

    def dereference(self):
        """
        Dereference the handle. If the event loop runs in default mode
        it will exit when there are no more active and referenced
        handles left. This has nothing to do with CPython's reference
        counting. References are idempotent, that is, if a handle is
        not referenced calling this method again will have not effect.

        :raises uv.HandleClosedError:
            handle has already been closed or is closing
        """
        if self.closing:
            raise error.ClosedHandleError()
        lib.uv_unref(self.uv_handle)

    def close(self, on_closed=None):
        """
        Close the handle. Please make sure to call this method on any
        handle you do not need anymore. This method is idempotent, that
        is, if the handle is already closed or is closing calling it
        will have no effect at all.

        In-progress requests, like connect or write requests, are
        cancelled and have their callbacks called asynchronously with
        :class:`uv.StatusCodes.ECANCELED`.

        After this method has been called on a handle no operations can
        be performed on it (they raise :class:`uv.HandleClosedError`).

        .. note::
            Handles are automatically closed when they are garbage
            collected. However because the exact time this happens is
            non-deterministic you should close all handles explicitly.
            Especially if they handle external resources.

        :param on_closed:
            callback which should run after the handle has been closed
            (overrides the current callback if specified)

        :type on_closed:
            ((uv.Handle) -> None) | ((Any, uv.Handle) -> None)
        """
        if self.closing:
            return
        self.closing = True
        self.on_closed = on_closed or self.on_closed
        # exclude the handle from garbage collection until it is closed
        self.gc_exclude()
        # the finalizer does not have to close the handle anymore
        common.detach_finalizer(self)
        lib.uv_close(self.uv_handle, uv_close_cb)

    def set_closed(self):
        """
        .. warning::
            This method is only for internal purposes and is not part
            of the official API. It sets the handles state to closed
            and activates garbage collection for the handle. You should
            never call it directly!
        """
        self.closing = True
        self.closed = True
        self.gc_include()

    def gc_exclude(self):
        """
        .. warning::
            This method is only for internal purposes and is not part
            of the official API. It deactivates the garbage collection
            for the handle which means the handle and the corresponding
            loop are excluded from garbage collection. You should never
            call it directly!
        """
        self.loop.gc_exclude_structure(self)

    def gc_include(self):
        """
        .. warning::
            This method is only for internal purposes and is not part
            of the official API. It reactivates the garbage collection
            for the handle. You should never call it directly!
        """
        self.loop.gc_include_structure(self)


HandleTypes.cls = Handle
