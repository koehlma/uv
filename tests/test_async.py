# -*- coding: utf-8 -*-

# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function, unicode_literals

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

    def test_callback_exception(self):
        def on_wakeup(_):
            raise ValueError('test exception')

        def excepthook(exc_type, exc_value, _):
            self.exception_occurred = (exc_type == ValueError and
                                       exc_value.args[0] == 'test exception')
            self.async.close()

        self.exception_occurred = False

        self.async = uv.Async(on_wakeup=on_wakeup)
        self.async.send()

        self.loop.excepthook = excepthook
        self.loop.run()

        self.assert_true(self.exception_occurred)
