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

from .error import UVError
from .fs import unpack_stat
from .handle import HandleType, Handle
from .library import ffi, lib, detach, dummy_callback
from .loop import Loop

__all__ = ['FSPoll']


@ffi.callback('uv_fs_poll_cb')
def uv_fs_poll_cb(uv_fs_poll, status, uv_previous_stat, uv_current_stat):
    previous_stat = unpack_stat(uv_previous_stat) if uv_previous_stat else None
    current_stat = unpack_stat(uv_current_stat) if uv_current_stat else None
    fs_poll = detach(uv_fs_poll)
    fs_poll.callback(fs_poll, status, previous_stat, current_stat)


@HandleType.FS_POLL
class FSPoll(Handle):
    __slots__ = ['fs_poll', 'callback', 'path']

    def __init__(self, path: str=None, loop: Loop=None, callback: callable=None):
        self.fs_poll = ffi.new('uv_fs_poll_t*')
        self.callback = callback or dummy_callback
        self.path = path
        super().__init__(self.fs_poll, loop)
        code = lib.uv_fs_poll_init(self.loop.uv_loop, self.fs_poll)
        if code < 0: raise UVError(code)

    def start(self, path: str=None, interval: int=5000, callback: callable=None):
        self.path = path or self.path
        self.callback = callback or self.callback
        uv_path = self.path.encode()
        code = lib.uv_fs_poll_start(self.fs_poll, uv_fs_poll_cb, uv_path, interval)
        if code < 0: raise UVError(code)

    def stop(self):
        code = lib.uv_fs_poll_stop(self.fs_poll)
        if code < 0: raise UVError(code)

    __call__ = start
