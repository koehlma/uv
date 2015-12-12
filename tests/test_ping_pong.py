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

import os

import common

import uv


class TestPingPong(common.TestCase):
    def on_shutdown(self, request, status):
        request.stream.close()

    def on_read(self, stream, status, length, data):
        if status is not uv.StatusCode.SUCCESS:
            stream.shutdown(on_shutdown=self.on_shutdown)
            return
        self.buffer.append(data)
        if b''.join(self.buffer) == b'PING':
            del self.buffer[:]
            self.pong_counter += 1
            self.assert_is(stream, self.client)
            stream.write(b'PONG')
        elif b''.join(self.buffer) == b'PONG':
            del self.buffer[:]
            if self.ping_counter < 5:
                stream.write(b'PING')
                self.ping_counter += 1
            else:
                stream.shutdown(on_shutdown=self.on_shutdown)
                self.server.close()

    def on_connect(self, request, status):
        self.assert_equal(status, uv.StatusCode.SUCCESS)
        request.stream.read_start(on_read=self.on_read)

    def on_connection(self, stream, status):
        self.assert_equal(status, uv.StatusCode.SUCCESS)
        connection = stream.accept()
        connection.read_start(on_read=self.on_read)
        connection.write(b'PING')

    def set_up(self):
        self.buffer = []

        self.ping_counter = 1
        self.pong_counter = 0

    def run_ping_pong(self):
        self.loop.run()

        self.assert_equal(self.ping_counter, 5)
        self.assert_equal(self.pong_counter, 5)

    def test_pipe(self):
        self.server = uv.Pipe()
        self.server.bind(common.TEST_PIPE1)
        self.server.listen(5, on_connection=self.on_connection)

        self.client = uv.Pipe()
        self.client.connect(common.TEST_PIPE1, on_connect=self.on_connect)

        self.run_ping_pong()

    def test_tcp_ipv4(self):
        self.server = uv.TCP()
        self.server.bind((common.TEST_IPV4, common.TEST_PORT1))
        self.server.listen(5, on_connection=self.on_connection)

        self.client = uv.TCP()
        self.client.connect((common.TEST_IPV4, common.TEST_PORT1),
                            on_connect=self.on_connect)

        self.run_ping_pong()

    def test_tcp_ipv6(self):
        address = (common.TEST_IPV6, common.TEST_PORT1)

        self.server = uv.TCP()
        self.server.bind(address)
        self.server.listen(5, on_connection=self.on_connection)

        self.client = uv.TCP()
        self.client.connect(address, on_connect=self.on_connect)

        self.run_ping_pong()



