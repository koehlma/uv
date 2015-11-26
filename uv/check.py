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

__all__ = ['Check']


@ffi.callback('uv_check_cb')
def uv_check_cb(uv_check):
    check = detach(uv_check)
    with check.loop.callback_context:
        check.callback(check)


@HandleType.CHECK
class Check(Handle):
    __slots__ = ['uv_check', 'callback']

    def __init__(self, loop: Loop=None, callback: callable=None):
        self.uv_check = ffi.new('uv_check_t*')
        super().__init__(self.uv_check, loop)
        self.callback = callback or dummy_callback
        code = lib.uv_check_init(self.loop.uv_loop, self.uv_check)
        if code < 0: raise UVError(code)

    def start(self, callback: callable=None):
        self.callback = callback or self.callback
        code = lib.uv_check_start(self.uv_check, uv_check_cb)
        if code < 0: raise UVError(code)

    def stop(self):
        code = lib.uv_check_stop(self.uv_check)
        if code < 0: raise UVError(code)

    __call__ = start
