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

from ..common import dummy_callback
from ..error import UVError, HandleClosedError
from ..handle import HandleType, Handle
from ..request import RequestType, Request


class Buffers(tuple):
    __slots__ = []

    def __new__(cls, buffers):
        """
        :type buffers: list[bytes] | bytes
        """
        buffers = [buffers] if isinstance(buffers, bytes) else buffers
        c_buffers = [ffi.new('char[]', buf) for buf in buffers]
        uv_buffers = ffi.new('uv_buf_t[]', len(buffers))
        for index, buf in enumerate(buffers):
            uv_buffers[index].base = c_buffers[index]
            uv_buffers[index].len = len(buf)
        super(Buffers, cls).__new__((c_buffers, uv_buffers))

    @property
    def c_buffers(self):
        return self[0]

    @property
    def uv_buffers(self):
        return self[1]


@ffi.callback('uv_shutdown_cb')
def uv_shutdown_cb(uv_request, status):
    request = detach(uv_request)
    request.destroy()
    with request.loop.callback_context:
        request.on_shutdown(request, status)


@RequestType.SHUTDOWN
class ShutdownRequest(Request):
    __slots__ = ['uv_shutdown', 'stream', 'on_shutdown']

    def __init__(self, stream, on_shutdown=None):
        if stream.closing: raise HandleClosedError()
        self.uv_shutdown = ffi.new('uv_shutdown_t*')
        super(ShutdownRequest, self).__init__(self.uv_shutdown, stream.loop)
        self.stream = stream
        self.on_shutdown = on_shutdown or dummy_callback
        code = lib.uv_shutdown(self.uv_shutdown, self.uv_stream, uv_shutdown_cb)
        if code < 0: raise UVError(code)


@ffi.callback('uv_write_cb')
def uv_write_cb(uv_request, status):
    request = detach(uv_request)
    request.destroy()
    with request.loop.callback_context:
        request.on_write(request, status)


@RequestType.WRITE
class WriteRequest(Request):
    __slots__ = ['uv_write', 'buffers', 'stream', 'send_stream', 'on_write']

    def __init__(self, stream, buffers, send_stream=None, on_write=None):
        if stream.closing: raise HandleClosedError()
        self.uv_write = ffi.new('uv_write_t*')
        super(WriteRequest, self).__init__(self.uv_write, stream.loop)
        self.buffers = Buffers(buffers)
        self.stream = stream
        """
        Stream this request is running on.

        :readonly: True
        :type: uv.Stream
        """
        self.send_stream = send_stream
        """
        Stream that is being send using this request.

        :readonly: True
        :type: uv.Stream | None
        """
        self.on_write = on_write or dummy_callback
        """
        Callback called after all data has been written.

        .. function: on_write(Request, Status)

        :readonly: False
        :type: (uv.WriteRequest, uv.StatusCode) -> None
        """
        uv_stream = self.stream.uv_stream
        if send_stream is None:
            code = lib.uv_write(self.uv_write, uv_stream, self.buffers.uv_buffers,
                                len(self.buffers.uv_buffers), uv_write_cb)
        else:
            code = lib.uv_write2(self.uv_write, uv_stream, self.buffers.uv_buffers,
                                 len(self.buffers.uv_buffers), seld.send_stream.uv_stream,
                                 uv_write_cb)
        if code < 0: raise UVError(code)


@ffi.callback('uv_connect_cb')
def uv_connect_cb(uv_request, status):
    request = detach(uv_request)
    request.destroy()
    with request.loop.callback_context:
        request.on_connect(request, status)


@RequestType.CONNECT
class ConnectRequest(Request):
    __slots__ = ['uv_connect', 'on_connect']

    def __init__(self, on_connect=None):
        self.uv_connect = ffi.new('uv_connect_t*')
        super(ConnectRequest, self).__init__(self.uv_connect)
        self.on_connect = on_connect or dummy_callback

    @property
    def handle(self):
        return detach(self.uv_connect.stream)


@ffi.callback('uv_connection_cb')
def uv_connection_cb(uv_stream, status):
    stream = detach(uv_stream)
    with stream.loop.callback_context:
        stream.on_connection(stream, status)


@ffi.callback('uv_read_cb')
def uv_read_cb(uv_stream, length, uv_buf):
    stream = detach(uv_stream)
    data = stream.loop.allocator.finalize(uv_stream, length, uv_buf)
    with stream.loop.callback_context:
        stream.on_read(stream, length, data)


