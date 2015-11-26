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

from .library import ffi, lib, attach, detach, dummy_callback, is_linux

from .error import UVError
from .loop import Loop

__all__ = ['close_all_handles', 'Handle']

handles = set()


def close_all_handles(callback: callable=None):
    for handle in handles: handle.close(callback)


class HandleType(enum.IntEnum):
    UNKNOWN = lib.UV_UNKNOWN_HANDLE
    HANDLE = lib.UV_HANDLE
    ASYNC = lib.UV_ASYNC
    CHECK = lib.UV_CHECK
    FILE = lib.UV_FILE
    IDLE = lib.UV_IDLE
    PIPE = lib.UV_NAMED_PIPE
    POLL = lib.UV_POLL
    PREPARE = lib.UV_PREPARE
    PROCESS = lib.UV_PROCESS
    SIGNAL = lib.UV_SIGNAL
    STREAM = lib.UV_STREAM
    TCP = lib.UV_TCP
    TIMER = lib.UV_TIMER
    TTY = lib.UV_TTY
    UDP = lib.UV_UDP

    FS_EVENT = lib.UV_FS_EVENT
    FS_POLL = lib.UV_FS_POLL

    def __call__(self, cls):
        self.cls = cls
        return cls


@ffi.callback('uv_close_cb')
def uv_close_cb(uv_handle):
    handle = detach(uv_handle)
    handles.remove(handle)
    handle.on_closed(handle)


@HandleType.UNKNOWN
@HandleType.HANDLE
class Handle:
    __slots__ = ['uv_handle', 'c_attachment', 'loop', 'on_closed']

    def __init__(self, uv_handle, loop: Loop=None):
        self.uv_handle = ffi.cast('uv_handle_t*', uv_handle)
        self.c_attachment = attach(self.uv_handle, self)
        self.on_closed = dummy_callback
        self.loop = loop or Loop.current_loop()
        handles.add(self)

    @property
    def active(self) -> bool:
        return bool(lib.uv_is_active(self.uv_handle))

    @property
    def closed(self) -> bool:
        return bool(lib.uv_is_closing(self.uv_handle))

    @property
    def referenced(self) -> bool:
        return bool(lib.uv_has_ref(self.uv_handle))

    @property
    def send_buffer_size(self) -> int:
        c_buffer_size = ffi.new('int*')
        code = lib.uv_send_buffer_size(self.uv_handle, c_buffer_size)
        if code < 0: raise UVError(code)
        return c_buffer_size[0]

    @send_buffer_size.setter
    def send_buffer_size(self, value: int):
        c_buffer_size = ffi.new('int*', int(value / 2) if is_linux else value)
        code = lib.uv_send_buffer_size(self.uv_handle, c_buffer_size)
        if code < 0: raise UVError(code)

    @property
    def receive_buffer_size(self) -> int:
        c_buffer_size = ffi.new('int*')
        code = lib.uv_recv_buffer_size(self.uv_handle, c_buffer_size)
        if code < 0: raise UVError(code)
        return c_buffer_size[0]

    @receive_buffer_size.setter
    def receive_buffer_size(self, value: int):
        c_buffer_size = ffi.new('int*', int(value / 2) if is_linux else value)
        code = lib.uv_recv_buffer_size(self.uv_handle, c_buffer_size)
        if code < 0: raise UVError(code)

    def fileno(self) -> int:
        uv_fd = ffi.new('uv_os_fd_t*')
        lib.uv_fileno(self.uv_handle, uv_fd)
        return ffi.cast('int*', uv_fd)[0]

    def reference(self):
        lib.uv_ref(self.uv_handle)

    def dereference(self):
        lib.uv_unref(self.uv_handle)

    def close(self, callback: callable=None):
        self.on_closed = callback or self.on_closed
        lib.uv_close(self.uv_handle, uv_close_cb)
