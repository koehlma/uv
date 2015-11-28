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

import threading
import time
import unittest

import uv


class TestLoop(unittest.TestCase):
    def setUp(self):
        self.loop = uv.Loop()

    def test_loop_alive(self):
        self.assertFalse(self.loop.alive)

        self.loop_alive = False

        def on_prepare(prepare):
            self.loop_alive = self.loop.alive
            prepare.close()

        self.prepare = uv.Prepare(self.loop, on_prepare)

        self.prepare.start()
        self.loop.run()

        self.assertTrue(self.loop_alive)

    def test_run_once(self):
        self.callback_called = 0

        def on_prepare(prepare):
            self.callback_called += 1
            prepare.close()

        for _ in range(500):
            self.prepare = uv.Prepare(self.loop, on_prepare)
            self.prepare.start()
            self.loop.run(uv.RunMode.ONCE)

        self.assertEqual(self.callback_called, 500)

    def test_run_nowait(self):
        self.callback_called = False

        def on_timeout(timer):
            self.callback_called = True
            timer.close()

        self.timer = uv.Timer(self.loop, on_timeout)

        self.timer.start(100, repeat=100)
        self.loop.run(uv.RunMode.NOWAIT)

        self.assertFalse(self.callback_called)

    def test_get_handles(self):
        prepare = uv.Prepare(self.loop)
        timer = uv.Timer(self.loop)

        handles = self.loop.handles

        self.assertEqual(len(handles), 2)
        self.assertTrue(prepare in handles)
        self.assertTrue(timer in handles)

        prepare.close()
        timer.close()

        self.loop.run()

        handles = self.loop.handles

        self.assertEqual(len(handles), 0)

    def test_stop(self):
        self.timer_called = 0
        self.prepare_called = 0

        def on_timeout(timer):
            self.timer_called += 1
            if self.timer_called == 2:
                self.loop.stop()
            if self.timer_called == 10:
                timer.close()

        def on_prepare(prepare):
            self.prepare_called += 1
            if self.prepare_called == 10:
                prepare.close()

        self.timer = uv.Timer(self.loop, on_timeout)
        self.timer.start(10, repeat=10)
        self.prepare = uv.Prepare(self.loop, on_prepare)
        self.prepare.start()

        self.loop.run()
        self.assertEqual(self.timer_called, 2)
        self.assertTrue(self.prepare_called >= 2)
        self.loop.run(uv.RunMode.NOWAIT)
        self.assertTrue(self.prepare_called >= 3)
        self.loop.run()
        self.assertEqual(self.timer_called, 10)
        self.assertEqual(self.prepare_called, 10)

    def test_close(self):
        self.prepare = uv.Prepare(self.loop)
        self.prepare.start()

        self.assertFalse(self.loop.closed)

        self.assertRaises(uv.UVError, self.loop.close)
        self.prepare.close()
        self.assertRaises(uv.UVError, self.loop.close)

        self.loop.run()

        self.loop.close()

        self.assertRaises(uv.ClosedLoop, uv.Async, loop=self.loop)
        self.assertRaises(uv.ClosedLoop, uv.Check, loop=self.loop)
        self.assertRaises(uv.ClosedLoop, uv.Idle, loop=self.loop)
        self.assertRaises(uv.ClosedLoop, uv.Pipe, loop=self.loop)
        self.assertRaises(uv.ClosedLoop, uv.Poll, 0, loop=self.loop)
        self.assertRaises(uv.ClosedLoop, uv.Prepare, loop=self.loop)
        self.assertRaises(uv.ClosedLoop, uv.Process, ['python'], loop=self.loop)
        self.assertRaises(uv.ClosedLoop, uv.Signal, loop=self.loop)
        self.assertRaises(uv.ClosedLoop, uv.TCP, loop=self.loop)
        self.assertRaises(uv.ClosedLoop, uv.Timer, loop=self.loop)
        self.assertRaises(uv.ClosedLoop, uv.TTY, 0, loop=self.loop)
        self.assertRaises(uv.ClosedLoop, uv.UDP, loop=self.loop)

    def test_current_loop(self):
        self.assertEqual(uv.Loop.default_loop(), uv.Loop.current_loop())

        self.loop1 = uv.Loop()
        self.loop2 = uv.Loop()

        def on_prepare1(prepare):
            self.assertEqual(self.loop1, uv.Loop.current_loop())
            prepare.close()

        def on_prepare2(prepare):
            self.assertEqual(self.loop2, uv.Loop.current_loop())
            prepare.close()

        def main1():
            for _ in range(500):
                self.prepare1 = uv.Prepare(self.loop1, on_prepare1)
                self.prepare1.start()
                self.loop1.run()

        def main2():
            for _ in range(500):
                self.prepare2 = uv.Prepare(self.loop2, on_prepare2)
                self.prepare2.start()
                self.loop2.run()

        thread1 = threading.Thread(target=main1)
        thread1.start()

        main2()

        thread1.join()

        self.assertEqual(uv.Loop.default_loop(), uv.Loop.current_loop())

    def test_update_time(self):
        def on_prepare(prepare):
            now = self.loop.now
            time.sleep(0.5)
            self.assertEqual(now, self.loop.now)
            self.loop.update_time()
            self.assertGreater(self.loop.now, now)
            prepare.close()

        self.prepare = uv.Prepare(self.loop, on_prepare)
        self.prepare.start()

        self.loop.run()
