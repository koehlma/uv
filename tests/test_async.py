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

import threading

from common import TestCase

import uv


class TestAsync(TestCase):
    def test_async(self):
        def thread():
            while True:
                with self.lock:
                    if self.async_callback_called == 3:
                        break
                    self.async.send()

        def on_closed(_):
            self.close_callback_called += 1

        def on_wakeup(async):
            with self.lock:
                self.async_callback_called += 1
                if self.async_callback_called == 3:
                    async.close(on_closed=on_closed)
            self.assert_equal(self.loop_thread, threading.current_thread)

        def on_prepare(prepare):
            threading.Thread(target=thread).start()
            prepare.close(on_closed=on_closed)

        self.async_callback_called = 0
        self.close_callback_called = 0
        self.lock = threading.RLock()

        self.loop_thread = threading.current_thread

        self.async = uv.Async(on_wakeup=on_wakeup)

        self.prepare = uv.Prepare(on_prepare=on_prepare)
        self.prepare.start()

        self.loop.run()

        self.assert_equal(self.async_callback_called, 3)
        self.assert_equal(self.close_callback_called, 2)

    def test_closed(self):
        self.async = uv.Async()
        self.async.close()

        self.assert_raises(uv.ClosedHandleError, self.async.send)
