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


MULTICAST_ADDRESS = '239.255.0.1'


def interface_addresses():
    if uv.common.is_win32:
        for interface_address in uv.misc.interface_addresses():
            if len(interface_address) > 2:
                continue
            yield interface_address.address[0]
    else:
        yield MULTICAST_ADDRESS


@common.skip_pypy((4, 0, 0))
class TestUDP(common.TestCase):
    def test_udp(self):
        self.datagram = None

        def on_receive(udp_handle, status, address, data, flags):
            self.datagram = data
            udp_handle.receive_stop()

        server = socket.socket(type=socket.SOCK_DGRAM)
        self.server = uv.UDP(on_receive=on_receive)
        self.assert_equal(self.server.family, None)
        self.server.open(server.fileno())
        self.assert_equal(self.server.family, server.family)
        self.server.bind((common.TEST_IPV4, common.TEST_PORT1))
        self.assert_equal(self.server.sockname, (common.TEST_IPV4, common.TEST_PORT1))
        self.server.receive_start()

        self.client = uv.UDP()
        self.client.send(b'hello', (common.TEST_IPV4, common.TEST_PORT1))

        self.loop.run()

        self.assert_equal(self.datagram, b'hello')

    def test_udp_multicast(self):
        self.clients = []
        self.results = []

        def on_receive(client, status, address, data, flags):
            self.results.append(data)
            client.receive_stop()

        for address in interface_addresses():
            client = uv.UDP(on_receive=on_receive)
            client.bind((address, common.TEST_PORT1))
            client.set_membership(MULTICAST_ADDRESS, uv.UDPMembership.JOIN_GROUP)
            client.set_multicast_ttl(10)
            client.receive_start()
            self.clients.append(client)

        self.server = uv.UDP()
        self.server.send(b'hello', (MULTICAST_ADDRESS, common.TEST_PORT1))

        self.loop.run()

        self.assert_equal(self.results, [b'hello'] * len(self.clients))

    def test_udp_multicast_loop(self):
        self.datagram = None

        def on_receive(client, status, address, data, flags):
            self.datagram = data
            client.receive_stop()

        self.server = uv.UDP(on_receive=on_receive)
        self.server.bind(('0.0.0.0', common.TEST_PORT1))
        self.server.set_multicast_interface('0.0.0.0')
        self.server.set_membership(MULTICAST_ADDRESS, uv.UDPMembership.JOIN_GROUP)
        self.server.set_multicast_loop(True)
        self.server.receive_start()
        self.server.send(b'hello', (MULTICAST_ADDRESS, common.TEST_PORT1))

        self.loop.run()

        self.assert_equal(self.datagram, b'hello')

    def test_udp_broadcast(self):
        self.datagram = None

        def on_receive(server, status, address, data, flags):
            self.datagram = data
            server.close()

        self.server = uv.UDP(on_receive=on_receive)
        self.server.bind(('0.0.0.0', common.TEST_PORT1))
        self.server.set_broadcast(True)
        self.server.receive_start()

        self.client = uv.UDP()
        self.client.bind(('0.0.0.0', 0))
        self.client.set_broadcast(True)
        self.client.send(b'hello', ('255.255.255.255', common.TEST_PORT1))

        self.loop.run()

        self.assert_equal(self.datagram, b'hello')

    def test_udp_try_send(self):
        self.datagram = None

        def on_receive(udp_handle, status, address, data, flags):
            self.datagram = data
            udp_handle.receive_stop()

        def on_timeout(timer):
            try:
                self.client.try_send(b'hello', (common.TEST_IPV4, common.TEST_PORT1))
            except uv.error.TemporaryUnavailableError:
                self.server.close()
                self.datagram = b'hello'

        self.server = uv.UDP(on_receive=on_receive)
        self.server.bind((common.TEST_IPV4, common.TEST_PORT1))
        self.server.receive_start()

        self.client = uv.UDP()
        self.client.bind(('0.0.0.0', 0))

        self.timer = uv.Timer(on_timeout=on_timeout)
        self.timer.start(100)

        self.loop.run()

        self.assert_equal(self.datagram, b'hello')

    def test_udp_closed(self):
        self.udp = uv.UDP()
        self.udp.close()
        self.assert_is(self.udp.family, None)
        self.assert_equal(self.udp.sockname, ('0.0.0.0', 0))
        self.assert_raises(uv.ClosedHandleError, self.udp.open, None)
        self.assert_raises(uv.ClosedHandleError, self.udp.set_membership, None, None)
        self.assert_raises(uv.ClosedHandleError, self.udp.set_multicast_loop, False)
        self.assert_raises(uv.ClosedHandleError, self.udp.set_multicast_ttl, 10)
        self.assert_raises(uv.ClosedHandleError, self.udp.set_multicast_interface, None)
        self.assert_raises(uv.ClosedHandleError, self.udp.set_broadcast, False)
        self.assert_raises(uv.ClosedHandleError, self.udp.bind, ('0.0.0.0', 0))
        self.assert_raises(uv.ClosedHandleError, self.udp.send, b'', ('0.0.0.0', 0))
        self.assert_raises(uv.ClosedHandleError, self.udp.try_send, b'', ('0.0.0.0', 0))
        self.assert_raises(uv.ClosedHandleError, self.udp.receive_start)
        self.assert_is(self.udp.receive_stop(), None)


