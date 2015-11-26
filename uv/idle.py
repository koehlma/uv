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

__all__ = ['Idle']


@ffi.callback('uv_idle_cb')
def uv_idle_cb(uv_idle):
    idle = detach(uv_idle)
    idle.callback(idle)


@HandleType.IDLE
class Idle(Handle):
    __slots__ = ['uv_idle', 'callback']

    def __init__(self, loop: Loop=None, callback: callable=None):
        self.uv_idle = ffi.new('uv_idle_t*')
        self.callback = callback or dummy_callback
        super().__init__(self.uv_idle, loop)
        code = lib.uv_idle_init(self.loop.uv_loop, self.uv_idle)
        if code < 0: raise UVError(code)

    def start(self, callback: callable=None):
        self.callback = callback or self.callback
        code = lib.uv_idle_start(self.uv_idle, uv_idle_cb)
        if code < 0: raise UVError(code)

    def stop(self):
        code = lib.uv_idle_stop(self.uv_idle)
        if code < 0: raise UVError(code)

    __call__ = start
