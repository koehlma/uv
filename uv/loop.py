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
import sys
import threading
import traceback

from .library import ffi, lib, attach_loop

from .error import UVError, LoopClosedError


__all__ = ['RunMode', 'Loop']


class RunMode(enum.IntEnum):
    DEFAULT = lib.UV_RUN_DEFAULT
    ONCE = lib.UV_RUN_ONCE
    NOWAIT = lib.UV_RUN_NOWAIT


class CallbackContext(object):
    """
    Default callback context manager.
    """
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            print('Exception happened during callback execution!', file=sys.stderr)
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        return True


class Loop:
    _global_lock = threading.Lock()
    _thread_locals = threading.local()
    _default = None
    _loops = set()

    @classmethod
    def get_default(cls, instantiate=True, **arguments):
        """
        :param instantiate:
        :type instantiate: bool
        :return: global default loop
        :rtype: Loop
        """
        with cls._global_lock:
            if cls._default is None and instantiate:
                Loop._default = Loop(default=True, **arguments)
            return Loop._default

    @classmethod
    def get_current(cls, instantiate=True, **arguments):
        """
        :param instantiate:
        :type instantiate: bool
        :return: current threads default loop
        :rtype: Loop
        """
        loop = getattr(cls._thread_locals, 'loop', None)
        if loop is None and instantiate: return cls(**arguments)
        return loop

    @classmethod
    def get_loops(cls):
        """
        :return:
        :rtype: frozenset[Loop]
        """
        with cls._global_lock: return frozenset(cls._loops)

    def __init__(self, buffer_size=2**16, allocate=None, release=None, default=False):
        if default:
            assert Loop._default is None
            self.uv_loop = lib.uv_default_loop()
            if not self.uv_loop: raise RuntimeError('error initializing default loop')
        else:
            self.uv_loop = ffi.new('uv_loop_t*')
            code = lib.uv_loop_init(self.uv_loop)
            if code < 0: raise UVError(code)

        self.attachment = attach_loop(self.uv_loop, self)

        if allocate is None or release is None:
            self.c_data_buffer = ffi.new('char[%d]' % buffer_size)
            self.attachment.data.buffer.length = buffer_size
            self.attachment.data.buffer.base = self.c_data_buffer
            self.allocate = lib.py_get_allocator()
            self.release = lib.py_release
        else:
            self.allocate = ffi.callback(allocate)
            self.release = ffi.callback(release)

        self.callback_context = CallbackContext()
        """
        Context manager in which callbacks are executed, if you want to
        change the default behaviour what happens after an exception
        occoured during a callback overwrite this.

        :readonly: False
        :type: CallbackContext
        """
        self.handles = set()
        """
        Contains all handles running on this loop which have not already
        been closed. We have to keep references to every single handle in
        this set because otherwise they are garbage collected before they
        have been closed which leads to segmentation faults.

        :readonly: True
        :type: set[Handle]
        """
        self.closed = False
        """
        Loop has been closed. This is `True` right after close has been
        called. It means all internal resources are freed and this loop
        is ready to be garbage collected. Operations on a closed loop
        will raise :class:`uv.LoopClosedError`.

        :readonly: True
        :type: bool
        """
        with Loop._global_lock: Loop._loops.add(self)
        self.make_current()

    @property
    def alive(self):
        if self.closed: return False
        return bool(lib.uv_loop_alive(self.uv_loop))

    @property
    def now(self):
        if self.closed: raise LoopClosedError()
        return lib.uv_now(self.uv_loop)

    def fileno(self):
        if self.closed: raise LoopClosedError()
        return lib.uv_backend_fd(self.uv_loop)

    def make_current(self):
        Loop._thread_locals.loop = self

    def update_time(self):
        if self.closed: raise LoopClosedError()
        return lib.uv_update_time(self.uv_loop)

    def get_timeout(self):
        if self.closed: raise LoopClosedError()
        return lib.uv_backend_timeout(self.uv_loop)

    def run(self, mode=RunMode.DEFAULT):
        if self.closed: raise LoopClosedError()
        Loop._thread_locals.loop = self
        result = bool(lib.uv_run(self.uv_loop, mode))
        return result

    def stop(self):
        if self.closed: raise LoopClosedError()
        if self.closed: return
        lib.uv_stop(self.uv_loop)

    def close(self):
        if self.closed: return
        code = lib.uv_loop_close(self.uv_loop)
        if code < 0: raise UVError(code)
        self.uv_loop = None
        self.closed = True
        with Loop._global_lock: Loop._loops.remove(self)
