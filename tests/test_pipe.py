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

import os

from common import TestCase

import uv

if uv.is_win32:
    TEST_PIPE1 = '\\\\?\\pipe\\python-uv-test1'
    TEST_PIPE2 = '\\\\?\\pipe\\python-uv-test2'
else:
    TEST_PIPE1 = '/tmp/python-uv-test1'
    TEST_PIPE2 = '/tmp/python-uv-test2'

BAD_PIPE = '/path/to/unix/socket/that/really/should/not/be/there'


class TestPipe(TestCase):
    def tear_down(self):
        try: os.remove(TEST_PIPE1)
        except: pass
        try: os.remove(TEST_PIPE2)
        except: pass

    def test_connect_bad(self):
        def on_connect(request, status):
            self.assert_not_equal(status, uv.StatusCode.SUCCESS)
            request.stream.close()

        self.pipe = uv.Pipe()
        self.pipe.connect(BAD_PIPE, on_connect=on_connect)

        self.loop.run()

    def test_ping_pong(self):
        def on_shutdown(request, status):
            request.stream.close()

        def on_read(pipe, status, length, data):
            if status is not uv.StatusCode.SUCCESS:
                pipe.shutdown(on_shutdown=on_shutdown)
                return
            self.buffer.append(data)
            if b''.join(self.buffer) == b'PING':
                del self.buffer[:]
                self.pong_counter += 1
                self.assert_is(pipe, self.client)
                pipe.write(b'PONG')
            elif b''.join(self.buffer) == b'PONG':
                del self.buffer[:]
                if self.ping_counter < 5:
                    pipe.write(b'PING')
                    self.ping_counter += 1
                else:
                    pipe.shutdown(on_shutdown=on_shutdown)
                    self.server.close()

        def on_connect(request, status):
            self.assert_equal(status, uv.StatusCode.SUCCESS)
            request.stream.read_start(on_read=on_read)

        def on_connection(pipe, status):
            """
            :type pipe: uv.Pipe
            """
            self.assert_equal(status, uv.StatusCode.SUCCESS)
            connection = pipe.accept()
            connection.read_start(on_read=on_read)
            connection.write(b'PING')

        self.buffer = []

        self.ping_counter = 1
        self.pong_counter = 0

        self.server = uv.Pipe()
        self.server.bind(TEST_PIPE1)
        self.server.listen(5, on_connection=on_connection)

        self.client = uv.Pipe()
        self.client.connect(TEST_PIPE1, on_connect=on_connect)

        self.loop.run()

        self.assert_equal(self.ping_counter, 5)
        self.assert_equal(self.pong_counter, 5)
