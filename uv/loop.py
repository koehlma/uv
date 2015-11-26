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
import threading
import traceback

from .library import ffi, lib, detach, attach_loop

from .error import UVError


__all__ = ['loops', 'RunMode', 'Loop']

loops = set()


class RunMode(enum.IntEnum):
    DEFAULT = lib.UV_RUN_DEFAULT
    ONCE = lib.UV_RUN_ONCE
    NOWAIT = lib.UV_RUN_NOWAIT


@ffi.callback('uv_walk_cb')
def uv_walk_cb(uv_handle, handles):
    handle = detach(uv_handle)
    if handle: ffi.from_handle(handles).append(handle)


class CallbackContext:
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            print('Exception happened during callback execution!')
            traceback.print_exception(exc_type, exc_val, exc_tb)
            return True


class Loop:
    _default_loop = None
    _current_loops = threading.local()

    @classmethod
    def default_loop(cls):
        """
        :rtype: Loop
        """
        if cls._default_loop is None:
            cls._default_loop = cls(default=True)
        return cls._default_loop

    @classmethod
    def current_loop(cls):
        """
        :rtype: Loop
        """
        try:
            loop = cls._current_loops.loop
        except AttributeError:
            loop = cls.default_loop()
        return loop

    def __init__(self, buffer_size: int=2**16, allocate: callable=None,
                 release: callable=None, default: bool=False):
        if default:
            assert self._default_loop is None
            self.uv_loop = lib.uv_default_loop()
            if not self.uv_loop: raise RuntimeError('error initializing default loop')
        else:
            self.uv_loop = ffi.new('uv_loop_t*')
            code = lib.uv_loop_init(self.uv_loop)
            if code < 0: raise UVError(code)

        self.attachment = attach_loop(self.uv_loop, self)

        if allocate is None or release is None:
            self.attachment.data.buffer.length = buffer_size
            self.attachment.data.buffer.base = ffi.new('char[%d]' % buffer_size)
            self.allocate = lib.py_get_allocator()
            self.release = lib.py_release
        else:
            self.allocate = ffi.callback(allocate)
            self.release = ffi.callback(release)

        self.callback_context = CallbackContext()

        loops.add(self)

    @property
    def alive(self):
        return bool(lib.uv_loop_alive(self.uv_loop))

    @property
    def now(self):
        return lib.uv_now(self.uv_loop)

    @property
    def handles(self):
        handles = []
        lib.uv_walk(self.uv_loop, uv_walk_cb, ffi.new_handle(handles))
        return handles

    def fileno(self):
        return lib.uv_backend_fd(self.uv_loop)

    def update_time(self):
        return lib.uv_update_time(self.uv_loop)

    def get_timeout(self):
        return lib.uv_backend_timeout(self.uv_loop)

    def run(self, mode: RunMode=RunMode.DEFAULT):
        Loop._current_loops.loop = self
        result = bool(lib.uv_run(self.uv_loop, mode))
        Loop._current_loops.loop = None
        return result

    def stop(self):
        lib.uv_stop(self.uv_loop)

    def close(self):
        code = lib.uv_loop_close(self.uv_loop)
        if code < 0: raise UVError(code)
        loops.remove(self)






