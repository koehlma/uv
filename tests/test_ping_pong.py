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

import common

import uv


class TestPingPong(common.TestCase):
    def on_shutdown(self, request, status):
        request.stream.close()

    def on_read(self, stream, status, data):
        if status is not uv.StatusCodes.SUCCESS:
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
        self.assert_equal(status, uv.StatusCodes.SUCCESS)
        request.stream.read_start(on_read=self.on_read)

    def on_connection(self, stream, status):
        self.assert_equal(status, uv.StatusCodes.SUCCESS)
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
        self.server.pending_instances(100)
        self.server.bind(common.TEST_PIPE1)
        self.server.listen(5, on_connection=self.on_connection)

        self.client = uv.Pipe()
        self.client.connect(common.TEST_PIPE1, on_connect=self.on_connect)

        self.run_ping_pong()

    def test_tcp_ipv4(self):
        address = (common.TEST_IPV4, common.TEST_PORT1)

        self.server = uv.TCP()
        self.server.bind(address)
        self.server.listen(5, on_connection=self.on_connection)

        self.client = uv.TCP()
        self.client.connect(address, on_connect=self.on_connect)

        self.run_ping_pong()

    def test_tcp_ipv6(self):
        address = (common.TEST_IPV6, common.TEST_PORT1)

        self.server = uv.TCP()
        self.server.bind(address)
        self.server.listen(5, on_connection=self.on_connection)

        self.client = uv.TCP()
        self.client.connect(address, on_connect=self.on_connect)

        self.run_ping_pong()

    def test_tcp_ipv4_icp_client(self):
        address = (common.TEST_IPV4, common.TEST_PORT1)

        self.server = uv.TCP()
        self.server.bind(address)
        self.server.listen(5, on_connection=self.on_connection)

        client = uv.TCP()
        client.connect(address)

        def on_read(pipe_client, status, data):
            if pipe_client.pending_count:
                self.client = pipe_client.pending_accept()
                self.client.read_start(on_read=self.on_read)
                pipe_client.close()

        def on_connection(pipe_server, status):
            connection = pipe_server.accept(ipc=True)
            connection.write(b'hello', send_stream=client)
            connection.close()
            pipe_server.close()

        self.pipe_server = uv.Pipe()
        self.pipe_server.pending_instances(100)
        self.pipe_server.bind(common.TEST_PIPE1)
        self.pipe_server.listen(on_connection=on_connection)

        self.pipe_client = uv.Pipe(ipc=True)
        self.pipe_client.connect(common.TEST_PIPE1)
        self.pipe_client.read_start(on_read=on_read)

        self.loop.run()

        self.run_ping_pong()

        client.close()
        self.server.close()
        self.client.close()
