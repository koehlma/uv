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


class PollEvent(common.Enumeration):
    """
    Events reported by :class:`uv.Poll` on IO events.
    """

    READABLE = lib.UV_READABLE
    """
    File descriptor is readable.

    :type: uv.PollEvent
    """

    WRITABLE = lib.UV_WRITABLE
    """
    File descriptor is writable.

    :type: uv.PollEvent
    """


@base.handle_callback('uv_poll_cb')
def poll_callback(poll_handle, status, events):
    """
    :type poll_handle:
        uv.Poll
    :type status:
        int
    :type events:
        int
    """
    poll_handle.on_event(poll_handle, error.StatusCodes.get(status), events)


@handle.HandleTypes.POLL
class Poll(handle.UVHandle):
    """
    Poll handles are used to watch file descriptors for readability and
    writability. The purpose of poll handles is to enable integrating
    external libraries that rely on the event loop to signal them about
    the socket status changes. Using them for any other purpose is not
    recommended. Use :class:`uv.TCP`, :class:`uv.UDP`, etc. instead,
    which provide faster and more scalable implementations, than what
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

    :raises uv.UVError:
        error while initializing the handle

    :param fd:
        file descriptor to be polled (is set to non-blocking mode)
    :param loop:
        event loop the handle should run on
    :param on_event:
        callback which should be called on IO events after the handle
        has been started

    :type fd:
        int
    :type loop:
        uv.Loop
    :type on_event:
        ((uv.Poll, uv.StatusCode, int) -> None) |
        ((Any, uv.Poll, uv.StatusCode, int) -> None)
    """

    __slots__ = ['uv_poll', 'fd', 'on_event']

    uv_handle_type = 'uv_poll_t*'
    uv_handle_init = lib.cross_uv_poll_init_socket

    def __init__(self, fd, loop=None, on_event=None):
        super(Poll, self).__init__(loop, (fd, ))
        self.uv_poll = self.base_handle.uv_object
        self.fd = fd
        """
        File descriptor the handle polls on.

        :readonly:
            True
        :type:
            int
        """
        self.on_event = on_event or common.dummy_callback
        """
        Callback which should be called on IO events after the handle
        has been started.


        .. function:: on_event(poll_handle, status, events)

            :param poll_handle:
                handle the call originates from
            :param status:
                may indicate any errors
            :param events:
                bitmask of the triggered IO events

            :type poll_handle:
                uv.Poll
            :type status:
                uv.StatusCode
            :type events:
                int


        :readonly:
            False
        :type:
            ((uv.Poll, uv.StatusCode, int) -> None) |
            ((Any, uv.Poll, uv.StatusCode, int) -> None)
        """

    def fileno(self):
        """
        Number of the file descriptor polled on.

        :rtype:
            int
        """
        return self.fd

    def start(self, events=PollEvent.READABLE, on_event=None):
        """
        Start polling the file descriptor for the given events. As soon
        as an event is detected the callback will be called with status
        code class:`uv.StatusCode.SUCCESS` and the triggered events.

        If an error happens while polling the callback gets called with
        status code != 0 which corresponds to a :class:`uv.StatusCode`.

        Calling this on a handle that is already active is fine. Doing
        so will update the events mask that is being polled for.

        :raises uv.UVError:
            error while starting the handle
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param events:
            bitmask of events to be polled for
        :param on_event:
            callback which should be called on IO events (overrides the
            current callback if specified)

        :type events:
            int
        :type on_event:
            ((uv.Poll, uv.StatusCode, int) -> None) |
            ((Any, uv.Poll, uv.StatusCode, int) -> None)
        """
        if self.closing:
            raise error.ClosedHandleError()
        self.on_event = on_event or self.on_event
        code = lib.uv_poll_start(self.uv_poll, events, poll_callback)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        if events:
            self.set_pending()
        else:
            self.clear_pending()

    def stop(self):
        """
        Stop the handle. The callback will no longer be called.

        :raises uv.UVError
            error while stopping the handle
        """
        if self.closing:
            return
        code = lib.uv_poll_stop(self.uv_poll)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.clear_pending()

    __call__ = start
