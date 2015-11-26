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

from .library import ffi, lib, detach, dummy_callback

from .error import UVError
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
    __slots__ = ['uv_async', 'callback']

    def __init__(self, loop: Loop=None, callback: callable=None):
        self.uv_async = ffi.new('uv_async_t*')
        super().__init__(self.uv_async, loop)
        self.callback = callback or dummy_callback
        code = lib.uv_async_init(self.loop.uv_loop, self.uv_async, uv_async_cb)
        if code < 0: raise UVError(code)

    def send(self, callback: callable=None):
        self.callback = callback or self.callback
        code = lib.uv_async_send(self.uv_async)
        if code < 0: raise UVError(code)

    __call__ = send
