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

__all__ = ['EventFlags', 'Event', 'FSEvent']


class EventFlags(enum.IntEnum):
    WATCH_ENTRY = lib.UV_FS_EVENT_WATCH_ENTRY
    STAT = lib.UV_FS_EVENT_STAT
    RECURSIVE = lib.UV_FS_EVENT_RECURSIVE


class Event(enum.IntEnum):
    RENAME = lib.UV_RENAME
    CHANGE = lib.UV_CHANGE


@ffi.callback('uv_fs_event_cb')
def uv_fs_event_cb(uv_fs_event, uv_filename, events, status):
    fs_event = detach(uv_fs_event)
    uv_filename = ffi.string(uv_filename).decode()
    with fs_event.loop.callback_context:
        fs_event.callback(fs_event, uv_filename, events, status)


@HandleType.FS_EVENT
class FSEvent(Handle):
    __slots__ = ['fs_event', 'callback', 'path']

    def __init__(self, loop: Loop=None, path: str=None, callback: callable=None):
        self.fs_event = ffi.new('uv_fs_event_t*')
        self.callback = callback or dummy_callback
        self.path = path
        super().__init__(self.fs_event, loop)
        code = lib.uv_fs_event_init(self.loop.uv_loop, self.fs_event)
        if code < 0: raise UVError(code)

    def start(self, path: str=None, callback: callable=None, flags: int=0):
        self.path = path or self.path
        self.callback = callback or self.callback
        uv_path = self.path.encode()
        code = lib.uv_fs_event_start(self.fs_event, uv_fs_event_cb, uv_path, flags)
        if code < 0: raise UVError(code)

    def stop(self):
        code = lib.uv_fs_event_stop(self.fs_event)
        if code < 0: raise UVError(code)

    __call__ = start
