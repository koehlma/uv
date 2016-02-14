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

from .. import base, common, error, handle, library, request
from ..library import ffi, lib


@base.request_callback('uv_shutdown_cb')
def uv_shutdown_cb(shutdown_request, status):
    """
    :type shutdown_request:
        uv.ShutdownRequest
    :type status:
        int
    """
    shutdown_request.on_shutdown(shutdown_request, error.StatusCodes.get(status))


@request.RequestType.SHUTDOWN
class ShutdownRequest(request.Request):
    """
    Request to shutdown the outgoing side of a duplex stream. It waits
    for pending write requests to complete.
    """

    __slots__ = ['uv_shutdown', 'stream', 'on_shutdown']

    uv_request_type = 'uv_shutdown_t*'
    uv_request_init = lib.uv_shutdown

    def __init__(self, stream, on_shutdown=None):
        """
        :raises uv.UVError:
            error while initializing the request
        :raises uv.ClosedHandleError:
            stream has already been closed or is closing

        :param stream:
            stream to shutdown
        :param on_shutdown:
            callback which should run after shutdown has been completed

        :type stream:
            uv.Stream
        :type on_shutdown:
            ((uv.ShutdownRequest, uv.StatusCodes) -> None) |
            ((Any, uv.ShutdownRequest, uv.StatusCodes) -> None)
        """
        if stream.closing:
            raise error.ClosedHandleError()
        self.stream = stream
        """
        Stream to shutdown.

        :readonly:
            True
        :type:
            uv.Stream
        """
        self.on_shutdown = on_shutdown or common.dummy_callback
        """
        Callback which should run after shutdown has been completed.


        .. function:: on_shutdown(shutdown_request, status)

            :param shutdown_request:
                request the call originates from
            :param status:
                status of the shutdown request

            :type shutdown_request:
                uv.ShutdownRequest
            :type status:
                uv.StatusCodes


        :readonly:
            False
        :type:
            ((uv.ShutdownRequest, uv.StatusCodes) -> None) |
            ((Any, uv.ShutdownRequest, uv.StatusCodes) -> None)
        """
        arguments = uv_shutdown_cb,
        super(ShutdownRequest, self).__init__(stream.loop, arguments, stream.uv_stream)


@base.request_callback('uv_write_cb')
def uv_write_cb(write_request, status):
    """
    :type write_request:
        uv.WriteRequest
    :type status:
        int
    """
    write_request.on_write(write_request, error.StatusCodes.get(status))


@request.RequestType.WRITE
class WriteRequest(request.Request):
    """
    Request to write data to a stream and, on streams with inter
    process communication support, to send stream handles. Buffers
    are written in the given order.
    """

    __slots__ = ['uv_buffers', 'stream', 'send_stream', 'on_write']

    uv_request_type = 'uv_write_t*'

    def __init__(self, stream, buffers, send_stream=None, on_write=None):
        """
        :raises uv.UVError:
            error while initializing the request
        :raises uv.ClosedHandleError:
            stream has already been closed or is closing

        :param stream:
            stream to write data to
        :param buffers:
            data which should be written
        :param send_stream:
            stream handle which should be send
        :param on_write:
            callback which should run after all data has been written

        :type stream:
            uv.Stream
        :type buffers:
            tuple[bytes] | list[bytes] | bytes
        :type send_stream:
            uv.TCP | uv.Pipe | None
        :type on_write:
            ((uv.WriteRequest, uv.StatusCodes) -> None) |
            ((Any, uv.WriteRequest, uv.StatusCodes) -> None)
        """
        if stream.closing:
            raise error.ClosedHandleError()
        self.uv_buffers = library.make_uv_buffers(buffers)
        self.stream = stream
        """
        Stream to write data to.

        :readonly:
            True
        :type:
            uv.Stream
        """
        self.send_stream = send_stream
        """
        Stream handle which should be send.

        :readonly:
            True
        :type:
            uv.Stream | None
        """
        self.on_write = on_write or common.dummy_callback
        """
        Callback which should run after all data has been written.


        .. function: on_write(write_request, status)

            :param write_request:
                request the call originates from
            :param status:
                status of the write request

            :type write_request:
                uv.WriteRequest
            :type status:
                uv.StatusCodes


        :readonly:
            False
        :type:
            ((uv.WriteRequest, uv.StatusCodes) -> None) |
            ((Any, uv.WriteRequest, uv.StatusCodes) -> None)
        """
        amount = len(self.uv_buffers)
        if send_stream is None:
            arguments = self.uv_buffers, amount, uv_write_cb
            init = lib.uv_write
        else:
            arguments = self.uv_buffers, amount, self.send_stream.uv_stream, uv_write_cb
            init = lib.uv_write2
        super(WriteRequest, self).__init__(stream.loop, arguments, stream.uv_stream, init)


