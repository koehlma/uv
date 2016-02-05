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

from .. import base, common, error, handle, loop, request
from ..library import ffi, lib

__all__ = ['ShutdownRequest', 'ConnectRequest', 'WriteRequest', 'Stream']


@base.request_callback('uv_shutdown_cb')
def uv_shutdown_cb(shutdown_request, status):
    """
    :type shutdown_request:
        ShutdownRequest
    :type status:
        int
    """
    shutdown_request.on_shutdown(shutdown_request, status)


@request.RequestType.SHUTDOWN
class ShutdownRequest(request.Request):
    """
    Shutdown request.

    :raises uv.UVError: error while initializing the request
    :raises uv.ClosedHandleError: stream has already been closed or is closing

    :param stream: stream to shutdown
    :param on_shutdown: callback called after shutdown has been completed

    :type stream: uv.Stream
    :type on_shutdown: ((uv.ShutdownRequest, uv.StatusCode) -> None) |
                       ((Any, uv.ShutdownRequest, uv.StatusCode) -> None)
    """

    __slots__ = ['uv_shutdown', 'stream', 'on_shutdown']

    uv_request_type = 'uv_shutdown_t*'
    uv_request_init = lib.uv_shutdown

    def __init__(self, stream, on_shutdown=None):
        if stream.closing: raise error.ClosedHandleError()
        self.stream = stream
        """
        Stream this request belongs to.

        :readonly: True
        :type: uv.Stream
        """
        self.on_shutdown = on_shutdown or common.dummy_callback
        """
        Callback called after shutdown has been completed.

        .. function:: on_shutdown(Shutdown-Request, Status)

        :readonly: False
        :type: ((uv.ShutdownRequest, uv.StatusCode) -> None) |
               ((Any, uv.ShutdownRequest, uv.StatusCode) -> None)
        """
        super(ShutdownRequest, self).__init__(stream.loop, uv_shutdown_cb,
                                              uv_handle=stream.uv_stream)


@base.request_callback('uv_write_cb')
def uv_write_cb(write_request, status):
    """
    :type write_request:
        WriteRequest
    :type status:
        int
    """
    write_request.on_write(write_request, status)


@request.RequestType.WRITE
class WriteRequest(request.Request):
    """
    Write request.

    :raises uv.UVError: error while initializing the request
    :raises uv.ClosedHandleError: stream has already been closed or is closing

    :param stream: stream to write to
    :param buffers: data to write
    :param send_stream: stream handle to send
    :param on_write: callback called after all data has been written

    :type stream: uv.Stream
    :type buffers: list[bytes] | bytes
    :type send_stream: uv.Stream
    :type on_write: ((uv.WriteRequest, uv.StatusCode) -> None) |
                    ((Any, uv.WriteRequest, uv.StatusCode) -> None)
    """

    __slots__ = ['uv_write', 'buffers', 'stream', 'send_stream', 'on_write']

    uv_request_type = 'uv_write_t*'

    def __init__(self, stream, buffers, send_stream=None, on_write=None):
        if stream.closing:
            raise error.ClosedHandleError()
        self.buffers = common.Buffers(buffers)
        self.stream = stream
        """
        Stream this request belongs to.

        :readonly: True
        :type: uv.Stream
        """
        self.send_stream = send_stream
        """
        Stream that is being send using this request.

        :readonly: True
        :type: uv.Stream | None
        """
        self.on_write = on_write or common.dummy_callback
        """
        Callback called after all data has been written.

        .. function: on_write(Write-Request, Status)

        :readonly: False
        :type: ((uv.WriteRequest, uv.StatusCode) -> None) |
               ((Any, uv.WriteRequest, uv.StatusCode) -> None)
        """
        c_buffers, uv_buffers = self.buffers
        if send_stream is None:
            super(WriteRequest, self).__init__(stream.loop, uv_buffers,
                                               len(self.buffers), uv_write_cb,
                                               uv_handle=stream.uv_stream,
                                               request_init=lib.uv_write)
        else:
            super(WriteRequest, self).__init__(stream.loop, uv_buffers,
                                               len(self.buffers),
                                               self.send_stream.uv_stream, uv_write_cb,
                                               uv_handle=stream.uv_stream,
                                               request_init=lib.uv_write2)
        self.uv_write = self.base_request.uv_object


@base.request_callback('uv_connect_cb')
def uv_connect_cb(connect_request, status):
    connect_request.on_connect(connect_request, status)


