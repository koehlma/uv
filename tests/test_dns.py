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


class TestDNS(common.TestCase):
    def test_dns_sync(self):
        self.assert_true(uv.getaddrinfo('localhost', 80))
        self.assert_equal(uv.getnameinfo('127.0.0.1', 80).service, 'http')

    def test_dns_async(self):
        def got_addrinfo(request, code, addrinfo):
            self.assert_true(addrinfo)

        def got_nameinfo(request, code, hostname, service):
            self.assert_equal(service, 'http')

        uv.getaddrinfo('localhost', 80, callback=got_addrinfo)
        uv.getnameinfo('127.0.0.1', 80, callback=got_nameinfo)

        self.loop.run()

    def test_structures(self):
        address6 = uv.Address6(common.TEST_IPV6, common.TEST_PORT1, 42, 442)
        self.assert_equal(address6.host, common.TEST_IPV6)
        self.assert_equal(address6.port, common.TEST_PORT1)
        self.assert_equal(address6.flowinfo, 42)
        self.assert_equal(address6.scope_id, 442)

        nameinfo = uv.NameInfo('localhost', 'http')
        self.assert_equal(nameinfo.hostname, 'localhost')
        self.assert_equal(nameinfo.service, 'http')

        addrinfo = uv.AddrInfo(0, 1, 2, None, address6)
        self.assert_equal(addrinfo.family, 0)
        self.assert_equal(addrinfo.socktype, 1)
        self.assert_equal(addrinfo.protocol, 2)
        self.assert_is(addrinfo.canonname, None)
        self.assert_equal(addrinfo.address, address6)
