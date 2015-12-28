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

from .. import common, error, fs, handle, library
from ..library import ffi, lib

__all__ = ['FSPoll']


@ffi.callback('uv_fs_poll_cb')
def uv_fs_poll_cb(uv_fs_poll, status, uv_previous_stat, uv_current_stat):
    previous_stat = fs.unpack_stat(uv_previous_stat) if uv_previous_stat else None
    current_stat = fs.unpack_stat(uv_current_stat) if uv_current_stat else None
    fs_poll = detach(uv_fs_poll)
    """ :type: uv.FSPoll """
    try:
        fs_poll.on_change(fs_poll, status, previous_stat, current_stat)
    except:
        fs_poll.loop.handle_exception()


@handle.HandleType.FS_POLL
class FSPoll(handle.Handle):
    """
    FS poll handles monitor a given filesystem path for changes. Unlike
    fs event handles, fs poll handles use `stat()` to detect when a
    file or directory has been changed so they can work on file systems
    where fs event handles can not.

    .. note::
        For maximum portability, use multi-second intervals. Sub-second
        intervals will not detect all changes on many file systems.
    """

    __slots__ = ['uv_fs_poll', 'on_change', 'path', 'interval']

    def __init__(self, path=None, interval=5000, loop=None, on_change=None):
        """
        :raises uv.UVError:
            error while initializing the handle

        :param path:
            directory or filename to monitor
        :param interval:
            interval to be used for monitoring (in milliseconds)
        :param loop:
            event loop the handle should run on
        :param on_change:
            callback which should be called on filesystem changes

        :type path:
            unicode
        :type interval:
            int
        :type loop:
            uv.Loop
        :type on_change:
            ((uv.FSPoll, uv.StatusCode, uv.fs.Stat, uv.fs.Stat) -> None) |
            ((Any, uv.FSPoll, uv.StatusCode, uv.fs.Stat, uv.fs.Stat) -> None)
        """
        self.uv_fs_poll = ffi.new('uv_fs_poll_t*')
        super(FSPoll, self).__init__(loop)
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
        Callback which should be called on filesystem changes.


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
                uv.fs.Stat
            :type current_stat:
                uv.fs.Stat


        :readonly:
            False
        :type:
            ((uv.FSPoll, uv.StatusCode, uv.fs.Stat, uv.fs.Stat) -> None)
            ((Any, uv.FSPoll, uv.StatusCode, uv.fs.Stat, uv.fs.Stat) -> None)
        """
        code = lib.uv_fs_poll_init(self.loop.uv_loop, self.uv_fs_poll)
        if code < 0:
            self.destroy()
            raise error.UVError(code)

    def start(self, path=None, interval=None, on_change=None):
        """
        Start monitoring for filesystem changes. The change callback is
        invoked with status code < 0 if the given path does not exist
        or is inaccessible. The watcher is not stopped but your callback
        is not called again until something changes (e.g. when the file
        is created or the error reason changes).

        :raises uv.UVError:
            error while starting the handle
        :raises uv.HandleClosedError:
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
            ((uv.FSPoll, uv.StatusCode, uv.fs.Stat, uv.fs.Stat) -> None) |
            ((Any, uv.FSPoll, uv.StatusCode, uv.fs.Stat, uv.fs.Stat) -> None)
        """
        # TODO: assert path is not none
        if self.closing:
            raise error.HandleClosedError()
        self.path = path or self.path
        self.interval = interval or self.interval
        self.on_change = on_change or self.on_change
        c_path = library.str_py2c(path)
        code = lib.uv_fs_poll_start(self.uv_fs_poll, uv_fs_poll_cb, c_path, self.interval)
        if code < 0:
            raise error.UVError(code)

    def stop(self):
        """
        Stops the handle, the callback will no longer be called.

        :raises uv.UVError:
            error while stopping the handle
        """
        if self.closing:
            return
        code = lib.uv_fs_poll_stop(self.uv_fs_poll)
        if code < 0:
            raise error.UVError(code)

    __call__ = start
