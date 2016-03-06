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

"""
This module provides low level data structures.

Python's automatic memory management ensures that all unreachable
objects are garbage collected. This is problematic when it comes to
Python code interacting with C code, because all objects have to be
kept alive until they are closed gracefully by libuv.

To archive a specific garbage collection semantic (description follows)
for user objects, this library uses cyclic references. Therefore the
`__del__` method can not be used to close objects.

To solve this problem there are two different object layers. The user
code layer and the base layer. For every libuv object there is one
corresponding object on each layer. User code objects, exposed by the
official API, are safe to garbage collect. When they have been garbage
collected the garbage collection notifies the corresponding base level
object which closes the underlying libuv object. After the libuv object
has been closed the base object will be garbage collected too.

We introduce the following garbage collection semantic:

Handles and requests could be in two different states, normal state and
pending state. Pending state means they are able to interact with user
code by themselves sometime in the future. Therefore they are only
garbage collected together with the event loop they are running on
which is ensured by a reference cycle. Handles and requests in normal
state are garbage collected if they are not referenced by user code. A
loop and all attached handles and requests are garbage collected if
there is no reference to neither of them.

This is reasonable because we do not want to close handles or requests
that call user code sometime in the future if the loop is running. If
there is no reference neither to the loop nor to any handle or request
corresponding to the loop, user code will be unable to start the event
loop, so all handles and requests are dead and can be garbage collected
even if they are in pending state.

The semantic is archived by the following reference system:
- loop -> pending handles and requests
- handles and requests -> loop
"""

import weakref

from . import error
from .library import ffi, lib

_loops = set()


@ffi.callback('uv_async_cb')
def base_async_cb(uv_async):
    base_loop = ffi.from_handle(uv_async.data)
    """ :type: BaseLoop """
    base_loop.on_wakeup()


@ffi.callback('uv_prepare_cb')
def base_prepare_cb(uv_prepare):
    base_loop = ffi.from_handle(uv_prepare.data)
    """ :type: BaseLoop """
    base_loop.on_prepare()


@ffi.callback('uv_walk_cb')
def base_walk_close_cb(uv_handle, _):
    if not lib.uv_is_closing(uv_handle):
        lib.uv_close(uv_handle, ffi.NULL)


