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

import enum

from .library import ffi, lib, detach, dummy_callback

from .error import UVError
from .handle import HandleType, Handle
from .loop import Loop

__all__ = ['Signals', 'Signal']


class Signals(enum.IntEnum):
    SIGINT = 2
    SIGBREAK = 21
    SIGHUP = 1
    SIGWINCH = 28


@ffi.callback('uv_signal_cb')
def uv_signal_cb(uv_signal, signum):
    signal = detach(uv_signal)
    signal.on_signal(signal, signum)


@HandleType.SIGNAL
class Signal(Handle):
    __slots__ = ['uv_signal', 'on_signal']

    def __init__(self, loop: Loop=None, on_signal: callable=None):
        self.uv_signal = ffi.new('uv_signal_t*')
        self.on_signal = on_signal or dummy_callback
        super().__init__(self.uv_signal, loop)
        code = lib.uv_signal_init(self.loop.uv_loop, self.uv_signal)
        if code < 0: raise UVError(code)

    @property
    def signum(self):
        return self.uv_signal.signum

    def start(self, signum: int, callback: callable=None):
        self.on_signal = callback or self.on_signal
        code = lib.uv_signal_start(self.uv_signal, uv_signal_cb, signum)
        if code < 0: raise UVError(code)

    def stop(self):
        code = lib.uv_signal_stop(self.uv_signal)
        if code < 0: raise UVError(code)
