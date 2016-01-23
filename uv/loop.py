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

import abc
import sys
import threading
import traceback
import warnings

from . import common, error, library
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
    prevent deadlocks or livelocks.

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
        c_base = library.uv_buffer_get_base(uv_buffer)
        return bytes(ffi.buffer(c_base, length)) if length > 0 else b''


@ffi.callback('uv_alloc_cb')
def uv_alloc_cb(uv_handle, suggested_size, uv_buf):
    handle = library.detach(uv_handle)
    """ :type: uv.Handle """
    try:
        handle.allocator.allocate(handle, suggested_size, uv_buf)
    except:
        warnings.warn('exception in lib uv allocator')
        library.uv_buffer_set(uv_buf, ffi.NULL, 0)


class Loop(object):
    """
    The event loop is the central part of this library. It takes care
    of polling for IO and scheduling callbacks to be run based on
    different sources of events.

    .. note::
        Event loops are not garbage collected until they are explicitly
        closed. Please close all loops you do not need anymore so
        resources could be freed.
    """

    _global_lock = threading.Lock()
    _thread_locals = threading.local()
    _default = None
    # we keep track of all loops here to prevent them from being garbage collected
    _loops = set()

    @classmethod
    def get_default(cls, instantiate=True, **arguments):
        """
        Get the default (across multiple threads) event loop. Note that
        although this returns the same loop across multiple threads
        loops are not thread safe. Normally there is one thread running
        the default loop and others interfering with it trough
        :class:`uv.Async` handles.

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
                Loop._default = Loop(default=True, **arguments)
            return Loop._default

    @classmethod
    def get_current(cls, instantiate=True, **arguments):
        """
        Get the current (thread local) default event loop. Loops
        register themselves as current loop on instantiation and in
        their :func:`uv.Loop.run` method.

        :param instantiate:
            instantiate a new loop if there is no current loop

        :type instantiate:
            bool

        :return:
            current threads default loop
        :rtype:
            Loop
        """
        loop = getattr(cls._thread_locals, 'loop', None)
        if loop is None and instantiate:
            return cls(**arguments)
        return loop

    @classmethod
    def get_loops(cls):
        """
        Get a set of all instantiated loops which have not been closed
        until the time of calling.

        :return:
            instantiated loops which have not been closed
        :rtype:
            frozenset[Loop]
        """
        with cls._global_lock:
            return frozenset(cls._loops)

    def __init__(self, allocator=None, default=False, buffer_size=2**16):
        """
        :param allocator:
            read buffer allocator
        :param default:
            use the lib uv default loop
        :param buffer_size:
            size of the default allocators read buffer

        :type allocator:
            uv.loop.Allocator
        :type default:
            bool
        :type buffer_size:
            int
        """
        if default:
            with Loop._global_lock:
                if Loop._default:
                    raise RuntimeError('global default loop already instantiated')
                self.uv_loop = lib.uv_default_loop()
                if not self.uv_loop:
                    raise RuntimeError('error initializing default loop')
        else:
            self.uv_loop = ffi.new('uv_loop_t*')
            code = lib.uv_loop_init(self.uv_loop)
            if code < 0:
                raise error.UVError(code)

        self.attachment = library.attach(self.uv_loop, self)

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
        Type of last exception handled by excepthook.

        :readonly:
            True
        :type:
            type
        """
        self.exc_value = None
        """
        Instance of last exception handled by excepthook.

        :readonly:
            True
        :type:
            BaseException
        """
        self.exc_traceback = None
        """
        Traceback which encapsulates the call stack at the point where
        the last exception handled by excepthook originally occurred.

        :readonly:
            True
        :type:
            traceback
        """
        self.handles = set()
        """
        Contains all handles running on this loop which have not already
        been closed. We have to keep references to every single handle in
        this set because otherwise they are garbage collected before they
        have been closed which leads to segmentation faults.

        :readonly: True
        :type: set[Handle]
        """
        self.requests = set()
        """
        Contains all requests running on this loop which are not already
        finished. We have to keep references to every single request in
        this set because otherwise they are garbage collected before they
        are finished which leads to segmentation faults.

        :readonly: True
        :type: set[Handle]
        """
        self.closed = False
        """
        Loop has been closed. This is `True` right after close has been
        called. It means all internal resources are freed and this loop
        is ready to be garbage collected. Operations on a closed loop
        will raise :class:`uv.LoopClosedError`.

        :readonly: True
        :type: bool
        """
        with Loop._global_lock: Loop._loops.add(self)
        self.make_current()

    @property
    def alive(self):
        if self.closed: return False
        return bool(lib.uv_loop_alive(self.uv_loop))

    @property
    def now(self):
        if self.closed: raise error.ClosedLoopError()
        return lib.uv_now(self.uv_loop)

    def fileno(self):
        if self.closed: raise error.ClosedLoopError()
        return lib.uv_backend_fd(self.uv_loop)

    def make_current(self):
        Loop._thread_locals.loop = self

    def update_time(self):
        if self.closed: raise error.ClosedLoopError()
        return lib.uv_update_time(self.uv_loop)

    def get_timeout(self):
        if self.closed: raise error.ClosedLoopError()
        return lib.uv_backend_timeout(self.uv_loop)

    def run(self, mode=RunModes.DEFAULT):
        """
        Run loop
        :param mode:
        :return:
        """
        if self.closed: raise error.ClosedLoopError()
        self.make_current()
        result = bool(lib.uv_run(self.uv_loop, mode))
        return result

    def stop(self):
        if self.closed: return
        lib.uv_stop(self.uv_loop)

    def close(self):
        if self.closed: return
        code = lib.uv_loop_close(self.uv_loop)
        if code < 0: raise error.UVError(code)
        self.uv_loop = None
        self.closed = True
        with Loop._global_lock: Loop._loops.remove(self)
        if Loop._thread_locals.loop is self: Loop._thread_locals.loop = None

    def close_all_handles(self, callback=None):
        for handle in self.handles: handle.close(callback)

    def handle_exception(self):
        self.exc_type, self.exc_value, self.exc_traceback = sys.exc_info()
        try:
            self.excepthook(self, self.exc_type, self.exc_value, self.exc_traceback)
        except:
            # this should never happen during normal operation but if it does the
            # program would be in an undefined state, so exit immediately
            try:
                print('[CRITICAL] error while executing excepthook!')
                traceback.print_exc()
            finally:
                sys.exit(1)
