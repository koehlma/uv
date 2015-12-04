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

from ..common import dummy_callback, Enumeration
from ..error import UVError, HandleClosedError
from ..handle import HandleType, Handle

__all__ = ['Poll', 'PollEvent']


class PollEvent(Enumeration):
    """
    Poll event types enumeration.
    """
    READABLE = lib.UV_READABLE
    """
    File descriptor is readable.

    :type: int
    """
    WRITABLE = lib.UV_WRITABLE
    """
    File descriptor is writable.

    :type: int
    """


@ffi.callback('uv_poll_cb')
def poll_callback(uv_poll, status, events):
    poll = detach(uv_poll)
    with poll.loop.callback_context:
        poll.on_event(poll, status, events)


@HandleType.POLL
class Poll(Handle):
    """
    Poll handles are used to watch file descriptors for readability and
    writability. The purpose of poll handles is to enable integrating
    external libraries that rely on the event loop to signal them about
    the socket status changes. Using them for any other purpose is not
    recommended. Use :class:`uv.TCP`, :class:`uv.UDP`, etc. instead,
    which provide faster an more scalable implementations, that what
    can be archived with :class:`uv.Poll`, especially on Windows.

    It is possible that poll handles occasionally signal that a file
    descriptor is readable or writable even when it is not. The user
    should therefore always be prepared to handle `EAGAIN` or equivalent
    when it attempts to read from or write to the fd.

    It is not okay to have multiple active poll handles for the same
    socket, this can cause libuv to busyloop or otherwise malfunction.

    Do not close a file descriptor while it is being polled by an active
    poll handle. This can cause the handle to report an error, but it
    might also start polling another socket. However the fd can be
    safely closed immediately after :func:`uv.Poll.stop` or
    :func:`uv.Handle.close` has been called.

    .. note::

        On Windows only sockets can be polled with :class:`uv.Poll`
        handles. On Unix any file descriptor that would be accepted
        by :manpage:`poll(2)` can be used.

    :raises uv.UVError: error during the initialization of the handle

    :param fd: file descriptor which should be polled (is set to non-blocking mode)
    :param loop: event loop which should be used for the handle
    :param on_event: callback which should be called on IO events

    :type fd: int
    :type loop: Loop
    :type on_event: (uv.Poll, uv.StatusCode, int) -> None
    """
    __slots__ = ['uv_poll', 'fd', 'on_event']

    def __init__(self, fd, loop=None, on_event=None):
        self.uv_poll = ffi.new('uv_poll_t*')
        super(Poll, self).__init__(self.uv_poll, loop)
        self.fd = fd
        """
        File descriptor the handle polls on.

        :readonly: True
        :type: int
        """
        self.on_event = on_event or dummy_callback
        """
        Callback which should be called on IO events.

        .. function:: on_event(Poll-Handle, Status-Code, Event-Mask)

        :readonly: False
        :type: (uv.Poll, uv.StatusCode, int) -> None
        """
        code = lib.cross_uv_poll_init_socket(self.loop.uv_loop, self.uv_poll, fd)
        if code < 0:
            self.destroy()
            raise UVError(code)

    def start(self, events=PollEvent.READABLE, on_event=None):
        """
        Starts polling the file descriptor for the given events. As soon as
        an event is detected the callback will be called with status code
        :class:`uv.StatusCode.SUCCESS` and the detected events.

        If an error happens while polling the callback gets called with status
        code < 0 which corresponds to a :class:`uv.StatusCode`.

        Calling this on a handle that is already active is fine. Doing so will
        update the events mask that is being watched for.

        :raises uv.UVError: error while starting the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param events: bitmask of events which should be polled for
        :param on_event: callback which should be called on IO events

        :type events: int
        :type on_event: (uv.Poll, uv.StatusCode, int) -> None
        """
        if self.closing: raise HandleClosedError()
        self.on_event = on_event or self.on_event
        code = lib.uv_poll_start(self.uv_poll, events, poll_callback)
        if code < 0: raise UVError(code)

    def stop(self):
        """
        Stops the handle, the callback will no longer be called.

        :raises uv.UVError: error while stopping the handle
        """
        if self.closing: return
        code = lib.uv_poll_stop(self.uv_poll)
        if code < 0: raise UVError(code)

    def destroy(self):
        self.uv_poll = None
        super(Poll, self).destroy()

    __call__ = start
