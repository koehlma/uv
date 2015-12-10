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

from ..library import ffi, lib, detach

from ..common import dummy_callback, Enumeration
from ..error import UVError, HandleClosedError
from ..handle import HandleType, Handle

__all__ = ['FSMonitor', 'FSEventFlags', 'FSEvent']


class FSEventFlags(Enumeration):
    """
    FS event flags enumeration.
    """

    WATCH_ENTRY = lib.UV_FS_EVENT_WATCH_ENTRY
    """
    By default, if the fs event watcher is given a directory name,
    it will watch for all events in that directory. This flags
    overrides this behavior and makes :class:`uv.FSEvent` report
    only changes to the directory entry itself. This flag does not
    affect individual files watched.

    .. note::

        This flag is currently not implemented yet on any backend.

    :type: int
    """
    STAT = lib.UV_FS_EVENT_STAT
    """
    By default :class:`uv.FSEvent` will try to use a kernel interface such
    as inotify or kqueue to detect events. This may not work on remote
    filesystems such as NFS mounts. This flag makes :class:`uv.FSEvent` fall
    back to calling `stat()` on a regular interval.

    .. note::

        This flag is currently not implemented yet on any backend.

    :type: int
    """
    RECURSIVE = lib.UV_FS_EVENT_RECURSIVE
    """
    By default, event watcher, when watching directory, is not registering
    (is ignoring) changes in it's subdirectories. This flag will override
    this behaviour on platforms that support it.

    .. note::

        Currently the only supported platforms are OSX and Windows.

    :type: int
    """


class FSEvent(Enumeration):
    """
    FS event types enumeration.
    """

    RENAME = lib.UV_RENAME
    """
    File has been renamed or deleted.

    :type: int
    """
    CHANGE = lib.UV_CHANGE
    """
    File has been changed.

    :type: int
    """


@ffi.callback('uv_fs_event_cb')
def uv_fs_event_cb(uv_fs_event, c_filename, events, status):
    fs_monitor = detach(uv_fs_event)
    filename = ffi.string(c_filename).decode()
    with fs_monitor.loop.callback_context:
        fs_monitor.on_event(fs_monitor, status, filename, events)


@HandleType.FS_EVENT
class FSMonitor(Handle):
    """
    FS handles monitor a given path for changes, for example, if the
    file was renamed or there was a generic change in it. This handle
    uses the best backend for the job on each platform.

    :raises uv.UVError: error while initializing the handle

    :param path: path to be monitored
    :param flags: flags to be used for monitoring
    :param loop: event loop the handle should run on
    :param on_event: callback called on FS event

    :type path: str
    :type flags: int
    :type loop: uv.Loop
    :type on_event: (uv.FSMonitor, uv.StatusCode, str, int) -> None
    """

    __slots__ = ['uv_fs_event', 'on_event', 'flags', 'path']

    def __init__(self, path=None, flags=0, loop=None, on_event=None):
        self.uv_fs_event = ffi.new('uv_fs_event_t*')
        super(FSMonitor, self).__init__(self.uv_fs_event, loop)
        self.path = path
        """
        Path to be monitored.

        .. warning::

            This property is writable, however you need to restart the
            handle if you change it during the handle is active.

        :readonly: False
        :type: str
        """
        self.flags = flags
        """
        Flags to be used for monitoring.

        .. warning::

            This property is writable, however you need to restart the
            handle if you change it during the handle is active.

        :readonly: False
        :type: int
        """
        self.on_event = on_event or dummy_callback
        """
        Callback called on FS events.

        .. function:: on_event(FSEvent-Handle, Status-Code, Filename, Event-Mask)

        :readonly: False
        :type: (uv.FSEvent, uv.StatusCode, str, int) -> None
        """
        code = lib.uv_fs_event_init(self.loop.uv_loop, self.uv_fs_event)
        if code < 0:
            self.destroy()
            raise UVError(code)

    def start(self, path=None, flags=None, on_event=None):
        """
        Starts monitoring for FS events.

        :raises uv.UVError: error while starting the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param path: path to be monitored
        :param flags: flags to be used for monitoring
        :param on_event: callback called on FS events

        :type path: str
        :type flags: int
        :type on_event: (uv.FSMonitor, uv.StatusCode, str, int) -> None
        """
        if self.closing: raise HandleClosedError()
        self.path = path or self.path
        self.flags = flags or self.flags
        self.on_event = on_event or self.on_event
        c_path = self.path.encode()
        code = lib.uv_fs_event_start(self.uv_fs_event, uv_fs_event_cb, c_path, self.flags)
        if code < 0: raise UVError(code)

    def stop(self):
        """
        Stops the handle, the callback will no longer be called.

        :raises uv.UVError: error while stopping the handle
        """
        if self.closing: return
        code = lib.uv_fs_event_stop(self.uv_fs_event)
        if code < 0: raise UVError(code)

    __call__ = start
