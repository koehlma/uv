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

from __future__ import print_function, unicode_literals, division

from .library import ffi, lib, detach, dummy_callback

from .error import UVError
from .handle import HandleType, Handle


@ffi.callback('uv_timer_cb')
def uv_timer_cb(uv_timer):
    timer = detach(uv_timer)
    with timer.loop.callback_context:
        timer.on_timeout(timer)


@HandleType.TIMER
class Timer(Handle):
    __slots__ = ['uv_timer', 'on_timeout']

    def __init__(self, loop=None, on_timeout=None):
        self.uv_timer = ffi.new('uv_timer_t*')
        self.on_timeout = on_timeout or dummy_callback
        super(Timer, self).__init__(self.uv_timer, loop)
        code = lib.uv_timer_init(self.loop.uv_loop, self.uv_timer)
        if code < 0: raise UVError(code)

    @property
    def repeat(self):
        return lib.uv_timer_get_repeat(self.uv_timer)

    @repeat.setter
    def repeat(self, repeat):
        lib.uv_timer_set_repeat(self.uv_timer, repeat)

    def start(self, timeout, callback=None, repeat=0):
        if callback is not None: self.on_timeout = callback
        lib.uv_timer_start(self.uv_timer, uv_timer_cb, timeout, repeat)

    def stop(self):
        lib.uv_timer_stop(self.uv_timer)

    def again(self):
        code = lib.uv_timer_again(self.uv_timer)
        if code < 0: raise UVError(code)