@request.RequestType.CONNECT
class ConnectRequest(request.Request):
    """
    Connect request.

    .. warning::

        This request cannot be used directly. Please use the stream's
        `connect` method to establish a connection.

    :param stream: stream to write to
    :param on_connect: callback called after connection has been established

    :type stream: uv.Stream
    :type on_connect: ((uv.ConnectRequest, uv.StatusCode) -> None) |
                      ((Any, uv.ConnectRequest, uv.StatusCode) -> None)
    """

    __slots__ = ['stream', 'on_connect']

    uv_request_type = 'uv_connect_t*'

    def __init__(self, stream, *arguments, **keywords):
        on_connect = keywords.get('on_connect')
        if stream.closing:
            raise error.ClosedHandleError()
        super(ConnectRequest, self).__init__(stream.loop, *(arguments + (uv_connect_cb,)),
                                             uv_handle=stream.base_handle.uv_object)
        self.stream = stream
        """
        Stream this request belongs to.

        :readonly: True
        :type: uv.Stream
        """
        self.on_connect = on_connect or common.dummy_callback
        """
        Callback called after connection has been established.

        .. function: on_connect(Connect-Request, Status)

        :readonly: False
        :type: ((uv.ConnectRequest, uv.StatusCode) -> None) |
               ((Any, uv.ConnectRequest, uv.StatusCode) -> None)
        """


@base.handle_callback('uv_connection_cb')
def uv_connection_cb(stream_handle, status):
    stream_handle.on_connection(stream_handle, status)


@base.handle_callback('uv_read_cb')
def uv_read_cb(stream_handle, length, uv_buffer):
    data = stream_handle.loop.allocator.finalize(stream_handle, length, uv_buffer)
    if length < 0:
        length, status = 0, length
    else:
        status = error.StatusCodes.SUCCESS
    stream_handle.on_read(stream_handle, status, length, data)


