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
    fs_poll = library.detach(uv_fs_poll)
    with fs_poll.loop.callback_context:
        fs_poll.callback(fs_poll, status, previous_stat, current_stat)


@handle.HandleType.FS_POLL
class FSPoll(handle.Handle):
    """
    FS poll handles monitor a given path for changes. Unlike :class:`uv.FSMonitor`
    fs poll handles use stat to detect when a file has changed so they can work
    on file systems where fs event handles can not.

    :raises uv.UVError: error while initializing the handle

    :param path: path to be monitored
    :param interval: interval to be used for monitoring (in milliseconds)
    :param loop: event loop the handle should run on
    :param on_change: callback called on FS change

    :type path: unicode
    :type interval: int
    :type loop: uv.Loop
    :type on_change: ((uv.FSPoll, uv.StatusCode, uv.fs.Stat, uv.fs.Stat) -> None) |
                     ((Any, uv.FSPoll, uv.StatusCode, uv.fs.Stat, uv.fs.Stat) -> None)
    """

    __slots__ = ['uv_fs_poll', 'on_change', 'path', 'interval']

    def __init__(self, path=None, interval=5000, loop=None, on_change=None):
        self.uv_fs_poll = ffi.new('uv_fs_poll_t*')
        super(FSPoll, self).__init__(loop)
        self.path = path
        """
        Path to be monitored.

        .. warning::

            This property is writable, however you need to restart the
            handle if you change it during the handle is active.

        :readonly: False
        :type: unicode
        """
        self.interval = interval
        """
        Interval to be used for monitoring (in milliseconds).

        .. warning::

            This property is writable, however you need to restart the
            handle if you change it during the handle is active.

        :readonly: False
        :type: int
        """
        self.on_change = on_change or common.dummy_callback
        """
        Callback called on FS change.

        .. function:: on_change(FSPoll, Status, Previous-Stat, Current-Stat)

        :readonly: False
        :type: ((uv.FSPoll, uv.StatusCode, uv.fs.Stat, uv.fs.Stat) -> None)
               ((Any, uv.FSPoll, uv.StatusCode, uv.fs.Stat, uv.fs.Stat) -> None)
        """
        code = lib.uv_fs_poll_init(self.loop.uv_loop, self.uv_fs_poll)
        if code < 0:
            self.destroy()
            raise error.UVError(code)

    def start(self, path=None, interval=None, on_change=None):
        """
        Starts monitoring for FS changes. The callback is invoked with
        status < 0 if path does not exist or is inaccessible. The watcher
        is not stopped but your callback is not called again until something
        changes (e.g. when the file is created or the error reason changes).

        :raises uv.UVError: error while starting the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param path: path to be monitored
        :param interval: interval to be used for monitoring (in milliseconds)
        :param on_change: callback called on FS change

        :type path: unicode
        :type interval: int
        :type on_change: ((uv.FSPoll, uv.StatusCode, uv.fs.Stat, uv.fs.Stat) -> None) |
                         ((Any, uv.FSPoll, uv.StatusCode, uv.fs.Stat, uv.fs.Stat) -> None)
        """
        if self.closing: raise error.HandleClosedError()
        self.path = path or self.path
        self.interval = interval or self.interval
        self.on_change = on_change or self.on_change
        c_path = self.path.encode()
        code = lib.uv_fs_poll_start(self.uv_fs_poll, uv_fs_poll_cb, c_path, self.interval)
        if code < 0: raise error.UVError(code)

    def stop(self):
        """
        Stops the handle, the callback will no longer be called.

        :raises uv.UVError: error while stopping the handle
        """
        if self.closing: return
        code = lib.uv_fs_poll_stop(self.uv_fs_poll)
        if code < 0: raise error.UVError(code)

    __call__ = start
