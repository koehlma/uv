# -*- coding: utf-8 -*-

# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function, unicode_literals

from .. import common, error, handle, library
from ..library import ffi, lib

__all__ = ['Idle']


@ffi.callback('uv_idle_cb')
def uv_idle_cb(uv_idle):
    idle = library.detach(uv_idle)
    with idle.loop.callback_context:
        idle.on_idle(idle)


@handle.HandleType.IDLE
class Idle(handle.Handle):
    """
    Idle handles will run the given callback once per loop iteration,
    right before the :class:`uv.Prepare` handles.

    The notable difference with prepare handles is, that when there
    are active idle handles, the loop will perform a zero timeout poll
    instead of blocking for IO.

    .. warning:

        Despite the name, idle handles will get their callback called on
        every loop iteration, not when the loop is actually "idle".

    :raises uv.UVError: error while initializing the handle

    :param loop: event loop the handle should run on
    :param on_idle: callback called before prepare handles

    :type loop: uv.Loop
    :type on_idle: ((uv.Idle) -> None) | ((Any, uv.Idle) -> None)
    """

    __slots__ = ['uv_idle', 'on_idle']

    def __init__(self, loop=None, on_idle=None):
        self.uv_idle = ffi.new('uv_idle_t*')
        super(Idle, self).__init__(self.uv_idle, loop)
        self.on_idle = on_idle or common.dummy_callback
        """
        Callback called before prepare handles.

        .. function:: on_idle(Idle)

        :readonly: False
        :type: ((uv.Idle) -> None) | ((Any, uv.Idle) -> None)
        """
        code = lib.uv_idle_init(self.loop.uv_loop, self.uv_idle)
        if code < 0:
            self.destroy()
            raise error.UVError(code)

    def start(self, on_idle=None):
        """
        Starts the handle.

        :raises uv.UVError: error while starting the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param on_idle: callback called before prepare handles
        :type on_idle: ((uv.Idle) -> None) | ((Any, uv.Idle) -> None)
        """
        if self.closing: raise error.HandleClosedError()
        self.on_idle = on_idle or self.on_idle
        code = lib.uv_idle_start(self.uv_idle, uv_idle_cb)
        if code < 0: raise error.UVError(code)

    def stop(self):
        """
        Stops the handle, the callback will no longer be called.

        :raises uv.UVError: error while stopping the handle
        """
        if self.closing: return
        code = lib.uv_idle_stop(self.uv_idle)
        if code < 0: raise error.UVError(code)

    __call__ = start