@handle.HandleTypes.STREAM
class Stream(handle.Handle):
    """
    Stream handles provide a duplex communication channel. This is
    the base class of all stream handles.

    :param uv_stream: allocated c struct for this stream
    :param ipc: does the stream support inter process communication
    :param loop: event loop the handle should run on

    :type uv_stream: ffi.CData
    :type ipc: bool
    :type loop: uv.Loop
    """

    __slots__ = ['uv_stream', 'on_read', 'on_connection', 'ipc']

    def __init__(self, loop, ipc, arguments):
        super(Stream, self).__init__(loop, arguments)
        self.uv_stream = ffi.cast('uv_stream_t*', self.base_handle.uv_object)
        self.on_read = common.dummy_callback
        """
        Callback called after data was read.

        .. function:: on_read(Stream, Status, Length, Data)

        :readonly: False
        :type: ((uv.Stream, uv.StatusCode, int, bytes) -> None) |
               ((Any, uv.Stream, uv.StatusCode, int, bytes) -> None)
        """
        self.on_connection = common.dummy_callback
        """
        Callback called when a new connection is available.

        .. function:: on_connection(Stream, Status)

        :readonly: False
        :type: ((uv.Stream, uv.StatusCode) -> None) |
               ((Any, uv.Stream, uv.StatusCode) -> None)
        """
        self.ipc = ipc
        """
        Stream supports inter process communication or not.

        :readonly: True
        :type: bool
        """

    @property
    def readable(self):
        """
        Stream is readable or not.

        :readonly: True
        :type: bool
        """
        if self.closing:
            return False
        return bool(lib.uv_is_readable(self.uv_stream))

    @property
    def writable(self):
        """
        Stream is writable or not.

        :readonly: True
        :type: bool
        """
        if self.closing:
            return False
        return bool(lib.uv_is_writable(self.uv_stream))

    @property
    def family(self):
        """
        Address family of stream, may be None.

        :rtype: int | None
        """
        return None

    def shutdown(self, on_shutdown=None):
        """
        Shutdown the outgoing (write) side of a duplex stream. It waits
        for pending write requests to complete. The callback is called
        after shutdown is complete.

        .. function: on_shutdown(Stream, Status)

        :param on_shutdown: callback called after shutdown is complete
        :type on_shutdown: ((uv.ShutdownRequest, uv.StatusCode) -> None) |
                           ((Any, uv.ShutdownRequest, uv.StatusCode) -> None)

        :returns: shutdown request
        :rtype: uv.ShutdownRequest
        """
        return ShutdownRequest(self, on_shutdown)

    def listen(self, backlog=5, on_connection=None):
        """
        Start listening for incoming connections.

        .. function: on_connection(Stream, Status)

        :raises uv.UVError: error while start listening for incoming connections
        :raises uv.ClosedHandleError: handle has already been closed or is closing

        :param backlog: number of connections the kernel might queue
        :param on_connection: callback called when a new connection is available

        :type backlog: int
        :type on_connection: ((uv.Stream, uv.StatusCode) -> None) |
                             ((Any, uv.Stream, uv.StatusCode) -> None
        """
        if self.closing:
            raise error.ClosedHandleError()
        self.on_connection = on_connection or self.on_connection
        code = lib.uv_listen(self.uv_stream, backlog, uv_connection_cb)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def accept(self, cls=None, *args, **kwargs):
        """
        This method is used in conjunction with :func:`Stream.listen` to accept
        incoming connections. Call this method after receiving a `on_connection`
        event to accept the connection.

        When the `on_connection` callback is called it is guaranteed that
        this method will complete successfully the first time. If you attempt
        to use it more than once, it may fail. It is suggested to only call
        this method once per `on_connection` call.

        :raises uv.UVError: error while accepting incoming connection
        :raises uv.ClosedHandleError: handle has already been closed or is closing

        :param cls: class of the new stream, must be a subclass of :class:`uv.Stream`
        :param args: arguments passed to the constructor of the new connection
        :param kwargs: keywords passed to the constructor of the new connection

        :type cls: type

        :return: new stream connection of type `cls`
        """
        if self.closing:
            raise error.ClosedHandleError()
        connection = (cls or type(self))(*args, **kwargs)
        code = lib.uv_accept(self.uv_stream, connection.uv_stream)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        return connection

    def read_start(self, on_read=None):
        """
        Read data from an incoming stream. The `on_read` callback will be
        called several times until there is no more data to read or
        `read_stop` has been called.

        :raises uv.UVError: error while start reading from stream
        :raises uv.ClosedHandleError: handle has already been closed or is closing

        :param on_read: callback called after data was read
        :type on_read: ((uv.Stream, uv.StatusCode, int, bytes) -> None) |
                       ((Any, uv.Stream, uv.StatusCode, int, bytes) -> None)
        """
        if self.closing:
            raise error.ClosedHandleError()
        self.on_read = on_read or self.on_read
        code = lib.uv_read_start(self.uv_stream, loop.uv_alloc_cb, uv_read_cb)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.set_pending()

    def read_stop(self):
        """
        Stop reading data from the stream. The `on_read` callback will
        no longer be called. This method is idempotent and may be safely
        called on a stopped stream.

        :raises uv.UVError: error while stop reading from stream
        """
        if self.closing:
            return
        code = lib.uv_read_stop(self.uv_stream)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.clear_pending()

    def write(self, buffers, send_stream=None, on_write=None):
        """
        Write data to stream. Buffers are written in order.

        If the stream supports inter process communication this method sends
        `send_stream` to the other end of the connection. `send_stream` must
        be either a TCP socket or pipe, which is a server or connection.

        :raises uv.UVError: error while creating a write request
        :raises uv.ClosedHandleError: handle has already been closed or is closing

        :param buffers: buffers or buffer to send
        :param send_stream: stream to send to the other end
        :param on_write: callback called after data was written

        :type buffers: list[bytes] | bytes
        :type send_stream: uv.Stream
        :type on_write: ((uv.WriteRequest, uv.StatusCode) -> None) |
                        ((Any, uv.WriteRequest, uv.StatusCode) -> None)

        :returns: write request
        :rtype: uv.WriteRequest
        """
        return WriteRequest(self, buffers, send_stream, on_write)

    def try_write(self, buffers):
        """
        Same as `write()`, but won’t queue a write request if it
        cannot be completed immediately.

        :raises uv.UVError: error while writing data
        :raises uv.ClosedHandleError: handle has already been closed or is closing

        :param buffers: buffers or buffer to send
        :type buffers: list[bytes] | bytes

        :return: number of bytes written
        :rtype: int
        """
        if self.closing:
            raise error.ClosedHandleError()
        buffers = Buffers(buffers)
        code = lib.uv_try_write(self.uv_stream, buffers.uv_buffers, len(buffers))
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        return code
