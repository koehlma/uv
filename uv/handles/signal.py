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

import signal as std_signal

from .. import common, error, handle, library
from ..library import ffi, lib

__all__ = ['Signal', 'Signals']


class Signals(common.Enumeration):
    """ """

    SIGINT = getattr(std_signal, 'SIGINT', 2)
    """
    Is normally delivered when the user presses CTRL+C. However it is
    not generated when terminal is in raw mode.

    :type: int
    """
    SIGBREAK = 21
    """
    Is delivered when the user presses CTRL+BREAK. This signal is only
    supported on Windows.

    :type: int
    """
    SIGHUP = getattr(std_signal, 'SIGHUP', 1)
    """
    Is generated when the user closes the console window. After that the
    OS might terminate the program after a few seconds.

    :type: int
    """
    SIGWINCH = getattr(std_signal, 'SIGWINCH', 28)
    """
    Is generated when the console window has been resized. On Windows libuv
    emulates SIGWINCH when the program uses a :class:`uv.TTY` handle to
    write to the console. It may not always be delivered in a timely manner,
    because libuv will only detect changes when the cursor is being moved.
    When a readable :class:`uv.TTY` handle is used in raw mode, resizing
    the console buffer will also trigger SIGWINCH.

    :type: int
    """


@ffi.callback('uv_signal_cb')
def uv_signal_cb(uv_signal, signum):
    signal = library.detach(uv_signal)
    """ :type: uv.Signal """
    if signal is not None:
        try:
            signal.on_signal(signal, signum)
        except:
            signal.loop.handle_exception()


@handle.HandleTypes.SIGNAL
class Signal(handle.Handle):
    """
    Signal handles implement Unix style signal handling on a per-event
    loop bases. Reception of the generic :class:`uv.Signals` is emulated
    on Windows. Watchers for other signals can be successfully created,
    but these signals are never received.

    .. note::

        On Linux SIGRT0 and SIGRT1 (signals 32 and 33) are used by the
        NPTL pthreads library to manage threads. Installing watchers for
        those signals will lead to unpredictable behavior and is strongly
        discouraged. Future versions of libuv may simply reject them.

    :raises uv.UVError: error while initializing the handle

    :param loop: event loop the handle should run on
    :param on_signal: callback called on signal delivery

    :type loop: uv.Loop
    :type on_signal: ((uv.Signal, int) -> None) | ((Any, uv.Signal, int) -> None)
    """

    __slots__ = ['uv_signal', 'on_signal']

    def __init__(self, loop=None, on_signal=None):
        self.uv_signal = ffi.new('uv_signal_t*')
        super(Signal, self).__init__(self.uv_signal, loop)
        self.on_signal = on_signal or common.dummy_callback
        """
        Callback called on signal delivery.

        .. function:: on_signal(Signal, Signum)

        :readonly: False
        :type: ((uv.Signal, int) -> None) | ((Any, uv.Signal, int) -> None)
        """
        code = lib.uv_signal_init(self.loop.uv_loop, self.uv_signal)
        if code < 0:
            self.set_closed()
            raise error.UVError(code)

    @property
    def signum(self):
        """
        Signal being monitored by this handle.

        :raises uv.HandleClosedError: handle has already been closed or is closing

        :readonly: True
        :rtype: int
        """
        if self.closing: raise error.ClosedHandleError()
        return self.uv_signal.signum

    def start(self, signum, on_signal=None):
        """
        Starts the handle.

        :raises uv.UVError: error while starting the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param signum: signal number to be monitored
        :param on_signal: callback called on signal delivery

        :type signum: int
        :type on_signal: ((uv.Signal, int) -> None) | ((Any, uv.Signal, int) -> None)
        """
        if self.closing: raise error.ClosedHandleError()
        self.on_signal = on_signal or self.on_signal
        code = lib.uv_signal_start(self.uv_signal, uv_signal_cb, signum)
        if code < 0: raise error.UVError(code)
        self.set_pending()

    def stop(self):
        """
        Stops the handle, the callback will no longer be called.

        :raises uv.UVError: error while stopping the handle
        """
        if self.closing: return
        code = lib.uv_signal_stop(self.uv_signal)
        if code < 0: raise error.UVError(code)
        self.clear_pending()

    __call__ = start