class BaseLoop(object):
    """
    This class implements an internal low level loop.

    It is the root anchor of every event loop. As long as a loop has
    not been closed a global reference is kept to the corresponding
    base loop. This ensures the base loop itself and all corresponding
    libuv objects which have not been closed are excluded from garbage
    collection. After the base loop has been closed, either by garbage
    collection of the user code loop or explicitly be user code the
    global reference is removed so resources could be freed.
    """

    def __init__(self, user_loop, default=False):
        """
        :param user_loop:
            the corresponding user level loop
        :param default:
            use the libuv default loop instead of creating a new one

        :type user_loop:
            uv.Loop
        :type default:
            bool

        :raises RuntimeError:
            error initializing the default loop
        :raises UVError:
            error initializing the event loop
        """
        self.c_reference = ffi.new_handle(self)

        self.uv_loop = lib.uv_default_loop() if default else ffi.new('uv_loop_t*')
        if default and not self.uv_loop:  # pragma: no cover
            raise RuntimeError('error initializing default loop')
        self.uv_loop.data = self.c_reference

        self.weak_user_loop = weakref.ref(user_loop, self._destroy)

        self.handles = set()
        self.requests = set()

        self.handles_to_close = set()
        self.requests_to_cancel = set()

        self.closed = False

        self.internal_uv_async = ffi.new('uv_async_t*')
        self.internal_uv_async.data = self.c_reference
        self.internal_uv_prepare = ffi.new('uv_prepare_t*')
        self.internal_uv_prepare.data = self.c_reference

        if not default:
            code = lib.uv_loop_init(self.uv_loop)
            if code != error.StatusCodes.SUCCESS:
                self.closed = True
                raise error.UVError(code)

        self._init_internal_async()
        self._init_internal_prepare()

        _loops.add(self)

    def _init_internal_async(self):
        """
        Initialize the internal async handle.
        """
        lib.uv_async_init(self.uv_loop, self.internal_uv_async, base_async_cb)
        lib.uv_unref(ffi.cast('uv_handle_t*', self.internal_uv_async))

    def _close_internal_async(self):
        """
        Close the internal async handle.
        """
        uv_handle = ffi.cast('uv_handle_t*', self.internal_uv_async)
        if not lib.uv_is_closing(uv_handle):
            lib.uv_close(uv_handle, ffi.NULL)

    def _init_internal_prepare(self):
        """
        Initialize the internal prepare handle.
        """
        lib.uv_prepare_init(self.uv_loop, self.internal_uv_prepare)
        lib.uv_prepare_start(self.internal_uv_prepare, base_prepare_cb)
        lib.uv_unref(ffi.cast('uv_handle_t*', self.internal_uv_prepare))

    def _close_internal_prepare(self):
        """
        Close the internal prepare handle.
        """
        uv_handle = ffi.cast('uv_handle_t*', self.internal_uv_prepare)
        if not lib.uv_is_closing(uv_handle):
            lib.uv_close(uv_handle, ffi.NULL)

    def _destroy(self, _):
        """
        This method is invoked by the garbage collection after the user
        loop has been garbage collected.
        """
        if not self.closed:
            for handle in self.handles:
                handle.close()
            for request in self.requests:
                request.cancel()
            self.handles_to_close.clear()
            self.requests_to_cancel.clear()
            lib.uv_walk(self.uv_loop, base_walk_close_cb, ffi.NULL)
            self.run()
            self.close()

    def reference_internal_async(self):
        """
        Reference the internal async handle used for wakeup.
        """
        lib.uv_ref(ffi.cast('uv_handle_t*', self.internal_uv_async))

    def dereference_internal_async(self):
        """
        Dereference the internal async handle used for wakeup.
        """
        lib.uv_unref(ffi.cast('uv_handle_t*', self.internal_uv_async))

    @property
    def user_loop(self):
        """
        :rtype:
            uv.Loop | None
        """
        return self.weak_user_loop()

    def attach_handle(self, base_handle):
        """
        :type base_handle:
            Handle
        """
        self.handles.add(base_handle)

    def attach_request(self, base_request):
        """
        :type base_request:
            Request
        """
        self.requests.add(base_request)

    def detach_handle(self, base_handle):
        """
        :type base_handle:
            Handle
        """
        self.handles.remove(base_handle)
        try:
            self.handles_to_close.remove(base_handle)
        except KeyError:
            pass

    def detach_request(self, base_request):
        """
        :type base_request:
            Request
        """
        self.requests.remove(base_request)
        try:
            self.requests_to_cancel.remove(base_request)
        except KeyError:
            pass

    def wakeup(self):
        """
        Wakeup the event loop from polling. This method is thread-safe.
        """
        lib.uv_async_send(self.internal_uv_async)

    def run(self, mode=lib.UV_RUN_DEFAULT):
        """
        :type mode:
            int
        """
        return bool(lib.uv_run(self.uv_loop, mode))

    def close(self):
        """
        Close the loop together with all garbage collected handles.
        """
        alive_handles = self.handles.difference(self.handles_to_close)
        alive_requests = self.requests.difference(self.requests_to_cancel)
        if alive_handles or alive_requests:
            return error.StatusCodes.EBUSY
        if self.closed:
            return error.StatusCodes.SUCCESS

        self._close_internal_async()
        self._close_internal_prepare()
        for handle in self.handles_to_close:
            handle.close()
        for request in self.requests_to_cancel:
            request.cancel()
        lib.uv_walk(self.uv_loop, base_walk_close_cb, ffi.NULL)
        self.run()

        code = lib.uv_loop_close(self.uv_loop)
        if code != error.StatusCodes.SUCCESS:
            self._init_internal_async()
            self._init_internal_prepare()
        else:
            _loops.remove(self)
            self.closed = True
        return code

    def on_prepare(self):
        """
        Internal prepare handle callback.
        """
        try:
            while True:
                base_handle = self.handles_to_close.pop()
                """ :type: BaseHandle """
                base_handle.close()  # pragma: no cover
        except KeyError:
            pass
        try:
            while True:
                base_request = self.requests_to_cancel.pop()
                """ :type: BaseRequest """
                base_request.cancel()  # pragma: no cover
        except KeyError:
            pass

    def on_wakeup(self):
        """
        Internal async handle wakeup callback.
        """
        user_loop = self.user_loop
        """ :type: uv.Loop """
        if user_loop is not None:
            user_loop.on_wakeup()


@ffi.callback('uv_close_cb')
def uv_close_cb(uv_handle):
    base_handle = ffi.from_handle(uv_handle.data)
    """ :type: Handle """
    base_handle.set_closed()

    user_handle = base_handle.user_handle
    """ :type: uv.Handle """
    if user_handle:
        try:
            user_handle.on_closed(user_handle)
        except Exception:
            user_handle.loop.handle_exception()


