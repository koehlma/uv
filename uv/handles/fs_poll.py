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

from .. import base, common, error, fs, handle
from ..library import lib


@base.handle_callback('uv_fs_poll_cb')
def uv_fs_poll_cb(fs_poll_handle, status, uv_previous_stat, uv_current_stat):
    """
    :type fs_poll_handle:
        uv.FSPoll
    :type status:
        int
    :type uv_previous_stat:
        ffi.CData[uv_stat_t*]
    :type uv_current_stat:
        ffi.CData[uv_stat_t*]
    """
    previous_stat = fs.unpack_stat(uv_previous_stat) if uv_previous_stat else None
    current_stat = fs.unpack_stat(uv_current_stat) if uv_current_stat else None
    fs_poll_handle.on_change(fs_poll_handle, status, previous_stat, current_stat)


@handle.HandleTypes.FS_POLL
class FSPoll(handle.UVHandle):
    """
    FS poll handles monitor a given filesystem path for changes. Unlike
    fs event handles, fs poll handles use `stat()` to detect when a
    file or directory has been changed so they can work on file systems
    where fs event handles can not.

    .. note::
        For maximum portability, use multi-second intervals. Sub-second
        intervals will not detect all changes on many file systems.

    :raises uv.UVError:
        error while initializing the handle

    :param path:
        directory or filename to monitor
    :param interval:
        interval to be used for monitoring (in milliseconds)
    :param loop:
        event loop the handle should run on
    :param on_change:
        callback which should be called on filesystem changes after the
        handle has been started

    :type path:
        unicode
    :type interval:
        int
    :type loop:
        uv.Loop
    :type on_change:
        ((uv.FSPoll, uv.StatusCode, uv.Stat, uv.Stat) -> None) |
        ((Any, uv.FSPoll, uv.StatusCode, uv.Stat, uv.Stat) -> None)
    """

    __slots__ = ['uv_fs_poll', 'on_change', 'path', 'interval']

    uv_handle_type = 'uv_fs_poll_t*'
    uv_handle_init = lib.uv_fs_poll_init

    def __init__(self, path=None, interval=5000, loop=None, on_change=None):
        super(FSPoll, self).__init__(loop)
        self.uv_fs_poll = self.base_handle.uv_object
        self.path = path
        """
        Directory or filename to monitor.

        .. warning::
            This property is writable, however you need to restart the
            handle if you change it during the handle is active.

        :readonly:
            False
        :type:
            unicode
        """
        self.interval = interval
        """
        Interval to be used for monitoring (in milliseconds).

        .. warning::
            This property is writable, however you need to restart the
            handle if you change it during the handle is active.

        :readonly:
            False
        :type:
            int
        """
        self.on_change = on_change or common.dummy_callback
        """
        Callback which should be called on filesystem changes after the
        handle has been started.


        .. function:: on_change(fs_poll, status, previous_stat, current_stat)

            :param fs_event:
                handle the call originates from
            :param status:
                may indicate any errors
            :param previous_stat:
                previous filesystem path's stat
            :param current_stat:
                current filesystem path's stat

            :type fs_event:
                uv.FSEvent
            :type status:
                uv.StatusCode
            :type previous_stat:
                uv.Stat
            :type current_stat:
                uv.Stat


        :readonly:
            False
        :type:
            ((uv.FSPoll, uv.StatusCode, uv.Stat,
              uv.Stat) -> None)
            ((Any, uv.FSPoll, uv.StatusCode, uv.Stat,
              uv.Stat) -> None)
        """

    def start(self, path=None, interval=None, on_change=None):
        """
        Start monitoring for filesystem changes. The change callback is
        invoked with status code < 0 if the given path does not exist
        or is inaccessible. The watcher is not stopped but your callback
        is not called again until something changes (e.g. when the file
        is created or the error reason changes).

        :raises uv.UVError:
            error while starting the handle
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param path:
            directory or filename to monitor (overrides the current
            path if specified)
        :param interval:
            interval to be used for monitoring (in milliseconds and
            overrides the current interval if specified)
        :param on_change:
            callback which should be called on filesystem changes

        :type path:
            unicode
        :type interval:
            int
        :type on_change:
            ((uv.FSPoll, uv.StatusCode, uv.Stat, uv.Stat) -> None) |
            ((Any, uv.FSPoll, uv.StatusCode, uv.Stat, uv.Stat) -> None)
        """
        if self.closing:
            raise error.ClosedHandleError()
        self.path = path or self.path
        self.interval = interval or self.interval
        self.on_change = on_change or self.on_change
        if self.path is None:
            raise error.ArgumentError(message='no path has been specified')
        c_path = self.path.encode()
        code = lib.uv_fs_poll_start(self.uv_fs_poll, uv_fs_poll_cb, c_path, self.interval)
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
        code = lib.uv_fs_poll_stop(self.uv_fs_poll)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.clear_pending()

    __call__ = start
