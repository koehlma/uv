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


class TestRequest(common.TestCase):
    def test_closed_loop(self):
        self.loop.close()

        self.assert_raises(uv.ClosedLoopError, uv.dns.getaddrinfo,
                           'localhost', 80, loop=self.loop)

    def test_type(self):
        self.pipe = uv.Pipe()
        request = self.pipe.connect(common.BAD_PIPE)
        self.assert_is(request.type, uv.ConnectRequest)

    def test_cancel(self):
        self.tcp = uv.TCP()
        self.assert_raises(uv.error.ArgumentError,
                           self.tcp.connect(('127.0.0.1', 80)).cancel)

