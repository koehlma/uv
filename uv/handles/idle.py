# -*- coding: utf-8 -*-

# Copyright (C) 2016, Maximilian Köhl <mail@koehlma.de>
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

from .. import base, common, error, handle
from ..library import lib


@base.handle_callback('uv_idle_cb')
def uv_idle_cb(idle_handle):
    """
    :type idle_handle:
        uv.Idle
    """
    idle_handle.on_idle(idle_handle)


@handle.HandleTypes.IDLE
class Idle(handle.UVHandle):
    """
    Idle handles will run the given callback once per loop iteration,
    right before the :class:`uv.Prepare` handles.

    The notable difference with prepare handles is, that when there
    are active idle handles, the loop will perform a zero timeout poll
    instead of blocking for IO.

    .. warning:
        Despite the name, idle handles will get their callback called on
        every loop iteration, not when the loop is actually "idle".

    :raises uv.UVError:
        error while initializing the handle

    :param loop:
        event loop the handle should run on
    :param on_idle:
        callback which should run right before the prepare handles
        after the handle has been started

    :type loop:
        uv.Loop
    :type on_idle:
        ((uv.Idle) -> None) | ((Any, uv.Idle) -> None)
    """

    __slots__ = ['uv_idle', 'on_idle']

    uv_handle_type = 'uv_idle_t*'
    uv_handle_init = lib.uv_idle_init

    def __init__(self, loop=None, on_idle=None):
        super(Idle, self).__init__(loop)
        self.uv_idle = self.base_handle.uv_object
        self.on_idle = on_idle or common.dummy_callback
        """
        Callback which should run right before the prepare handles
        after the handle has been started.


        .. function:: on_idle(idle)

            :param idle:
                handle the call originates from

            :type idle:
                uv.Idle


        :readonly:
            False
        :type:
            ((uv.Idle) -> None) | ((Any, uv.Idle) -> None)
        """

    def start(self, on_idle=None):
        """
        Start the handle. The callback will run once per loop iteration
        right before the prepare handles from now on.

        :raises uv.UVError:
            error while starting the handle
        :raises uv.HandleClosedError:
            handle has already been closed or is closing

        :param on_idle:
            callback which should run right before the prepare handles
            (overrides the current callback if specified)

        :type on_idle:
            ((uv.Idle) -> None) | ((Any, uv.Idle) -> None)
        """
        if self.closing:
            raise error.ClosedHandleError()
        self.on_idle = on_idle or self.on_idle
        code = lib.uv_idle_start(self.uv_idle, uv_idle_cb)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.set_pending()

    def stop(self):
        """
        Stop the handle. The callback will no longer be called.

        :raises uv.UVError:
            error while stopping the handle
        """
        if self.closing:
            return
        code = lib.uv_idle_stop(self.uv_idle)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.clear_pending()

    __call__ = start
