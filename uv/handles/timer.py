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


@base.handle_callback('uv_timer_cb')
def uv_timer_cb(timer_handle):
    """
    :type timer_handle:
        uv.Timer
    """
    if not timer_handle.repeat:
        timer_handle.clear_pending()
    timer_handle.on_timeout(timer_handle)


@handle.HandleTypes.TIMER
class Timer(handle.UVHandle):
    """
    Timer handles are used to schedule callbacks to be called in the
    future after a given amount of time.

    :raises uv.UVError:
        error while initializing the handle

    :param loop: event
        loop the handle should run on
    :param on_timeout:
        callback which should run on timeout

    :type loop:
        uv.Loop
    :type on_timeout:
        ((uv.Timer) -> None) | ((Any, uv.Timer) -> None)
    """

    __slots__ = ['uv_timer', 'on_timeout']

    uv_handle_type = 'uv_timer_t*'
    uv_handle_init = lib.uv_timer_init

    def __init__(self, loop=None, on_timeout=None):
        super(Timer, self).__init__(loop)
        self.uv_timer = self.base_handle.uv_object
        self.on_timeout = on_timeout or common.dummy_callback
        """
        Callback which should run on timeout.


        .. function:: on_timeout(timer_handle)

            :param timer_handle:
                handle the call originates from

            :type timer_handle:
                uv.Timer


        :readonly:
            False
        :type:
            ((uv.Timer) -> None) | ((Any, uv.Timer) -> None)
        """

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
            If the repeat value is set from a timer callback it does
            not immediately take effect. If the timer was non-repeating
            before, it will have been stopped. If it was repeating,
            then the old repeat value will have been used to schedule
            the next timeout.

        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :readonly:
            False
        :rtype:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        return lib.uv_timer_get_repeat(self.uv_timer)

    @repeat.setter
    def repeat(self, repeat):
        """
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param repeat:
            repeat interval which should be set in milliseconds

        :type repeat:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        lib.uv_timer_set_repeat(self.uv_timer, repeat)

    def again(self):
        """
        Stop the timer, and if it is repeating restart it using the
        repeat value as the timeout. If the timer has never been
        started before it raises :class:`uv.error.ArgumentError`.

        :raises uv.UVError:
            error while restarting the timer
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing
        """
        if self.closing:
            raise error.ClosedHandleError
        code = lib.uv_timer_again(self.uv_timer)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        if self.repeat:
            self.set_pending()

    def start(self, timeout, repeat=0, on_timeout=None):
        """
        Start the timer. If `timeout` is zero, the callback fires on
        the next event loop iteration. If repeat is non-zero, the
        callback fires first after `timeout` milliseconds and then
        repeatedly after `repeat` milliseconds.

        :raises uv.UVError:
            error while starting the handle
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param timeout
            timeout to be used (in milliseconds)
        :param repeat:
            repeat interval to be used (in milliseconds)
        :param on_timeout:
            callback which should run on timeout (overrides the current
            callback if specified)

        :type timeout:
            int
        :type repeat:
            int
        :type on_timeout:
            ((uv.Timer) -> None) | ((Any, uv.Timer) -> None)
        """
        if self.closing:
            raise error.ClosedHandleError()
        self.on_timeout = on_timeout or self.on_timeout
        code = lib.uv_timer_start(self.uv_timer, uv_timer_cb, timeout, repeat)
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
        code = lib.uv_timer_stop(self.uv_timer)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.clear_pending()
