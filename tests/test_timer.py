# -*- coding: utf-8 -*-
#
# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import unittest

import uv


class TestTimer(unittest.TestCase):
    def setUp(self):
        self.loop = uv.Loop()

    def test_timer_simple(self):
        self.timer_called = 0

        def on_timeout(t):
            self.timer_called += 1

        timer = uv.Timer(self.loop, on_timeout)
        timer.start(50)

        self.loop.run()

        self.assertEqual(self.timer_called, 1)

    def test_timer_repeat(self):
        self.timer_called = 0

        def on_timeout(t):
            self.timer_called += 1
            if self.timer_called == 3: t.stop()

        timer = uv.Timer(self.loop, on_timeout)
        timer.start(50, repeat=50)

        self.loop.run()

        self.assertEquals(self.timer_called, 3)

    def test_timer_delta(self):
        self.timer_called = 0
        self.timer_times = []

        def on_timeout(t):
            self.timer_called += 1
            self.timer_times.append(uv.misc.hrtime())
            if self.timer_called == 2: t.stop()

        timer = uv.Timer(self.loop, on_timeout)
        timer.start(20, repeat=50)

        self.loop.run()

        delta = round((self.timer_times[1] - self.timer_times[0]) / 10 ** 6, 0)
        self.assertEqual(delta, 50)

    def test_timer_close(self):
        self.timer_called = 0

        def on_timeout(t):
            self.timer_called += 1

        timer = uv.Timer(self.loop, on_timeout)
        timer.start(50)
        timer.close()

        self.loop.run()

        self.assertEqual(self.timer_called, 0)

    def test_timer_reference(self):
        self.timer_called = 0

        def on_timeout(t):
            self.timer_called += 1

        timer = uv.Timer(self.loop, on_timeout)
        timer.start(50)
        timer.dereference()

        self.loop.run()

        self.assertFalse(timer.referenced)
        self.assertEqual(self.timer_called, 0)

        timer.reference()

        self.loop.run()

        self.assertTrue(timer.referenced)
        self.assertEqual(self.timer_called, 1)
