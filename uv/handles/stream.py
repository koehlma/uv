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

from ..library import ffi, lib, detach

from ..common import dummy_callback
from ..error import UVError
from ..handle import HandleType, Handle
from ..request import RequestType, Request


@ffi.callback('uv_shutdown_cb')
def uv_shutdown_cb(uv_request, status):
    request = detach(uv_request)
    request.finish()
    with request.loop.callback_context:
        request.callback(request, status)


@ffi.callback('uv_connection_cb')
def uv_connection_cb(uv_stream, status):
    stream = detach(uv_stream)
    if stream.on_connection: stream.on_connection(stream, status)


@ffi.callback('uv_read_cb')
def uv_read_cb(uv_stream, length, buffer):
    stream = detach(uv_stream)
    data = bytes(ffi.buffer(buffer.base, length)) if length > 0 else b''
    stream.loop.allocator.release(stream)
    with stream.loop.callback_context:
        stream.on_read(stream, length, data)


@ffi.callback('uv_write_cb')
def uv_write_cb(uv_request, status):
    request = detach(uv_request)
    request.finish()
    with request.loop.callback_context:
        request.callback(request, status)


@ffi.callback('uv_connect_cb')
def uv_connect_cb(uv_request, status):
    request = detach(uv_request)
    request.handle.requests.remove(request)
    if request.callback: request.callback(request, status)


@RequestType.SHUTDOWN
class ShutdownRequest(Request):
    __slots__ = ['uv_shutdown', 'callback']

    def __init__(self, callback=None):
        self.uv_shutdown = ffi.new('uv_shutdown_t*')
        super(ShutdownRequest, self).__init__(self.uv_shutdown)
        self.callback = callback or dummy_callback

    @property
    def handle(self):
        return detach(self.uv_shutdown.handle)


@RequestType.WRITE
class WriteRequest(Request):
    __slots__ = ['uv_write', 'uv_buffers', 'callback']

    def __init__(self, uv_buffers, callback=None, loop=None):
        self.uv_write = ffi.new('uv_write_t*')
        self.uv_buffers = uv_buffers
        self.callback = callback or dummy_callback
        super(WriteRequest, self).__init__(self.uv_write)

    @property
    def handle(self):
        return detach(self.uv_write.handle)

    @property
    def send_handle(self):
        return detach(self.uv_write.send_handle)


@RequestType.CONNECT
class ConnectRequest(Request):
    __slots__ = ['uv_connect', 'callback']

    def __init__(self, callback=None):
        self.uv_connect = ffi.new('uv_connect_t*')
        self.callback = callback or dummy_callback
        super(ConnectRequest, self).__init__(self.uv_connect)

    @property
    def handle(self):
        return detach(self.uv_connect.handle)


@HandleType.STREAM
class Stream(Handle):
    __slots__ = ['uv_stream', 'on_read', 'on_connection', 'ipc', 'requests']

    def __init__(self, stream, loop=None, ipc=False):
        super(Stream, self).__init__(stream, loop)
        self.uv_stream = ffi.cast('uv_stream_t*', stream)
        self.on_read = dummy_callback
        self.on_connection = dummy_callback
        self.ipc = ipc

    @property
    def readable(self):
        return bool(lib.uv_is_readable(self.uv_stream))

    @property
    def writable(self):
        return bool(lib.uv_is_writable(self.uv_stream))

    @property
    def family(self):
        return None

    def shutdown(self, callback=None):
        request = ShutdownRequest(callback)
        lib.uv_shutdown(request.uv_shutdown, self.uv_stream, uv_shutdown_cb)
        return request

    def listen(self, backlog=5, callback=None):
        self.on_connection = callback or self.on_connection
        lib.uv_listen(self.uv_stream, backlog, uv_connection_cb)

    def accept(self, cls=None):
        connection = (cls or type(self))()
        code = lib.uv_accept(self.uv_stream, connection.uv_stream)
        if code < 0: raise UVError(code)
        return connection

    def read_start(self, callback=None):
        self.on_read = callback or self.on_read
        uv_alloc_cb = self.loop.allocator.uv_alloc_cb
        code = lib.uv_read_start(self.uv_stream, uv_alloc_cb, uv_read_cb)
        if code < 0: raise UVError(code)

    def read_stop(self):
        code = lib.uv_read_stop(self.uv_stream)
        if code < 0: raise UVError(code)

    def write(self, c_data, callback=None, stream=None):
        c_buffers = ffi.new('uv_buf_t[1]')
        c_data = ffi.new('char[%d]' % len(c_data), c_data)
        c_buffers[0].base = c_data
        c_buffers[0].len = len(c_data)
        request = WriteRequest([(c_buffers, c_data)], callback, self.loop)
        if stream is None:
            lib.uv_write(request.uv_write, self.uv_stream, c_buffers, 1, uv_write_cb)
        else:
            lib.uv_write2(request.uv_write, self.uv_stream, c_buffers, 1,
                          stream.stream, uv_write_cb)
        return request

    def try_write(self, data):
        buffer = ffi.new('uv_buf_t[1]')
        data = ffi.new('char[]', data)
        buffer[0].base = data
        buffer[0].len = len(data)
        code = lib.uv_try_write(self.uv_stream, buffer, 1)
        if code < 0: raise UVError(code)
        return code
