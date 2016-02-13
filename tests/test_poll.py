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


class TestPoll(common.TestCase):
    def test_poll(self):
        def on_shutdown(shutdown_request, _):
            """
            :type shutdown_request:
                uv.ShutdownRequest
            """
            shutdown_request.stream.close()

        def on_connection(server, status):
            """
            :type server:
                uv.TCP
            """
            connection = server.accept()
            connection.write(b'hello')
            connection.shutdown(on_shutdown=on_shutdown)
            server.close()

        self.buffer = b''

        def on_event(poll_handle, status, events):
            if status == uv.StatusCodes.SUCCESS:
                self.buffer = self.client.recv(1024)
            if self.buffer.startswith(b'hello') or status != uv.StatusCodes.SUCCESS:
                poll_handle.stop()

        self.tcp = uv.TCP()
        self.tcp.bind((common.TEST_IPV4, common.TEST_PORT1))
        self.tcp.listen(on_connection=on_connection)

        self.client = socket.socket()
        self.client.connect((common.TEST_IPV4, common.TEST_PORT1))

        self.poll = uv.Poll(self.client.fileno(), on_event=on_event)
        self.poll.start()

        self.assert_equal(self.poll.fileno(), self.client.fileno())

        self.loop.run()

        self.assert_equal(self.buffer, b'hello')

    def test_closed(self):
        self.client = socket.socket()
        self.poll = uv.Poll(self.client.fileno())
        self.poll.close()

        self.assert_raises(uv.ClosedHandleError, self.poll.start)
        self.assert_is(self.poll.stop(), None)
