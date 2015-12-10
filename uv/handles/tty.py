# -*- coding: utf-8 -*-
#
# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals, division

from ..library import ffi, lib

from ..common import Enumeration
from ..error import UVError, HandleClosedError
from ..handle import HandleType

from .stream import Stream


class ConsoleSize(tuple):
    def __new__(cls, width, height):
        return tuple.__new__(cls, (width, height))

    def __init__(self, width, height):
        super(ConsoleSize, self).__init__((width, height))

    @property
    def width(self):
        return self[0]

    @property
    def height(self):
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
    if code < 0: raise UVError(code)


class TTYMode(Enumeration):
    """
    TTY modes enumeration.
    """

    NORMAL = lib.UV_TTY_MODE_NORMAL
    """
    initial normal terminal mode
    """
    RAW = lib.UV_TTY_MODE_RAW
    """
    raw input mode (on windows, `ENABLE_WINDOW_INPUT` is also enabled)
    """
    IO = lib.UV_TTY_MODE_IO
    """
    binary-safe IO mode for IPC (Unix only)
    """


@HandleType.TTY
class TTY(Stream):
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
            raise UVError(code)

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
        if code < 0: raise UVError(code)
        return ConsoleSize(c_with[0], c_height[0])

    def set_mode(self, mode=TTYMode.NORMAL):
        """
        Set the TTY using the specified terminal mode.

        :raises uv.UVError: error while setting mode
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param mode: mode to set
        :type mode: uv.TTYMode
        """
        if self.closing: raise HandleClosedError()
        code = lib.uv_tty_set_mode(self.uv_tty, mode)
        if code < 0: raise UVError(code)