@HandleType.STREAM
class Stream(Handle):
    """
    Stream handles provide a duplex communication channel. This is
    the base class of all stream handles.

    :param uv_stream: allocated c struct for this stream
    :param ipc: does the stream support inter process communication
    :param loop: loop where the handle should run on

    :type uv_stream: ffi.CData
    :type ipc: bool
    :type loop: Loop
    """

    __slots__ = ['uv_stream', 'on_read', 'on_connection', 'ipc']

    def __init__(self, uv_stream, ipc=False, loop=None):
        super(Stream, self).__init__(uv_stream, loop)
        self.uv_stream = ffi.cast('uv_stream_t*', uv_stream)
        self.on_read = dummy_callback
        """
        Callback called after data was read.

        .. function:: on_read(Stream, Status, Length, Data)

        :readonly: False
        :type: (uv.Stream, uv.StatusCode, int, bytes) -> None
        """
        self.on_connection = dummy_callback
        """
        Callback called when a new connection is available.

        .. function:: on_connection(Stream, Status)

        :readonly: False
        :type: (uv.Stream, uv.StatusCode) -> None
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

        :type: bool
        """
        if self.closing: return False
        return bool(lib.uv_is_readable(self.uv_stream))

    @property
    def writable(self):
        """
        Stream is writable or not.

        :type: bool
        """
        if self.closing: return False
        return bool(lib.uv_is_writable(self.uv_stream))

    @property
    def family(self):
        """
        Address family of stream, may be None.

        :type: int | None
        """
        return None

    def shutdown(self, on_shutdown=None):
        """
        Shutdown the outgoing (write) side of a duplex stream. It waits
        for pending write requests to complete. The callback is called
        after shutdown is complete.

        .. function: on_shutdown(Stream, Status)

        :param on_shutdown: callback called after shutdown is complete
        :type on_shutdown: (uv.Stream, uv.StatusCode) -> None

        :returns: shutdown request
        :rtype: uv.ShutdownRequest
        """
        return ShutdownRequest(self, on_shutdown)

    def listen(self, backlog=5, on_connection=None):
        """
        Start listening for incoming connections.

        .. function: on_connection(Stream, Status)

        :raises uv.UVError: error while start listening for incoming connections
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param backlog: number of connections the kernel might queue
        :param on_connection: callback called when a new connection is available

        :type backlog: int
        :type on_connection: (uv.Stream, uv.StatusCode) -> None
        """
        if self.closing: raise HandleClosedError()
        self.on_connection = on_connection or self.on_connection
        code = lib.uv_listen(self.uv_stream, backlog, uv_connection_cb)
        if code < 0: raise UVError(code)

    def accept(self, cls=None, *args, **kwargs):
        """
        This method is used in conjunction with `listen()` to accept incoming
        connections. Call this method after receiving a `on_connection` event
        to accept the connection.

        When the `on_connection` callback is called it is guaranteed that
        this method will complete successfully the first time. If you attempt
        to use it more than once, it may fail. It is suggested to only call
        this method once per `on_connection` call.

        :raises uv.UVError: error while accepting incoming connection
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param cls: class of the new stream, must be a subclass of :class:`uv.Stream`
        :param args: arguments passed to the constructor of the new connection
        :param kwargs: keywords passed to the constructor of the new connection

        :type cls: type

        :return: new stream connection of type `cls`
        """
        if self.closing: raise HandleClosedError()
        connection = (cls or type(self))(*args, **kwargs)
        code = lib.uv_accept(self.uv_stream, connection.uv_stream)
        if code < 0: raise UVError(code)
        return connection

    def read_start(self, on_read=None):
        """
        Read data from an incoming stream. The `on_read` callback will be
        called several times until there is no more data to read or
        `read_stop` has been called.

        :raises uv.UVError: error while start reading from stream
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param on_read: callback called after data was read

        :type on_read: (uv.Stream, uv.StatusCode, int, bytes) -> None

        :return: new stream connection of type `cls`
        """
        if self.closing: raise HandleClosedError()
        self.on_read = on_read or self.on_read
        uv_alloc_cb = self.loop.allocator.uv_alloc_cb
        code = lib.uv_read_start(self.uv_stream, uv_alloc_cb, uv_read_cb)
        if code < 0: raise UVError(code)

    def read_stop(self):
        """
        Stop reading data from the stream. The `on_read` callback will
        no longer be called. This method is idempotent and may be safely
        called on a stopped stream.

        :raises uv.UVError: error while stop reading from stream
        """
        if self.closing: return
        code = lib.uv_read_stop(self.uv_stream)
        if code < 0: raise UVError(code)

    def write(self, buffers, send_stream=None, on_write=None):
        """
        Write data to stream. Buffers are written in order.

        If the stream supports inter process communication this method sends
        `send_stream` to the other end of the connection. `send_stream` must
        be either a TCP socket or pipe, which is a server or connection.

        :raises uv.UVError: error while creating a write request
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param buffers: buffers or buffer to send
        :param send_stream: stream to send to the other end
        :param on_write: callback called after data was written

        :type buffers: list[bytes] | bytes
        :type send_stream: uv.Stream
        :type on_write: (uv.WriteRequest, uv.StatusCode) -> None

        :returns: write request
        :rtype: uv.WriteRequest
        """
        return WriteRequest(self, buffers, send_stream, on_write)

    def try_write(self, buffers):
        """
        Same as `write()`, but won’t queue a write request if it
        cannot be completed immediately.

        :raises uv.UVError: error while writing data
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param buffers: buffers or buffer to send
        :type buffers: list[bytes] | bytes

        :return: number of bytes written
        :rtype: int
        """
        if self.closing: raise HandleClosedError()
        buffers = Buffers(buffers)
        code = lib.uv_try_write(self.uv_stream, buffers.uv_buffers, len(bufs.uv_buffers))
        if code < 0: raise UVError(code)
        return code
