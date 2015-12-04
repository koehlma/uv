# -*- coding: utf-8 -*-
#
# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals, division

from collections import namedtuple

from ..library import ffi, lib, detach

from ..common import dummy_callback
from ..error import UVError, HandleClosedError
from ..handle import HandleType, Handle
from ..request import RequestType, Request


Buffers = namedtuple('UVBuffers', ['c_buffers', 'uv_buffers'])


def create_buffers(buffers):
    buffers = [buffers] if isinstance(buffers, bytes) else buffers
    c_buffers = [ffi.new('char[]', len(buf)) for buf in buffers]
    uv_buffers = ffi.new('uv_buf_t[]', len(buffers))
    for index, buf in enumerate(buffers):
        uv_buffers[index].base = c_buffers[index]
        uv_buffers[index].len = len(buf)
    return Buffers(c_buffers, uv_buffers)


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
        self.buffers = create_buffers(buffers)
        self.stream = stream
        self.send_stream = send_stream
        self.on_write = on_write or dummy_callback
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
        Callback which should be called after data was read.

        .. function:: on_closed(Stream, Status, Length, Data)

        :readonly: False
        :type: (uv.Stream, uv.StatusCode, int, bytes) -> None
        """
        self.on_connection = dummy_callback
        """
        Callback which should be called if there is a new connection available.

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

        :type: int
        """
        return None

    def shutdown(self, on_shutdown=None):
        """
        Shutdown the outgoing (write) side of a duplex stream. It waits
        for pending write requests to complete. The callback is called
        after shutdown is complete.

        .. function: on_shutdown(Stream, Status)

        :param on_shutdown: callback which should be called after shutdown
        :type on_shutdown: (uv.Stream, uv.StatusCode) -> None
        """
        return ShutdownRequest(self, on_shutdown)

    def listen(self, backlog=5, callback=None):
        if self.closing: raise HandleClosedError()
        self.on_connection = callback or self.on_connection
        lib.uv_listen(self.uv_stream, backlog, uv_connection_cb)

    def accept(self, cls=None):
        if self.closing: raise HandleClosedError()
        connection = (cls or type(self))()
        code = lib.uv_accept(self.uv_stream, connection.uv_stream)
        if code < 0: raise UVError(code)
        return connection

    def read_start(self, on_read=None):
        if self.closing: raise HandleClosedError()
        self.on_read = on_read or self.on_read
        uv_alloc_cb = self.loop.allocator.uv_alloc_cb
        code = lib.uv_read_start(self.uv_stream, uv_alloc_cb, uv_read_cb)
        if code < 0: raise UVError(code)

    def read_stop(self):
        if self.closing: return
        code = lib.uv_read_stop(self.uv_stream)
        if code < 0: raise UVError(code)

    def write(self, buffers, send_stream=None, on_write=None):
        return WriteRequest(self, buffers, send_stream, on_write)

    def try_write(self, buffers):
        if self.closing: raise HandleClosedError()
        c_buffers, uv_buffers = create_buffers(buffers)
        code = lib.uv_try_write(self.uv_stream, uv_buffers, len(bufs.uv_buffers))
        if code < 0: raise UVError(code)
        return code
