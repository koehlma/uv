# -*- coding: utf-8 -*-

# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
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

import time

from common import TestCase

import uv


class TestLoop(TestCase):
    def test_loop_alive(self):
        self.assert_false(self.loop.alive)

        self.loop_alive = False

        def on_prepare(prepare):
            self.loop_alive = self.loop.alive
            prepare.close()

        self.prepare = uv.Prepare(on_prepare=on_prepare)

        self.prepare.start()
        self.loop.run()

        self.assert_true(self.loop_alive)
        self.assert_false(self.loop.alive)

    def test_run_once(self):
        self.callback_called = 0

        def on_prepare(prepare):
            self.callback_called += 1
            prepare.close()

        for _ in range(500):
            self.prepare = uv.Prepare(on_prepare=on_prepare)
            self.prepare.start()
            self.loop.run(uv.RunModes.ONCE)

        self.assert_equal(self.callback_called, 500)

    def test_run_nowait(self):
        self.callback_called = False

        def on_timeout(timer):
            self.callback_called = True
            timer.close()

        self.timer = uv.Timer(on_timeout=on_timeout)
        self.timer.start(100, repeat=100)

        self.loop.run(uv.RunModes.NOWAIT)

        self.assert_false(self.callback_called)

        self.timer.close()
        self.loop.run()

    def test_get_handles(self):
        prepare = uv.Prepare()
        timer = uv.Timer()

        self.assert_equal(len(self.loop.handles), 2)
        self.assert_in(prepare, self.loop.handles)
        self.assert_in(timer, self.loop.handles)

        prepare.close()
        timer.close()

        self.loop.run()

        self.assert_equal(len(self.loop.handles), 0)

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

        self.timer = uv.Timer(on_timeout=on_timeout)
        self.timer.start(10, repeat=10)
        self.prepare = uv.Prepare(on_prepare=on_prepare)
        self.prepare.start()

        self.loop.run()
        self.assert_equal(self.timer_called, 2)
        self.assert_greater_equal(self.prepare_called, 2)
        self.loop.run(uv.RunModes.NOWAIT)
        self.assert_greater_equal(self.prepare_called, 3)
        self.loop.run()
        self.assert_equal(self.timer_called, 10)
        self.assert_equal(self.prepare_called, 10)

    def test_close(self):
        self.prepare = uv.Prepare()
        self.prepare.start()

        self.assert_false(self.loop.closed)

        self.assert_raises(uv.UVError, self.loop.close)
        self.prepare.close()
        self.assert_raises(uv.UVError, self.loop.close)

        self.loop.run()

        self.loop.close()

        self.assert_raises(uv.LoopClosedError, uv.Async, loop=self.loop)
        self.assert_raises(uv.LoopClosedError, uv.Check, loop=self.loop)
        self.assert_raises(uv.LoopClosedError, uv.Idle, loop=self.loop)
        self.assert_raises(uv.LoopClosedError, uv.Pipe, loop=self.loop)
        self.assert_raises(uv.LoopClosedError, uv.Poll, 0, loop=self.loop)
        self.assert_raises(uv.LoopClosedError, uv.Prepare, loop=self.loop)
        self.assert_raises(uv.LoopClosedError, uv.Process, ['python'], loop=self.loop)
        self.assert_raises(uv.LoopClosedError, uv.Signal, loop=self.loop)
        self.assert_raises(uv.LoopClosedError, uv.TCP, loop=self.loop)
        self.assert_raises(uv.LoopClosedError, uv.Timer, loop=self.loop)
        self.assert_raises(uv.LoopClosedError, uv.TTY, 0, loop=self.loop)
        self.assert_raises(uv.LoopClosedError, uv.UDP, loop=self.loop)

    def test_update_time(self):
        def on_prepare(prepare):
            now = self.loop.now
            time.sleep(0.5)
            self.assert_equal(now, self.loop.now)
            self.loop.update_time()
            self.assert_greater(self.loop.now, now)
            prepare.close()

        self.prepare = uv.Prepare(on_prepare=on_prepare)
        self.prepare.start()

        self.loop.run()


    '''
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
    '''

