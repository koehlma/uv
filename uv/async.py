# -*- coding: utf-8 -*-
#
# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals, division

from .library import ffi, lib, detach, dummy_callback

from .error import UVError, ClosedStructure
from .handle import HandleType, Handle
from .loop import Loop

__all__ = ['Async']


@ffi.callback('uv_async_cb')
def uv_async_cb(uv_async):
    async = detach(uv_async)
    with async.loop.callback_context:
        async.callback(async)


@HandleType.ASYNC
class Async(Handle):
    """
    :param loop: event loop which should be used for the handle
    :param callback: callback which should be called from within the event loop
    :type loop: Loop
    :type callback: (uv.Async) -> None
    """

    __slots__ = ['uv_async', 'callback']

    def __init__(self, loop=None, callback=None):
        self.uv_async = ffi.new('uv_async_t*')
        super(Async, self).__init__(self.uv_async, loop)
        self.callback = callback or dummy_callback
        code = lib.uv_async_init(self.loop.uv_loop, self.uv_async, uv_async_cb)
        if code < 0: raise UVError(code)

    def send(self, callback=None):
        """
        :param callback: callback which should be called from within the event loop
        :type callback: (uv.Async) -> None
        """
        if self.closed: raise ClosedStructure()
        self.callback = callback or self.callback
        code = lib.uv_async_send(self.uv_async)
        if code < 0: raise UVError(code)

    def destroy(self):
        self.uv_async = None
        super(Async, self).destroy()

    __call__ = send