@base.request_callback('uv_connect_cb')
def uv_connect_cb(connect_request, status):
    """
    :type connect_request:
        uv.ConnectRequest
    :param status:
        int
    """
    connect_request.on_connect(connect_request, error.StatusCodes.get(status))


@request.RequestType.CONNECT
class ConnectRequest(request.Request):
    """
    Request to connect to a specific address.

    .. note::
        There is a specific connect request type for every stream type.
    """

    __slots__ = ['stream', 'on_connect']

    uv_request_type = 'uv_connect_t*'

    def __init__(self, stream, arguments, on_connect=None):
        """
        :param stream:
            stream to establish a connection on
        :param on_connect:
            callback which should run after a connection has been
            established or on error

        :type stream:
            uv.Stream
        :type on_connect:
            ((uv.ConnectRequest, uv.StatusCodes) -> None) |
            ((Any, uv.ConnectRequest, uv.StatusCodes) -> None)
        """
        if stream.closing:
            raise error.ClosedHandleError()
        uv_handle = stream.base_handle.uv_object
        arguments = arguments + (uv_connect_cb, )
        super(ConnectRequest, self).__init__(stream.loop, arguments, uv_handle)
        self.stream = stream
        """
        Stream to establish a connection on.

        :readonly:
            True
        :type:
            uv.Stream
        """
        self.on_connect = on_connect or common.dummy_callback
        """
        Callback which should run after a connection has been
        established.


        .. function: on_connect(connect_request, status)

            :param connect_request:
                request the call originates from
            :param status:
                status of the connect request

            :type connect_request:
                uv.ConnectRequest
            :type status:
                uv.StatusCodes


        :readonly:
            False
        :type:
            ((uv.ConnectRequest, uv.StatusCodes) -> None) |
            ((Any, uv.ConnectRequest, uv.StatusCodes) -> None)
        """


@base.handle_callback('uv_connection_cb')
def uv_connection_cb(stream_handle, status):
    """
    :type stream_handle:
        uv.Stream
    :type status:
        int
    """
    stream_handle.on_connection(stream_handle, error.StatusCodes.get(status))


@base.handle_callback('uv_read_cb')
def uv_read_cb(stream_handle, length, uv_buffer):
    """
    :type stream_handle:
        uv.Stream
    :type length:
        int
    :type uv_buffer:
        ffi.CData[uv_buf_t*]
    """
    data = stream_handle.loop.allocator.finalize(stream_handle, length, uv_buffer)
    if length < 0:  # pragma: no cover
        status = error.StatusCodes.get(length)
        data = b''
    else:
        status = error.StatusCodes.SUCCESS
    stream_handle.on_read(stream_handle, status, data)


