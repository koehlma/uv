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


class TestStream(common.TestCase):
    def test_closed(self):
        self.pipe = uv.Pipe()
        self.pipe.close()
        self.assert_false(self.pipe.readable)
        self.assert_false(self.pipe.writable)
        self.assert_raises(uv.ClosedHandleError, self.pipe.shutdown)
        self.assert_raises(uv.ClosedHandleError, self.pipe.listen)
        self.assert_raises(uv.ClosedHandleError, self.pipe.read_start)
        self.assert_is(self.pipe.read_stop(), None)
        self.assert_raises(uv.ClosedHandleError, self.pipe.write, b'')
        self.assert_raises(uv.ClosedHandleError, self.pipe.try_write, b'')
        self.assert_raises(uv.ClosedHandleError, self.pipe.accept)

    @common.skip_platform('win32')
    def test_try_write(self):
        self.buffer = b''
        self.bytes_written = 0

        def on_read(connection, status, data):
            self.buffer += data
            connection.read_stop()

        def on_connection(pipe_handle, status):
            connection = pipe_handle.accept()
            connection.read_start(on_read=on_read)
            pipe_handle.close()

        def on_timeout(timer):
            try:
                self.bytes_written = self.client.try_write(b'hello')
            except uv.error.TemporaryUnavailableError:
                self.server.close()
            finally:
                timer.close()

        self.server = uv.Pipe()
        self.server.bind(common.TEST_PIPE1)
        self.server.listen(on_connection=on_connection)

        self.client = uv.Pipe()
        self.client.connect(common.TEST_PIPE1)

        self.timer = uv.Timer(on_timeout=on_timeout)
        self.timer.start(10)

        self.loop.run()

        self.assert_equal(self.buffer, b'hello'[:self.bytes_written])

    def test_writable_readable(self):
        self.pipe = uv.Pipe()
        self.assert_false(self.pipe.readable)
        self.assert_false(self.pipe.writable)