class BaseHandle(object):
    """
    This class implements an internal low level handle.
    """

    __slots__ = ['c_reference', 'weak_user_handle', 'base_loop', 'uv_object',
                 'uv_handle', 'closed', 'closing']

    @staticmethod
    def detach(uv_handle):
        """
        :type uv_handle:
            ffi.CData[uv_handle_t*]
        :rtype:
            uv.Handle | None
        """
        try:
            if uv_handle.data:
                return ffi.from_handle(uv_handle.data).user_handle
        except AttributeError:
            return None

    def __init__(self, user_handle, base_loop, handle_type, handle_init, arguments):
        """
        :type user_handle:
            uv.Handle
        :type base_loop:
            Loop
        :type handle_type:
            unicode
        :type handle_init:
            callable
        :type arguments:
            tuple
        """
        self.c_reference = ffi.new_handle(self)

        self.weak_user_handle = weakref.ref(user_handle, self._destroy)
        self.base_loop = base_loop

        self.uv_object = ffi.new(handle_type)
        self.uv_object.data = self.c_reference
        self.uv_handle = ffi.cast('uv_handle_t*', self.uv_object)

        code = handle_init(self.base_loop.uv_loop, self.uv_object, *arguments)
        if code != error.StatusCodes.SUCCESS:
            self.closed = True
            self.closing = True
            raise error.UVError(code)
        else:
            self.closed = False
            self.closing = False
            self.base_loop.attach_handle(self)

    def _destroy(self, _):
        """
        This method is invoked by the garbage collection after the user
        handle has been garbage collected. The handle is not closed
        immediately because this may lead to data races.
        """
        if not self.closing:
            self.base_loop.handles_to_close.add(self)

    @property
    def user_handle(self):
        """
        :rtype:
            uv.Handle | None
        """
        return self.weak_user_handle()

    def set_closed(self):
        """
        Set the handle's state to closed. This method is called from
        within the close callback after the handle has been closed.

        Detach the low level handle from it's base loop, which removes
        the global reference and allows the garbage collection to
        collect the low level handle.
        """
        self.uv_object.data = ffi.NULL
        self.closed = True
        self.c_reference = None
        self.base_loop.detach_handle(self)

    def close(self):
        """
        Close the handle if it is not already closed or closing.
        """
        if not self.closing:
            self.closing = True
            lib.uv_close(self.uv_handle, uv_close_cb)


def handle_callback(callback_type):
    """
    Decorator for handle callbacks.

    :type callback_type:
        unicode
    """
    def decorator(callback):
        def wrapper(uv_handle, *arguments):
            user_handle = BaseHandle.detach(uv_handle)
            if user_handle:
                try:
                    callback(user_handle, *arguments)
                except:
                    user_handle.loop.handle_exception()
        return ffi.callback(callback_type, wrapper)
    return decorator


class BaseRequest(object):
    """
    This class implements an internal low level request.
    """

    __slots__ = ['c_reference', 'weak_user_request', 'base_loop', 'uv_object',
                 'uv_request', 'finished', 'canceled']

    def __init__(self, user_request, base_loop, request_type, request_init,
                 arguments, uv_handle=None):
        """
        :type user_request:
            uv.UVRequest
        :type base_loop:
            Loop
        :type request_type:
            unicode
        :type request_init:
            callable
        :type arguments:
            tuple
        """
        self.c_reference = ffi.new_handle(self)

        self.weak_user_request = weakref.ref(user_request, self._destroy)
        self.base_loop = base_loop

        self.uv_object = ffi.new(request_type)
        self.uv_object.data = self.c_reference
        self.uv_request = ffi.cast('uv_req_t*', self.uv_object)

        if uv_handle is None:
            code = request_init(base_loop.uv_loop, self.uv_object, *arguments)
        else:
            code = request_init(self.uv_object, uv_handle, *arguments)

        if code != error.StatusCodes.SUCCESS and code is not None:
            self.finished = True
            self.canceled = True
            raise error.UVError(code)
        else:
            self.finished = False
            self.canceled = False
            self.base_loop.attach_request(self)

    def _destroy(self, _):
        """
        This method is invoked by the garbage collection after the user
        request has been garbage collected. The request is not
        cancelled immediately because this may lead to data races.
        """
        if not self.finished and not self.canceled:
            self.base_loop.requests_to_cancel.add(self)

    @property
    def user_request(self):
        """
        :rtype:
            uv.UVRequest | None
        """
        return self.weak_user_request()

    def set_finished(self):
        """
        Set the request's state to finished. This method is called from
        within the request callback after the request has finished.

        Detach the low level request from it's base loop, which removes
        the global reference and allows the garbage collection to
        collect the low level request.
        """
        self.uv_object.data = ffi.NULL
        self.finished = True
        self.c_reference = None
        self.base_loop.detach_request(self)

    def cancel(self):
        """
        Cancel the request if it has not been canceled or has finished.
        """
        if not self.finished and not self.canceled:
            code = lib.uv_cancel(self.uv_request)
            self.canceled = code == error.StatusCodes.SUCCESS
            return code
        return error.StatusCodes.SUCCESS  # pragma: no cover


def request_callback(callback_type):
    """
    Decorator for request callbacks.

    :type callback_type:
        unicode
    """
    def decorator(callback):
        def wrapper(uv_request, *arguments):
            base_request = ffi.from_handle(uv_request.data)
            """ :type: BaseRequest """
            base_request.set_finished()
            user_request = base_request.user_request
            if user_request:
                user_request.clear_pending()
                try:
                    callback(user_request, *arguments)
                except Exception:
                    user_request.loop.handle_exception()
        return ffi.callback(callback_type, wrapper)
    return decorator


def finalize_request(user_request):
    """
    :type user_request:
        uv.UVRequest
    """
    user_request.base_request.set_finished()
    user_request.clear_pending()
