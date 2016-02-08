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

from common import TestCase

import uv


class TestTimer(TestCase):
    def test_timer_simple(self):
        self.timer_called = 0

        def on_timeout(_):
            self.timer_called += 1

        timer = uv.Timer(on_timeout=on_timeout)
        timer.start(50)

        self.loop.run()

        self.assert_equal(self.timer_called, 1)

    def test_timer_repeat(self):
        self.timer_called = 0

        def on_timeout(t):
            self.timer_called += 1
            if self.timer_called == 3: t.close()

        timer = uv.Timer(on_timeout=on_timeout)
        timer.start(50, repeat=50)

        self.loop.run()

        self.assert_equal(self.timer_called, 3)

    def test_timer_close(self):
        self.timer_called = 0

        def on_timeout(_):
            self.timer_called += 1

        timer = uv.Timer(on_timeout=on_timeout)
        timer.start(50)
        timer.close()

        self.loop.run()

        self.assert_equal(self.timer_called, 0)

    def test_timer_reference(self):
        self.timer_called = 0

        def on_timeout(_):
            self.timer_called += 1

        timer = uv.Timer(on_timeout=on_timeout)
        timer.start(50)
        timer.dereference()

        self.loop.run()

        self.assert_false(timer.referenced)
        self.assert_equal(self.timer_called, 0)

        timer.reference()

        self.loop.run()

        self.assert_true(timer.referenced)
        self.assert_equal(self.timer_called, 1)

    def test_timer_pending(self):
        self.timer_called = 0

        def on_timeout(timer_handle):
            if self.timer_called == 0:
                self.assert_false(self.loop.structure_is_pending(timer_handle))
                timer_handle.repeat = 5
                timer_handle.again()
                self.assert_true(self.loop.structure_is_pending(timer_handle))
            self.timer_called += 1
            if self.timer_called >= 5:
                timer_handle.stop()
                self.assert_false(self.loop.structure_is_pending(timer_handle))

        self.timer = uv.Timer(on_timeout=on_timeout)
        self.assert_false(self.loop.structure_is_pending(self.timer))
        self.timer.start(5)
        self.assert_true(self.loop.structure_is_pending(self.timer))

        self.loop.run()

        self.assert_equal(self.timer_called, 5)

    def test_closed(self):
        self.timer = uv.Timer()
        self.timer.close()

        try:
            repeat = self.timer.repeat
        except uv.ClosedHandleError:
            pass
        else:
            self.assert_true(False)
        try:
            self.timer.repeat = 10
        except uv.ClosedHandleError:
            pass
        else:
            self.assert_true(False)
        self.assert_raises(uv.ClosedHandleError, self.timer.again)
        self.assert_raises(uv.ClosedHandleError, self.timer.start, 10)
        self.assert_is(self.timer.stop(), None)
