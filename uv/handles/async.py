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

from __future__ import absolute_import, division, print_function, unicode_literals

from .. import base, common, error, handle
from ..library import lib


@base.handle_callback('uv_async_cb')
def uv_async_cb(async_handle):
    """
    :type async_handle:
        uv.Async
    """
    async_handle.clear_pending()
    async_handle.on_wakeup(async_handle)


@handle.HandleTypes.ASYNC
class Async(handle.UVHandle):
    """
    Async handles are able to wakeup the event loop of another thread
    and run the given callback in the event loop's thread. Although the
    :func:`uv.Async.send` method is thread-safe the constructor is not.

    To run a callback in the event loop's thread without creating an
    :class:`uv.Async` handle use :func:`uv.Loop.call_later`.

    :raises uv.UVError:
        error while initializing the handle

    :param loop:
        event loop the handle should run on
    :param on_wakeup:
        callback which should run in the event loop's thread after the
        event loop has been woken up

    :type loop:
        uv.Loop
    :type on_wakeup:
        ((uv.Async) -> None) | ((Any, uv.Async) -> None)
    """

    __slots__ = ['uv_async', 'on_wakeup']

    uv_handle_type = 'uv_async_t*'
    uv_handle_init = lib.uv_async_init

    def __init__(self, loop=None, on_wakeup=None):
        super(Async, self).__init__(loop, (uv_async_cb, ))
        self.uv_async = self.base_handle.uv_object
        self.on_wakeup = on_wakeup or common.dummy_callback
        """
        Callback which should run in the event loop's thread after the
        event loop has been woken up.


        .. function:: on_wakeup(async_handle)

            :param async_handle:
                handle the call originates from

            :type async_handle:
                uv.Async


        :readonly:
            False
        :type:
            ((uv.Async) -> None) | ((Any, uv.Async) -> None)
        """

    def send(self, on_wakeup=None):
        """
        Wakeup the event loop and run the callback afterwards. Multiple
        calls to this method are coalesced if they happen before the
        callback has been called. This means not every call will yield
        an execution of the callback. It is safe to call this method
        form outside the event loop's thread.

        :raises uv.UVError:
            error while trying to wakeup the event loop
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param on_wakeup:
            callback which should run in the event loop's thread after
            the event loop has been woken up (overrides the current
            callback if specified)

        :type on_wakeup:
            ((uv.Async) -> None) | ((Any, uv.Async) -> None)
        """
        if self.closing:
            raise error.ClosedHandleError()
        self.on_wakeup = on_wakeup or self.on_wakeup
        code = lib.uv_async_send(self.uv_async)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.set_pending()

    __call__ = send
