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

from __future__ import print_function, unicode_literals, division, absolute_import

import socket

import common

import uv


class TestPipe(common.TestCase):
    def test_connect_bad(self):
        def on_connect(request, status):
            self.assert_not_equal(status, uv.StatusCodes.SUCCESS)
            request.stream.close()

        self.pipe = uv.Pipe()
        self.pipe.connect(common.BAD_PIPE, on_connect=on_connect)

        self.loop.run()

    def test_sockname(self):
        self.pipe = uv.Pipe()
        self.pipe.bind(common.TEST_PIPE1)
        self.assert_equal(self.pipe.sockname, common.TEST_PIPE1)

    def test_peername(self):
        def on_connect(request, status):
            self.assert_equal(status, uv.StatusCodes.SUCCESS)
            self.assert_equal(request.stream.peername, common.TEST_PIPE1)
            request.stream.close()

        def on_connection(handle, status):
            self.assert_equal(status, uv.StatusCodes.SUCCESS)
            handle.close()

        self.pipe1 = uv.Pipe()
        self.pipe1.bind(common.TEST_PIPE1)
        self.pipe1.listen(on_connection=on_connection)

        self.pipe2 = uv.Pipe()
        self.pipe2.connect(common.TEST_PIPE1, on_connect=on_connect)

        self.loop.run()

    def test_no_pending_accept(self):
        self.pipe = uv.Pipe()
        self.assert_raises(uv.error.ArgumentError, self.pipe.pending_accept)

    def test_closed(self):
        self.pipe = uv.Pipe()
        self.pipe.close()

        self.assert_raises(uv.error.ClosedHandleError, self.pipe.open, 0)
        self.assert_equal(self.pipe.pending_count, 0)
        self.assert_equal(self.pipe.pending_type, None)
        self.assert_raises(uv.error.ClosedHandleError, self.pipe.pending_accept)
        self.assert_raises(uv.error.ClosedHandleError, self.pipe.pending_instances, 100)
        with self.should_raise(uv.error.ClosedHandleError):
            sockname = self.pipe.sockname
        with self.should_raise(uv.error.ClosedHandleError):
            peername = self.pipe.peername
        self.assert_raises(uv.error.ClosedHandleError, self.pipe.bind, '')
        self.assert_raises(uv.error.ClosedHandleError, self.pipe.connect, '')

    def test_family(self):
        self.pipe = uv.Pipe()
        if uv.common.is_win32:
            self.assert_is(self.pipe.family, None)
        else:
            self.assert_is(self.pipe.family, socket.AF_UNIX)

    @common.skip_platform('win32')
    def test_pipe_open(self):
        unix_socket = socket.socket(family=socket.AF_UNIX)
        self.pipe = uv.Pipe()
        self.pipe.open(unix_socket.fileno())
        self.assert_equal(self.pipe.fileno(), unix_socket.fileno())
