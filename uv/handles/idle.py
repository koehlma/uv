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

from ..library import ffi, lib, detach

from ..common import dummy_callback
from ..error import UVError, HandleClosedError
from ..handle import HandleType, Handle

__all__ = ['Idle']


@ffi.callback('uv_idle_cb')
def uv_idle_cb(uv_idle):
    idle = detach(uv_idle)
    with idle.loop.callback_context:
        idle.on_idle(idle)


@HandleType.IDLE
class Idle(Handle):
    """
    Idle handles will run the given callback once per loop
    iteration, right before the :class:`uv.Prepare` handles.

    The notable difference with prepare handles is, that when
    there are active idle handles, the loop will perform a zero
    timeout poll instead of blocking for IO.

    .. warning:

        Despite the name, idle handles will get their callback called on
        every loop iteration, not when the loop is actually "idle".

    :raises uv.UVError: error during the initialization of the handle

    :param loop: event loop which should be used for the handle
    :param on_idle: callback which should be called before prepare handles

    :type loop: uv.Loop
    :type on_idle: (uv.Idle) -> None
    """

    __slots__ = ['uv_idle', 'on_idle']

    def __init__(self, loop=None, on_idle=None):
        self.uv_idle = ffi.new('uv_idle_t*')
        super(Idle, self).__init__(self.uv_idle, loop)
        self.on_idle = on_idle or dummy_callback
        """
        Callback which should be called before prepare handles.

        .. function:: on_idle(Idle-Handle)

        :readonly: False
        :type: (uv.Idle) -> None
        """
        code = lib.uv_idle_init(self.loop.uv_loop, self.uv_idle)
        if code < 0:
            self.destroy()
            raise UVError(code)

    def start(self, on_idle=None):
        """
        Starts the handle.

        :raises uv.UVError: error while starting the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param on_idle: callback which should be called before prepare handles
        :type on_idle: (uv.Idle) -> None
        """
        if self.closing: raise HandleClosedError()
        self.on_idle = on_idle or self.on_idle
        code = lib.uv_idle_start(self.uv_idle, uv_idle_cb)
        if code < 0: raise UVError(code)

    def stop(self):
        """
        Stops the handle, the callback will no longer be called.

        :raises uv.UVError: error while stopping the handle
        """
        if self.closing: return
        code = lib.uv_idle_stop(self.uv_idle)
        if code < 0: raise UVError(code)

    def destroy(self):
        self.uv_idle = None
        super(Idle, self).destroy()

    __call__ = start
