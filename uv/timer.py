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

from .library import ffi, lib, detach, dummy_callback

from .error import UVError, HandleClosedError
from .handle import HandleType, Handle

__all__ = ['Timer']


@ffi.callback('uv_timer_cb')
def uv_timer_cb(uv_timer):
    timer = detach(uv_timer)
    with timer.loop.callback_context:
        timer.callback(timer)


@HandleType.TIMER
class Timer(Handle):
    """
    Timer handles are used to schedule callbacks to be called in the future.

    :raises uv.UVError: error during the initialization of the handle

    :param loop: event loop which should be used for the handle
    :param callback: callback which should be called on timeout

    :type loop: Loop
    :type callback: (uv.Timer) -> None
    """

    __slots__ = ['uv_timer', 'callback']

    def __init__(self, loop=None, callback=None):
        self.uv_timer = ffi.new('uv_timer_t*')
        super(Timer, self).__init__(self.uv_timer, loop)
        self.callback = callback or dummy_callback
        """
        Callback which should be called on timeout.

        .. function:: callback(Timer-Handle)

        :readonly: False
        :type: (uv.Timer) -> None
        """
        code = lib.uv_timer_init(self.loop.uv_loop, self.uv_timer)
        if code < 0:
            self.destroy()
            raise UVError(code)

    @property
    def repeat(self):
        """
        The repeat interval value in milliseconds. The timer will be
        scheduled to run on the given interval, regardless of the
        callback execution duration, and will follow normal timer
        semantics in the case of time-slice overrun.

        For example, if a 50ms repeating timer first runs for 17ms,
        it will be scheduled to run again 33ms later. If other tasks
        consume more than the 33ms following the first timer callback,
        then the callback will run as soon as possible.

        .. note::

            If the repeat value is set from a timer callback it
            does not immediately take effect. If the timer was
            non-repeating before, it will have been stopped. If it
            was repeating, then the old repeat value will have been
            used to schedule the next timeout.

        :raises uv.HandleClosedError: handle has already been closed or is closing

        :readonly: False
        :rtype: int
        """
        if self.closing: raise HandleClosedError()
        return lib.uv_timer_get_repeat(self.uv_timer)

    @repeat.setter
    def repeat(self, repeat):
        """
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param repeat: repeat interval which should be set
        :type repeat: int
        """
        if self.closing: raise HandleClosedError()
        lib.uv_timer_set_repeat(self.uv_timer, repeat)

    def again(self):
        """
        Stop the timer, and if it is repeating restart it using the repeat
        value as the timeout. If the timer has never been started before it
        raises :class:`uv.UVError` with :class:`uv.StatusCode.EINVAL`.

        :raises uv.UVError: error while restarting the timer
        :raises uv.HandleClosedError: handle has already been closed or is closing

        """
        if self.closing: raise HandleClosedError
        code = lib.uv_timer_again(self.uv_timer)
        if code < 0: raise UVError(code)

    def start(self, timeout, callback=None, repeat=0):
        """
        Starts the timer. If `timeout` is zero, the callback fires
        on the next event loop iteration. If repeat is non-zero, the
        callback fires first after `timeout` milliseconds and then
        repeatedly after `repeat` milliseconds.

        :raises uv.UVError: error while starting the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param timeout: timeout which should be used (in milliseconds)
        :param callback: callback which should be called on timeout
        :param repeat: repeat interval which should be set (in milliseconds)

        :type timeout: int
        :type callback: (uv.Timer) -> None
        :type repeat: int
        """
        if self.closing: raise HandleClosedError()
        self.callback = callback or self.callback
        code = lib.uv_timer_start(self.uv_timer, uv_timer_cb, timeout, repeat)
        if code < 0: raise UVError(code)

    def stop(self):
        """
        Stops the handle, the callback will no longer be called.

        :raises uv.UVError: error while stopping the handle
        """
        if self.closing: return
        code = lib.uv_timer_stop(self.uv_timer)
        if code < 0: raise UVError(code)


