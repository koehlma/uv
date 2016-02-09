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


class TestHandle(common.TestCase):
    def test_double_close(self):
        self.prepare = uv.Prepare()
        self.prepare.close()
        self.prepare.close()

    def test_active(self):
        self.async = uv.Async()
        self.assert_true(self.async.active)

    def test_referencing(self):
        self.async = uv.Async()
        self.assert_true(self.async.referenced)
        self.async.referenced = False
        self.assert_false(self.async.referenced)
        self.async.reference()
        self.assert_true(self.async.referenced)
        self.async.dereference()
        self.assert_false(self.async.referenced)

    def test_buffer_size(self):
        self.tcp = uv.TCP()
        self.tcp.bind((common.TEST_IPV4, common.TEST_PORT1))
        self.tcp.send_buffer_size = 262144
        self.assert_equal(self.tcp.send_buffer_size, 262144)
        self.tcp.receive_buffer_size = 262144
        self.assert_equal(self.tcp.receive_buffer_size, 262144)

    def test_fileno(self):
        self.tcp = uv.TCP()
        self.tcp.bind((common.TEST_IPV4, common.TEST_PORT1))
        self.assert_is_instance(self.tcp.fileno(), int)

    def test_closed(self):
        self.tcp = uv.TCP()
        self.tcp.close()
        self.assert_true(self.tcp.closing)
        with self.should_raise(uv.ClosedHandleError):
            self.tcp.referenced = True
        with self.should_raise(uv.ClosedHandleError):
            self.tcp.referenced = False
        with self.should_raise(uv.ClosedHandleError):
            send_buffer_size = self.tcp.send_buffer_size
        with self.should_raise(uv.ClosedHandleError):
            self.tcp.send_buffer_size = 42
        with self.should_raise(uv.ClosedHandleError):
            receive_buffer_size = self.tcp.receive_buffer_size
        with self.should_raise(uv.ClosedHandleError):
            self.tcp.receive_buffer_size = 42
        self.assert_raises(uv.ClosedHandleError, self.tcp.fileno)
        self.assert_is(self.tcp.close(), None)
        self.loop.run()
        self.assert_true(self.tcp.closed)
        self.assert_false(self.tcp.active)
        self.assert_false(self.tcp.referenced)
