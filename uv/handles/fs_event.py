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

from .. import common, error, handle, library
from ..library import ffi, lib

__all__ = ['FSEventFlags', 'FSEvents', 'FSEvent']


class FSEventFlags(common.Enumeration):
    """ """
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


class FSEvents(common.Enumeration):
    """ """
    RENAME = lib.UV_RENAME
    """
    File has been renamed.

    :type: int
    """
    CHANGE = lib.UV_CHANGE
    """
    File has been changed.

    :type: int
    """


@ffi.callback('uv_fs_event_cb')
def uv_fs_event_cb(uv_fs_event, c_filename, events, status):
    fs_monitor = library.detach(uv_fs_event)
    with fs_monitor.loop.callback_context:
        filename = library.str_c2py(c_filename)
        fs_monitor.on_event(fs_monitor, status, filename, events)


@handle.HandleType.FS_EVENT
class FSEvent(handle.Handle):
    """
    FS handles monitor a given path for changes, for example, if the
    file was renamed or there was a generic change in it. This handle
    uses the best backend for the job on each platform.

    :raises uv.UVError: error while initializing the handle

    :param path: path to be monitored
    :param flags: flags to be used for monitoring
    :param loop: event loop the handle should run on
    :param on_event: callback called on FS event

    :type path: unicode
    :type flags: int
    :type loop: uv.Loop
    :type on_event: ((uv.FSMonitor, uv.StatusCode, unicode, int) -> None) |
                    ((Any, uv.FSMonitor, uv.StatusCode, unicode, int) -> None)
    """

    __slots__ = ['uv_fs_event', 'on_event', 'flags', 'path']

    def __init__(self, path=None, flags=0, loop=None, on_event=None):
        self.uv_fs_event = ffi.new('uv_fs_event_t*')
        super(FSEvent, self).__init__(self.uv_fs_event, loop)
        self.path = path
        """
        Path to be monitored.

        .. warning::

            This property is writable, however you need to restart the
            handle if you change it during the handle is active.

        :readonly: False
        :type: unicode
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
        self.on_event = on_event or common.dummy_callback
        """
        Callback called on FS events.

        .. function:: on_event(FSMonitor, Status, Filename, Events)

        :readonly: False
        :type: ((uv.FSMonitor, uv.StatusCode, unicode, int) -> None) |
               ((Any, uv.FSMonitor, uv.StatusCode, unicode, int) -> None)
        """
        code = lib.uv_fs_event_init(self.loop.uv_loop, self.uv_fs_event)
        if code < 0:
            self.destroy()
            raise error.UVError(code)

    def start(self, path=None, flags=None, on_event=None):
        """
        Starts monitoring for FS events.

        :raises uv.UVError: error while starting the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param path: path to be monitored
        :param flags: flags to be used for monitoring
        :param on_event: callback called on FS events

        :type path: unicode
        :type flags: int
        :type on_event: ((uv.FSMonitor, uv.StatusCode, unicode, int) -> None) |
                        ((Any, uv.FSMonitor, uv.StatusCode, unicode, int) -> None)
        """
        if self.closing: raise error.HandleClosedError()
        self.path = path or self.path
        self.flags = flags or self.flags
        self.on_event = on_event or self.on_event
        c_path = self.path.encode()
        code = lib.uv_fs_event_start(self.uv_fs_event, uv_fs_event_cb, c_path, self.flags)
        if code < 0: raise error.UVError(code)

    def stop(self):
        """
        Stops the handle, the callback will no longer be called.

        :raises uv.UVError: error while stopping the handle
        """
        if self.closing: return
        code = lib.uv_fs_event_stop(self.uv_fs_event)
        if code < 0: raise error.UVError(code)

    __call__ = start
