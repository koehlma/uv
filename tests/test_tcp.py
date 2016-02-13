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


class TestTCP(common.TestCase):
    def test_closed(self):
        self.tcp = uv.TCP()
        self.tcp.close()

        self.assert_raises(uv.ClosedHandleError, self.tcp.open, 0)
        self.assert_raises(uv.ClosedHandleError, self.tcp.bind, None, 0)
        self.assert_raises(uv.ClosedHandleError, self.tcp.connect, (common.TEST_IPV4, 42))
        with self.should_raise(uv.ClosedHandleError):
            sockname = self.tcp.sockname
        with self.should_raise(uv.ClosedHandleError):
            peername = self.tcp.peername
        self.assert_raises(uv.ClosedHandleError, self.tcp.set_nodelay, True)
        self.assert_raises(uv.ClosedHandleError, self.tcp.set_keepalive, True, 10)
        self.assert_raises(uv.ClosedHandleError, self.tcp.set_simultaneous_accepts, True)

    def test_settings(self):
        self.tcp = uv.TCP()
        self.tcp.set_nodelay(True)
        self.tcp.set_keepalive(False, 10)
        self.tcp.set_simultaneous_accepts(True)

    def test_open(self):
        server = socket.socket()
        self.tcp = uv.TCP()
        self.tcp.open(server.fileno())

    def test_family(self):
        self.tcp4 = uv.TCP()
        self.assert_equal(self.tcp4.family, None)
        self.tcp4.bind((common.TEST_IPV4, common.TEST_PORT1))
        self.assert_equal(self.tcp4.family, socket.AF_INET)

        self.tcp6 = uv.TCP()
        self.tcp6.bind((common.TEST_IPV6, common.TEST_PORT1))
        self.assert_equal(self.tcp6.family, socket.AF_INET6)

    def test_sockname_peername(self):
        address = (common.TEST_IPV4, common.TEST_PORT1)

        def on_connection(server, status):
            server.close()

        def on_connect(request, status):
            self.assert_equal(request.stream.peername, address)
            request.stream.close()

        self.server = uv.TCP()
        self.server.bind(address)
        self.server.listen(on_connection=on_connection)
        self.assert_equal(self.server.sockname, address)

        self.client = uv.TCP()
        self.client.connect(address, on_connect=on_connect)

        self.loop.run()
