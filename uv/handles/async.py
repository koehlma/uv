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

from __future__ import absolute_import, division, print_function, unicode_literals

from .. import common, error, handle, library
from ..library import ffi, lib

__all__ = ['Async']


@ffi.callback('uv_async_cb')
def uv_async_cb(uv_async):
    async = library.detach(uv_async)
    """ :type: uv.Async """
    try:
        async.on_wakeup(async)
    except:
        async.loop.handle_exception()


@handle.HandleType.ASYNC
class Async(handle.Handle):
    """
    Async handles are able to wakeup the event loop of another thread
    and run the given callback in the event loop's thread. They are the
    only thread-safe handles. Operations on other handles can be safely
    executed in the `on_wakeup` callback.
    """

    __slots__ = ['uv_async', 'on_wakeup']

    def __init__(self, loop=None, on_wakeup=None):
        """
        :raises uv.UVError:
            error while initializing the handle

        :param loop:
            event loop the handle should run on
        :param on_wakeup:
            callback which should run in the event loop's thread after
            the event loop has been woken up

        :type loop:
            uv.Loop
        :type on_wakeup:
            ((uv.Async) -> None) | ((Any, uv.Async) -> None)
        """
        self.uv_async = ffi.new('uv_async_t*')
        super(Async, self).__init__(self.uv_async, loop)
        self.on_wakeup = on_wakeup or common.dummy_callback
        """
        Callback which should run in the event loop's thread after the
        event loop has been woken up.


        .. function:: on_wakeup(async)

            :param async:
                handle the call originates from

            :type async:
                uv.Async


        :readonly:
            False
        :type:
            ((uv.Async) -> None) | ((Any, uv.Async) -> None)
        """
        code = lib.uv_async_init(self.loop.uv_loop, self.uv_async, uv_async_cb)
        if code < 0:
            self.destroy()
            raise error.UVError(code)

    def send(self, on_wakeup=None):
        """
        Wakeup the event loop and run the callback afterwards. Multiple
        calls to this method are coalesced if they happen before the
        callback has been called. This means not every call will yield
        an execution of the callback.

        :raises uv.UVError:
            error while trying to wakeup the event loop
        :raises uv.HandleClosedError:
            handle has already been closed or is closing

        :param on_wakeup:
            callback which should run in the event loop's thread after
            the event loop has been woken up (overrides the current
            callback if specified)

        :type on_wakeup:
            ((uv.Async) -> None) | ((Any, uv.Async) -> None)
        """
        if self.closing:
            raise error.HandleClosedError()
        self.on_wakeup = on_wakeup or self.on_wakeup
        code = lib.uv_async_send(self.uv_async)
        if code < 0:
            raise error.UVError(code)

    __call__ = send
