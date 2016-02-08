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

import abc
import collections
import sys
import threading
import traceback
import warnings

from . import base, common, error, library
from .library import ffi, lib


class RunModes(common.Enumeration):
    """
    Run modes to control the behavior of :func:`uv.Loop.run`.
    """

    DEFAULT = lib.UV_RUN_DEFAULT
    """
    Run the event loop until there are no more active and referenced
    handles or requests. :func:`uv.Loop.run` returns `True` if
    :func:`uv.Loop.stop` was called and there are still active
    handles or requests and `False` otherwise.

    :type: uv.RunModes
    """

    ONCE = lib.UV_RUN_ONCE
    """
    Poll for IO once. Note that :func:`uv.Loop.run` will block if there
    are no pending callbacks. :func:`uv.Loop.run` returns `True` if
    there are still active handles or requests which means the event
    loop should run again sometime in the future.

    :type: uv.RunModes
    """

    NOWAIT = lib.UV_RUN_NOWAIT
    """
    Poll for IO once but do not block if there are no pending
    callbacks. :func:`uv.Loop.run` returns `True` if there are still
    active handles or requests which means the event loop should run
    again sometime in the future.

    :type: uv.RunModes
    """


def default_excepthook(loop, exc_type, exc_value, exc_traceback):
    """
    Default excepthook. Prints a traceback and stops the event loop to
    prevent deadlocks and livelocks.

    :param loop:
        event loop the callback belongs to
    :param exc_type:
        exception class of the thrown exception
    :param exc_value:
        exception instance of the thrown exception
    :param exc_traceback:
        traceback to the stack frame where the exception occoured

    :type loop:
        uv.Loop
    :type exc_type:
        Subclass[Exception]
    :type exc_value:
        Exception
    :type exc_traceback:
        traceback
    """
    print('Exception happened during callback execution!', file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    loop.stop()


class Allocator(common.with_metaclass(abc.ABCMeta)):
    """
    Abstract base class for read buffer allocators. Allows swappable
    allocation strategies and custom read result types.

    .. warning::
        This class exposes some details of the underlying CFFI based
        wrapper — use it with caution. Any errors in the allocator
        might lead to unpredictable behavior.
    """

    @abc.abstractmethod
    def allocate(self, handle, suggested_size, uv_buffer):
        """
        Called if libuv needs a new read buffer. The allocated chunk of
        memory has to be assigned to `uv_buf.base` and the length of
        the chunk to `uv_buf.len` use :func:`library.uv_buffer_set()`
        for assigning. Base might be `NULL` which triggers an `ENOBUFS`
        error in the read callback.

        :param handle:
            handle caused the read
        :param suggested_size:
            suggested buffer size
        :param uv_buffer:
            uv target buffer

        :type handle:
            uv.Handle
        :type suggested_size:
            int
        :type uv_buffer:
            ffi.CData[uv_buf_t]
        """

    @abc.abstractmethod
    def finalize(self, handle, length, uv_buffer):
        """
        Called in the read callback to access the read buffer's data.
        The result of this call is directly passed to the user's read
        callback which allows to use a custom read result type.

        :param handle:
            handle caused the read
        :param length:
            length of bytes read
        :param uv_buffer:
            uv buffer used for reading

        :type handle:
            uv.Handle
        :type length:
            int
        :type uv_buffer:
            ffi.CData[uv_buf_t]

        :return:
            buffer's data (default type is :class:`bytes`)
        :rtype:
            Any | bytes
        """


class DefaultAllocator(Allocator):
    """
    Default read buffer allocator which only uses one buffer and copies
    the data to a python :class:`bytes` object after reading.
    """

    def __init__(self, buffer_size=2**16):
        """
        :param buffer_size:
            size of the internal buffer

        :type buffer_size:
            int
        """
        self.buffer_size = buffer_size
        self.buffer_in_use = False

        self.c_buffer = ffi.new('char[]', self.buffer_size)

    def allocate(self, handle, suggested_size, uv_buffer):
        if self.buffer_in_use:
            # this should never happen because lib uv reads the data right
            # before the execution of the read callback even if there are
            # multiple sockets ready for reading
            library.uv_buffer_set(uv_buffer, ffi.NULL, 0)
        else:
            library.uv_buffer_set(uv_buffer, self.c_buffer, self.buffer_size)
        self.buffer_in_use = True

    def finalize(self, uv_handle, length, uv_buffer):
        self.buffer_in_use = False
        c_base = library.uv_buffer_get(uv_buffer).base
        return bytes(ffi.buffer(c_base, length)) if length > 0 else b''


@ffi.callback('uv_walk_cb')
def uv_walk_cb(uv_handle, c_handles_set):
    handle = base.BaseHandle.detach(uv_handle)
    if handle is not None:
        ffi.from_handle(c_handles_set).add(handle)


class Loop(object):
    """
    The event loop is the central part of this library. It takes care
    of polling for IO and scheduling callbacks to be run based on
    different sources of events.
    """

    _global_lock = threading.RLock()
    _thread_locals = threading.local()
    _default = None

    @classmethod
    def get_default(cls, instantiate=True, **keywords):
        """
        Get the default (across multiple threads) event loop. Note that
        although this returns the same loop across multiple threads
        loops are not thread safe. Normally there is one thread running
        the default loop and others interfering with it trough
        :class:`uv.Async` handles or :func:`uv.Loop.call_later`.

        :param instantiate:
            instantiate the default event loop if it does not exist

        :type instantiate:
            bool

        :return:
            global default loop
        :rtype:
            Loop
        """
        with cls._global_lock:
            if cls._default is None and instantiate:
                Loop._default = Loop(default=True, **keywords)
            return Loop._default

    @classmethod
    def get_current(cls, instantiate=True, **keywords):
        """
        Get the current (thread local) default event loop. Loops
        register themselves as current loop on instantiation and in
        their :func:`uv.Loop.run` method.

        :param instantiate:
            instantiate a new loop if there is no current loop

        :type instantiate:
            bool

        :return:
            current thread's default loop
        :rtype:
            Loop
        """
        loop = getattr(cls._thread_locals, 'loop', None)
        if loop is None and instantiate:
            return cls(**keywords)
        return loop

    def __init__(self, allocator=None, buffer_size=2**16, default=False):
        """
        :raises RuntimeError:
            error while initializing global default loop
        :raises UVError:
            error initializing the new event loop

        :param allocator:
            read buffer allocator
        :param buffer_size:
            size of the default allocators read buffer
        :param default:
            instantiate the default loop

        :type allocator:
            uv.loop.Allocator
        :type buffer_size:
            int
        :type default:
            bool
        """
        if default:
            with Loop._global_lock:
                if Loop._default:
                    raise RuntimeError('global default loop already instantiated')
                Loop._default = self

        self.base_loop = base.BaseLoop(self, default)
        self.uv_loop = self.base_loop.uv_loop

        self.allocator = allocator or DefaultAllocator(buffer_size)

        self.excepthook = default_excepthook
        """
        If an exception occurs during the execution of a callback this
        excepthook is called with the corresponding event loop and
        exception details. The default behavior is to print the
        traceback to stderr and stop the event loop. To override the
        default behavior assign a custom function to this attribute.

        .. note::
            If the excepthook raises an exception itself the program
            would be in an undefined state. Therefore it terminates
            with `sys.exit(1)` in that case immediately.


        .. function:: excepthook(loop, exc_type, exc_value, exc_traceback)

            :param loop:
                corresponding event loop
            :param exc_type:
                exception type (subclass of :class:`BaseException`)
            :param exc_value:
                exception instance
            :param exc_traceback:
                traceback which encapsulates the call stack at the
                point where the exception originally occurred

            :type loop:
                uv.Loop
            :type exc_type:
                type
            :type exc_value:
                BaseException
            :type exc_traceback:
                traceback


        :readonly:
            False
        :type:
            ((uv.Loop, type, Exception, traceback.Traceback) -> None) |
            ((Any, uv.Loop, type, Exception, traceback.Traceback) -> None)
        """
        self.exc_type = None
        """
        Type of last exception handled by the excepthook.

        :readonly:
            True
        :type:
            type
        """
        self.exc_value = None
        """
        Instance of last exception handled by the excepthook.

        :readonly:
            True
        :type:
            BaseException
        """
        self.exc_traceback = None
        """
        Traceback of the last exception handled by the excepthook.

        :readonly:
            True
        :type:
            traceback
        """

        self.make_current()
        self.pending_structures = set()
        self.pending_callbacks = collections.deque()
        self.pending_callbacks_lock = threading.RLock()

    @property
    def closed(self):
        """
        True if and only if the loop has been closed.

        :readonly:
            True
        :rtype:
            bool
        """
        return self.base_loop.closed

    @property
    def alive(self):
        """
        `True` if there are active and referenced handles running on
        the loop, `False` otherwise.

        :readonly:
            True
        :rtype:
            bool
        """
        if self.closed:
            return False
        return bool(lib.uv_loop_alive(self.uv_loop))

    @property
    def now(self):
        """
        Current internal timestamp in milliseconds. The timestamp
        increases monotonically from some arbitrary point in time.

        :readonly:
            True
        :rtype:
            int
        """
        if self.closed:
            raise error.ClosedLoopError()
        return lib.uv_now(self.uv_loop)

    @property
    def handles(self):
        """
        Set of all handles running on the loop.

        :readonly:
            True
        :rtype:
            set
        """
        handles = set()
        if not self.closed:
            lib.uv_walk(self.uv_loop, uv_walk_cb, ffi.new_handle(handles))
        return handles

    def fileno(self):
        """
        Get the file descriptor of the backend. This is only supported
        on kqueue, epoll and event ports.

        :raises uv.UVError:
            error getting file descriptor
        :raises uv.ClosedLoopError:
            loop has already been closed

        :returns:
            backend file descriptor
        :rtype:
            int
        """
        if self.closed:
            raise error.ClosedLoopError()
        return lib.uv_backend_fd(self.uv_loop)

    def make_current(self):
        """
        Make the loop the current thread local default loop.
        """
        Loop._thread_locals.loop = self

    def update_time(self):
        """
        Update the event loop’s concept of “now”. Libuv caches the
        current time at the start of the event loop tick in order to
        reduce the number of time-related system calls.

        :raises uv.ClosedLoopError:
            loop has already been closed

        .. note::
            You won’t normally need to call this function unless you
            have callbacks that block the event loop for longer periods
            of time, where “longer” is somewhat subjective but probably
            on the order of a millisecond or more.
        """
        if self.closed:
            raise error.ClosedLoopError()
        lib.uv_update_time(self.uv_loop)

    def get_timeout(self):
        """
        Get the poll timeout. The return value is in milliseconds, or
        -1 for no timeout.

        :raises uv.ClosedLoopError:
            loop has already been closed

        :returns:
            backend timeout in milliseconds
        :rtype:
            int
        """
        if self.closed:
            raise error.ClosedLoopError()
        return lib.uv_backend_timeout(self.uv_loop)

    def run(self, mode=RunModes.DEFAULT):
        """
        Run the loop in the specified mode.

        :raises uv.ClosedLoopError:
            loop has already been closed

        :param mode:
            run mode

        :type mode:
            uv.RunModes

        :returns:
            run mode specific return value
        :rtype:
            bool
        """
        if self.closed:
            raise error.ClosedLoopError()
        self.make_current()
        return bool(lib.uv_run(self.uv_loop, mode))

    def stop(self):
        """
        Stop the event loop, causing :func:`uv.Loop.run` to end as soon
        as possible. This will happen not sooner than the next loop
        iteration. If this method was called before blocking for IO,
        the loop will not block for IO on this iteration.
        """
        if self.closed:
            return
        lib.uv_stop(self.uv_loop)

    def close(self):
        """
        Closes all internal loop resources. This method must only be
        called once the loop has finished its execution or it will
        raise :class:`uv.error.ResourceBusyError`.

        .. note::
            Loops are automatically closed when they are garbage
            collected. However because the exact time this happens is
            non-deterministic you should close them explicitly.

        :raises uv.UVError:
            error while closing the loop
        :raises uv.error.ResourceBusyError:
            loop is currently running or there are pending operations
        """
        if self.closed:
            return
        code = self.base_loop.close()
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        if Loop._thread_locals.loop is self:
            Loop._thread_locals.loop = None

    def close_all_handles(self, on_closed=None):
        """
        Close all handles.

        :param on_closed:
            callback which should run after a handle has been closed
            (overrides the current callback if specified)

        :type on_closed:
            ((uv.Handle) -> None) | ((Any, uv.Handle) -> None)
        """
        for handle in self.handles:
            handle.close(on_closed)

    def call_later(self, callback, *arguments, **keywords):
        """
        Schedule a callback to run at some later point in time.

        This method is thread safe.

        :param callback:
            callback which should run at some later point in time
        :param arguments:
            arguments that should be passed to the callback
        :param keywords:
            keyword arguments that should be passed to the callback

        :type callback:
            callable
        :type arguments:
            tuple
        :type keywords:
            dict
        """
        with self.pending_callbacks_lock:
            self.pending_callbacks.append((callback, arguments, keywords))
            self.base_loop.wakeup()
            self.base_loop.reference_internal_async()

    def on_wakeup(self):
        """
        Called after the event loop has been woken up.

         .. warning::
            This method is only for internal purposes and is not part
            of the official API. You should never call it directly!
        """
        try:
            while True:
                with self.pending_callbacks_lock:
                    callback, arguments, keywords = self.pending_callbacks.popleft()
                try:
                    callback(*arguments, **keywords)
                except BaseException:
                    self.handle_exception()
        except IndexError:
            pass
        with self.pending_callbacks_lock:
            if not self.pending_callbacks:
                self.base_loop.dereference_internal_async()

    def handle_exception(self):
        """
        Handle the current exception using the excepthook.

        .. warning::
            This method is only for internal purposes and is not part
            of the official API. You should never call it directly!
        """
        self.exc_type, self.exc_value, self.exc_traceback = sys.exc_info()
        try:
            self.excepthook(self, self.exc_type, self.exc_value, self.exc_traceback)
        except BaseException:
            # this should never happen during normal operation but if it does the
            # program would be in an undefined state, so exit immediately
            try:
                print('[CRITICAL] error while executing excepthook!', file=sys.stderr)
                traceback.print_exc()
            finally:
                sys.exit(1)

    def structure_set_pending(self, structure):
        """
        Add a structure to the set of pending structures.

        .. warning::
            This method is only for internal purposes and is not part
            of the official API. You should never call it directly!

        :type structure:
            uv.Handle | uv.Request
        """
        self.pending_structures.add(structure)

    def structure_clear_pending(self, structure):
        """
        Remove a structure from the set of pending structures.

        .. warning::
            This method is only for internal purposes and is not part
            of the official API. You should never call it directly!

        :type structure:
            uv.Handle | uv.Request
        """
        try:
            self.pending_structures.remove(structure)
        except KeyError:
            pass

    def structure_is_pending(self, structure):
        """
        Return true if and only if the structure is pending.

        .. warning::
            This method is only for internal purposes and is not part
            of the official API. You should never call it directly!

        :type structure:
            uv.Handle | uv.Request
        """
        return structure in self.pending_structures
