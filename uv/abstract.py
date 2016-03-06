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

"""
This module contains abstract base classes to be implemented by various
types of objects. This allows to implement streams and other types of
libuv objects in pure python.
"""

from __future__ import print_function, unicode_literals, division, absolute_import

import abc

from . import common


class Handle(common.with_metaclass(abc.ABCMeta)):
    """
    Handles represent long-lived objects capable of performing certain
    operations while active. This is the abstract base class of all
    internal libuv and pure Python handles.

    .. note::
        Handles underlie a special garbage collection strategy which
        means they are not garbage collected as other objects. If a
        handle is able to do anything in the program for example
        calling a callback they are not garbage collected.
    """
    @abc.abstractproperty
    def loop(self):
        """
        Loop the handle is running on.

        :readonly:
            True
        :rtype:
            uv.Loop
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def closing(self):
        """
        Handle is already closed or is closing. This is `True` right
        after close has been called. Operations on a closed or closing
        handle will raise :class:`uv.ClosedHandleError`.

        :readonly:
            True
        :rtype:
            bool
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def closed(self):
        """
        Handle has been closed. This is `True` right after the close
        callback has been called. It means all internal resources are
        freed and this handle is ready to be garbage collected.

        :readonly:
            True
        :rtype:
            bool
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def active(self):
        """
        Handle is active or not. What "active" means depends on the
        handle type:

        :class:`uv.Async`:
            is always active and cannot be deactivated

        :class:`uv.Pipe`, :class:`uv.TCP`, :class:`uv.UDP`, …:
            basically any handle dealing with IO is active when it is
            doing something involves IO like reading, writing,
            connecting or listening

        :class:`uv.Check`, :class:`uv.Idle`, :class:`uv.Timer`, …:
            handle is active when it has been started and not yet
            stopped

        :readonly:
            True
        :type:
            bool
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def referenced(self):
        """
        Handle is referenced or not. If the event loop runs in default
        mode it will exit when there are no more active and referenced
        handles left. This has nothing to do with CPython's reference
        counting.

        :readonly:
            False
        :type:
            bool
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def reference(self):
        """
        Reference the handle. If the event loop runs in default mode
        it will exit when there are no more active and referenced
        handles left. This has nothing to do with CPython's reference
        counting. References are idempotent, that is, if a handle is
        referenced calling this method again will have not effect.

        :raises uv.ClosedHandleError:
            handle has already been closed or is closing
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def dereference(self):
        """
        Dereference the handle. If the event loop runs in default mode
        it will exit when there are no more active and referenced
        handles left. This has nothing to do with CPython's reference
        counting. References are idempotent, that is, if a handle is
        not referenced calling this method again will have not effect.

        :raises uv.ClosedHandleError:
            handle has already been closed or is closing
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def close(self, on_closed=None):
        """
        Close the handle. Please make sure to call this method on any
        handle you do not need anymore. This method is idempotent, that
        is, if the handle is already closed or is closing calling it
        will have no effect at all.

        In-progress requests, like connect or write requests, are
        cancelled and have their callbacks called asynchronously with
        :class:`uv.StatusCodes.ECANCELED`.

        After this method has been called on a handle no operations can
        be performed on it (they raise :class:`uv.ClosedHandleError`).

        .. note::
            Handles are automatically closed when they are garbage
            collected. However because the exact time this happens is
            non-deterministic you should close all handles explicitly.
            Especially if they handle external resources.

        :param on_closed:
            callback which should run after the handle has been closed
            (overrides the current callback if specified)

        :type on_closed:
            ((uv.Handle) -> None) | ((Any, uv.Handle) -> None)
        """
        raise NotImplementedError()


class Request(common.with_metaclass(abc.ABCMeta)):
    """
    Requests represent (typically) short-lived operations. These operations
    can be performed over a handle: write requests are used to write data
    on a handle; or standalone: getaddrinfo requests don’t need a handle
    they run directly on the loop. This is the abstract base class of all
    internal libuv and pure Python requests.
    """

    @abc.abstractmethod
    def cancel(self):
        """
        Cancel a pending request. Fails if the request is executing
        or has finished executing.
        """
        raise NotImplementedError()


class Stream(Handle):
    """
    Stream handles provide a reliable ordered duplex communication
    channel. This is the abstract base class of all stream handles.
    """

    @abc.abstractproperty
    def readable(self):
        """
        Stream is readable or not.

        :readonly:
            True
        :type:
            bool
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def writeable(self):
        """
        Stream is writable or not.

        :readonly:
            True
        :type:
            bool
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def read_start(self, on_read=None):
        """
        Start reading data from the stream. The read callback will be
        called from now on when data has been read.

        :raises uv.UVError:
            error while start reading data from the stream
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param on_read:
            callback which should be called when data has been read
            (overrides the current callback if specified)

        :type on_read:
            ((uv.Stream, uv.StatusCodes, bytes) -> None) |
            ((Any, uv.Stream, uv.StatusCodes, bytes) -> None)
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def read_stop(self):
        """
        Stop reading data from the stream. The read callback will no
        longer be called from now on.

        :raises uv.UVError:
            error while stop reading data from the stream
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def write(self, buffers, send_stream=None, on_write=None):
        """
        Write data to stream. Buffers are written in the given order.

        If `send_stream` is not `None` and the stream supports inter
        process communication this method sends `send_stream` to the
        other end of the connection.

        :param buffers:
            data which should be written
        :param send_stream:
            stream handle which should be send
        :param on_write:
            callback which should run after all data has been written

        :type buffers:
            tuple[bytes] | list[bytes] | bytes
        :type send_stream:
            uv.TCP | uv.Pipe | None
        :type on_write:
            ((uv.Request, uv.StatusCodes) -> None) |
            ((Any, uv.Request, uv.StatusCodes) -> None)

        :returns:
            issued write request
        :rtype:
            uv.Request
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def shutdown(self, on_shutdown=None):
        """
        Shutdown the outgoing (write) side of a duplex stream. It waits
        for pending write requests to complete.

        :param on_shutdown:
            callback which should run after shutdown has been completed

        :type on_shutdown:
            ((uv.ShutdownRequest, uv.StatusCodes) -> None) |
            ((Any, uv.ShutdownRequest, uv.StatusCodes) -> None)

        :returns:
            issued stream shutdown request
        :rtype:
            uv.Request
        """
        raise NotImplementedError()
