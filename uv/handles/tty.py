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

from .. import common, error, handle
from ..library import ffi, lib

from . import stream

__all__ = ['ConsoleSize', 'reset_mode', 'TTYMode', 'TTY']


class ConsoleSize(tuple):
    def __new__(cls, width, height):
        return tuple.__new__(cls, (width, height))

    # to satisfy pycharm
    def __init__(self, width, height):
        super(ConsoleSize, self).__init__((width, height))

    @property
    def width(self):
        """
        Width of th console.

        :readonly: True
        :type: int
        """
        return self[0]

    @property
    def height(self):
        """
        Height of th console.

        :readonly: True
        :type: int
        """
        return self[1]


def reset_mode():
    """
    To be called when the program exits. Resets TTY settings to default
    values for the next process to take over.

    This function is async signal-safe on Unix platforms but can fail with
    error code UV_EBUSY if you call it when execution is inside `set_mode()`.

    :raises uv.UVError: error while resetting tty mode
    """
    code = lib.uv_tty_reset_mode()
    if code < 0: raise error.UVError(code)


class TTYMode(common.Enumeration):
    """ """
    NORMAL = lib.UV_TTY_MODE_NORMAL
    """
    Initial normal terminal mode.
    """
    RAW = lib.UV_TTY_MODE_RAW
    """
    Raw input mode (on windows, `ENABLE_WINDOW_INPUT` is also enabled).
    """
    IO = lib.UV_TTY_MODE_IO
    """
    Binary-safe IO mode for IPC (Unix only).
    """


@handle.HandleType.TTY
class TTY(stream.Stream):
    """
    TTY handles represent a stream for the console.

    :raises uv.UVError: error while initializing the handle

    :param fd: file descriptor
    :param readable: specifies whether the file descriptor is readable or not
    :param loop: event loop the handle should run on
    :param ipc: inter process communication support

    :type fd: int
    :type readable: bool
    :type loop: uv.Loop
    :type ipc: bool
    """

    __slots__ = ['uv_tty']

    def __init__(self, fd, readable=False, loop=None, ipc=False):
        self.uv_tty = ffi.new('uv_tty_t*')
        super(TTY, self).__init__(self.uv_tty, ipc, loop)
        code = lib.cross_uv_tty_init(self.loop.uv_loop, self.uv_tty, fd, int(readable))
        if code < 0:
            self.destroy()
            raise error.UVError(code)

    @property
    def console_size(self):
        """
        Current size of the console.

        :raises uv.UVError: error while getting console size

        :rtype: ConsoleSize
        """
        if self.closing: return ConsoleSize(0, 0)
        c_with, c_height = ffi.new('int*'), ffi.new('int*')
        code = lib.uv_tty_get_winsize(self.uv_tty, c_with, c_height)
        if code < 0: raise error.UVError(code)
        return ConsoleSize(c_with[0], c_height[0])

    def set_mode(self, mode=TTYMode.NORMAL):
        """
        Set the TTY using the specified terminal mode.

        :raises uv.UVError: error while setting mode
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param mode: mode to set
        :type mode: uv.TTYMode
        """
        if self.closing: raise error.HandleClosedError()
        code = lib.uv_tty_set_mode(self.uv_tty, mode)
        if code < 0: raise error.UVError(code)
