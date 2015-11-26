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

from .library import ffi, lib, detach, dummy_callback

from .error import UVError
from .handle import HandleType, Handle
from .loop import Loop

__all__ = ['Poll', 'PollEvent']


class PollEvent(enum.IntEnum):
    READABLE = lib.UV_READABLE
    WRITABLE = lib.UV_WRITABLE


@ffi.callback('uv_poll_cb')
def poll_callback(uv_poll, status, events):
    poll = detach(uv_poll)
    poll.on_event(poll, status, events)


@HandleType.POLL
class Poll(Handle):
    __slots__ = ['uv_poll', 'fd', 'on_event']

    def __init__(self, fd: int, loop: Loop=None, on_event: callable=None):
        self.fd = fd
        self.uv_poll = ffi.new('uv_poll_t*')
        self.on_event = on_event or dummy_callback
        super().__init__(self.uv_poll, loop)
        lib.cross_uv_poll_init_socket(self.loop.uv_loop, self.uv_poll, fd)

    def start(self, events: int=PollEvent.READABLE, on_event: callable=None):
        self.on_event = on_event or self.on_event
        code = lib.uv_poll_start(self.uv_poll, events, poll_callback)
        if code < 0: raise UVError(code)

    def stop(self):
        code = lib.uv_poll_stop(self.uv_poll)
        if code < 0: raise UVError(code)