@handle.HandleTypes.STREAM
class Stream(handle.Handle):
    """
    Stream handles provide a reliable ordered duplex communication
    channel. This is the base class of all stream handles.

    .. note::
        This class must not be instantiated directly. Please use the
        sub-classes for specific communication channels.
    """

    __slots__ = ['uv_stream', 'on_read', 'on_connection', 'ipc']

    def __init__(self, loop, ipc, arguments, on_read, on_connection):
        """
        :param loop:
            event loop the handle should run on
        :param ipc:
            stream should support inter process communication or not
        :param arguments:
            arguments passed to the underling libuv initializer
        :param on_read:
            callback which should be called when data has been read
        :param on_connection:
            callback which should run after a new connection has been
            made or on error (if stream is in listen mode)

        :type loop:
            uv.Loop
        :type ipc:
            bool
        :type arguments:
            tuple
        :type on_read:
            ((uv.Stream, uv.StatusCodes, bytes) -> None) |
            ((Any, uv.Stream, uv.StatusCodes, bytes) -> None)
        :type on_connection:
            ((uv.Stream, uv.StatusCodes, bytes) -> None) |
            ((Any, uv.Stream, uv.StatusCodes, bytes) -> None)
        """
        super(Stream, self).__init__(loop, arguments)
        self.uv_stream = ffi.cast('uv_stream_t*', self.base_handle.uv_object)
        self.on_read = on_read or common.dummy_callback
        """
        Callback which should be called when data has been read.

        .. note::
            Data might be a zero-bytes long bytes object. In contrast
            to the Python standard library this does not indicate any
            error, especially not `EOF`.


        .. function:: on_read(stream_handle, status, data)

            :param stream_handle:
                handle the call originates from
            :param status:
                status of the handle (indicate any errors)
            :param data:
                data which has been read

            :type stream_handle:
                uv.Stream
            :type status:
                uv.StatusCodes
            :type data:
                bytes | Any


        :readonly:
            False
        :type:
            ((uv.Stream, uv.StatusCodes, bytes) -> None) |
            ((Any, uv.Stream, uv.StatusCodes, bytes) -> None)
        """
        self.on_connection = on_connection or common.dummy_callback
        """
        Callback which should run after a new connection has been made
        or on error (if stream is in listen mode).


        .. function:: on_connection(stream_handle, status)

            :param stream_handle:
                handle the call originates from
            :param status:
                status of the new connection

            :type stream_handle:
                uv.Stream
            :type status:
                uv.StatusCodes


        :readonly:
            False
        :type:
            ((uv.Stream, uv.StatusCodes, uv.Stream) -> None) |
            ((Any, uv.Stream, uv.StatusCodes, uv.Stream) -> None)
        """
        self.ipc = ipc
        """
        Stream does support inter process communication or not.

        :readonly:
            True
        :type:
            bool
        """

    @property
    def readable(self):
        """
        Stream is readable or not.

        :readonly:
            True
        :type:
            bool
        """
        if self.closing:
            return False
        return bool(lib.uv_is_readable(self.uv_stream))

    @property
    def writable(self):
        """
        Stream is writable or not.

        :readonly:
            True
        :type:
            bool
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
        raise NotImplemented()

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
            uv.ShutdownRequest
        """
        return ShutdownRequest(self, on_shutdown)

    def listen(self, backlog=5, on_connection=None):
        """
        Start listening for incoming connections.

        :raises uv.UVError:
            error while start listening for incoming connections
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param backlog:
            number of connections the kernel might queue
        :param on_connection:
            callback which should run after a new connection has been
            made (overrides the current callback if specified)

        :type backlog:
            int
        :type on_connection:
            ((uv.Stream, uv.StatusCodes) -> None) |
            ((Any, uv.Stream, uv.StatusCodes) -> None)
        """
        if self.closing:
            raise error.ClosedHandleError()
        self.on_connection = on_connection or self.on_connection
        code = lib.uv_listen(self.uv_stream, backlog, uv_connection_cb)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

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
        if self.closing:
            raise error.ClosedHandleError()
        self.on_read = on_read or self.on_read
        code = lib.uv_read_start(self.uv_stream, handle.uv_alloc_cb, uv_read_cb)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.set_pending()

    def read_stop(self):
        """
        Stop reading data from the stream. The read callback will no
        longer be called from now on.

        :raises uv.UVError:
            error while stop reading data from the stream
        """
        if self.closing:
            return
        code = lib.uv_read_stop(self.uv_stream)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.clear_pending()

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
            ((uv.WriteRequest, uv.StatusCodes) -> None) |
            ((Any, uv.WriteRequest, uv.StatusCodes) -> None)

        :returns:
            issued write request
        :rtype:
            uv.WriteRequest
        """
        return WriteRequest(self, buffers, send_stream, on_write)

    def try_write(self, buffers):
        """
        Immediately write data to the stream without issuing a write
        request. Throws :class:`uv.error.TemporaryUnavailableError` if
        data could not be written immediately, otherwise it returns the
        number of written bytes.

        :raises uv.UVError:
            error while writing data
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing
        :raises uv.error.TemporaryUnavailableError:
            unable to write data immediately

        :param buffers:
            data which should be written
        :type buffers:
            tuple[bytes] | list[bytes] | bytes

        :return:
            number of bytes written
        :rtype:
            int
        """
        if self.closing:
            raise error.ClosedHandleError()
        uv_buffers = library.make_uv_buffers(buffers)
        code = lib.uv_try_write(self.uv_stream, uv_buffers, len(uv_buffers))
        if code < 0:  # pragma: no cover
            raise error.UVError(code)
        return code

    def accept(self, cls=None, *arguments, **keywords):
        """
        Accept a new stream. This might be a new client connection or a
        stream sent by inter process communication.

        .. warning::
            There should be no need to use this method directly, it is
            mainly for internal purposes.

        :raises uv.UVError:
            error while accepting incoming stream
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param cls:
            type of the new stream
        :param arguments:
            arguments passed to the constructor of the new stream
        :param keywords:
            keywords passed to the constructor of the new stream

        :type cls:
            type
        :type arguments:
            tuple
        :type keywords:
            dict

        :return:
            new stream connection of type `cls`
        :rtype:
            uv.Stream
        """
        if self.closing:
            raise error.ClosedHandleError()
        connection = (cls or type(self))(*arguments, **keywords)
        code = lib.uv_accept(self.uv_stream, connection.uv_stream)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        return connection
