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
from ..library import ffi, lib


class FSEventFlags(common.Enumeration):
    """
    Flags to configure the behavior of :class:`uv.FSEvent`.
    """

    WATCH_ENTRY = lib.UV_FS_EVENT_WATCH_ENTRY
    """
    By default, if the fs event watcher is given a directory
    name, it will watch for all events in that directory. This
    flag overrides this behavior and makes :class:`uv.FSEvent`
    report only changes to the directory entry itself. This flag
    does not affect individual files watched.

    .. note::
        This flag is currently not implemented yet on any backend.

    :type: uv.FSEventFlags
    """

    STAT = lib.UV_FS_EVENT_STAT
    """
    By default :class:`uv.FSEvent` will try to use a kernel
    interface such as inotify or kqueue to detect events. This
    may not work on remote filesystems such as NFS mounts. This
    flag makes :class:`uv.FSEvent` fall back to calling `stat()`
    on a regular interval.

    .. note::
        This flag is currently not implemented yet on any backend.

    :type: uv.FSEventFlags
    """

    RECURSIVE = lib.UV_FS_EVENT_RECURSIVE
    """
    By default, if the fs event watcher is given a directory name,
    it will not watch for events in its subdirectories. This flag
    overrides this behavior and makes :class:`uv.FSEvent` report
    also changes in subdirectories.

    .. note::
        Currently the only supported platforms are OSX and Windows.

    :type: uv.FSEventFlags
    """


class FSEvents(common.Enumeration):
    """
    Events reported by :class:`uv.FSEvent` on filesystem changes.
    """

    RENAME = lib.UV_RENAME
    """
    File has been renamed or deleted. If the file has been deleted it
    is necessary (at least on Linux) to restart the corresponding
    watcher even if the file has been directly recreated.

    :type: uv.FSEvents
    """

    CHANGE = lib.UV_CHANGE
    """
    File has been changed.

    :type: uv.FSEvents
    """


@base.handle_callback('uv_fs_event_cb')
def uv_fs_event_cb(fs_event_handle, c_filename, events, status):
    """
    :type fs_event_handle:
        uv.FSEvent
    :type c_filename:
        ffi.CData[char*]
    :type events:
        int
    :type status:
        int
    """
    filename = ffi.string(c_filename).decode()
    code = error.StatusCodes.get(status)
    fs_event_handle.on_event(fs_event_handle, code, filename, events)


@handle.HandleTypes.FS_EVENT
class FSEvent(handle.UVHandle):
    """
    FS event handles monitor a given filesystem path for changes
    including renaming und deletion after they have been started.
    This handle uses the best backend available for this job on
    each platform.

    :raises uv.UVError:
        error while initializing the handle

    :param path:
        directory or filename to monitor
    :param flags:
        flags to be used for monitoring
    :param loop:
        event loop the handle should run on
    :param on_event:
        callback which should be called on filesystem events after
        the handle has been started

    :type path:
        unicode
    :type flags:
        int
    :type loop:
        uv.Loop
    :type on_event:
        ((uv.FSEvent, uv.StatusCode, unicode, int) -> None) |
        ((Any, uv.FSEvent, uv.StatusCode, unicode, int) -> None)
    """

    __slots__ = ['uv_fs_event', 'on_event', 'flags', 'path']

    uv_handle_type = 'uv_fs_event_t*'
    uv_handle_init = lib.uv_fs_event_init

    def __init__(self, path=None, flags=0, loop=None, on_event=None):
        super(FSEvent, self).__init__(loop)
        self.uv_fs_event = self.base_handle.uv_object
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
        self.flags = flags
        """
        Flags to be used for monitoring.

        .. warning::
            This property is writable, however you need to restart the
            handle if you change it during the handle is active.

        :readonly:
            False
        :type:
            int
        """
        self.on_event = on_event or common.dummy_callback
        """
        Callback which should be called on filesystem events after tha
        handle has been started.


        .. function:: on_event(fs_event, status, filename, events)

            :param fs_event:
                handle the call originates from
            :param status:
                may indicate any errors
            :param filename:
                if the handle has been started with a directory this
                will be a relative path to a file contained in that
                directory which triggered the events
            :param events:
                bitmask of the triggered events

            :type fs_event:
                uv.FSEvent
            :type status:
                uv.StatusCode
            :type filename:
                unicode
            :type events:
                int


        :readonly:
            False
        :type:
            ((uv.FSEvent, uv.StatusCode, unicode, int) -> None) |
            ((Any, uv.FSEvent, uv.StatusCode, unicode, int) -> None)
        """

    def start(self, path=None, flags=None, on_event=None):
        """
        Start watching for filesystem events.

        :raises uv.UVError:
            error while starting the handle
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param path:
            directory or filename to monitor (overrides the current
            path if specified)
        :param flags:
            flags to be used for monitoring (overrides the current
            flags if specified)
        :param on_event:
            callback which should be called on filesystem events
            (overrides the current callback if specified)

        :type path:
            unicode
        :type flags:
            int
        :type on_event:
            ((uv.FSEvent, uv.StatusCode, unicode, int) -> None) |
            ((Any, uv.FSEvent, uv.StatusCode, unicode, int) -> None)
        """
        if self.closing:
            raise error.ClosedHandleError()
        self.path = path or self.path
        self.flags = flags or self.flags
        self.on_event = on_event or self.on_event
        if self.path is None:
            raise error.ArgumentError(message='no path has been specified')
        c_path = self.path.encode()
        code = lib.uv_fs_event_start(self.uv_fs_event, uv_fs_event_cb, c_path, self.flags)
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
        code = lib.uv_fs_event_stop(self.uv_fs_event)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.clear_pending()

    __call__ = start
