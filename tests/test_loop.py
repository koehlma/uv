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

import threading
import time

import common

import uv


class TestLoop(common.TestCase):
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

        self.assert_raises(uv.ClosedLoopError, uv.Async, loop=self.loop)
        self.assert_raises(uv.ClosedLoopError, uv.Check, loop=self.loop)
        self.assert_raises(uv.ClosedLoopError, uv.Idle, loop=self.loop)
        self.assert_raises(uv.ClosedLoopError, uv.Pipe, loop=self.loop)
        self.assert_raises(uv.ClosedLoopError, uv.Poll, 0, loop=self.loop)
        self.assert_raises(uv.ClosedLoopError, uv.Prepare, loop=self.loop)
        self.assert_raises(uv.ClosedLoopError, uv.Process, ['python'], loop=self.loop)
        self.assert_raises(uv.ClosedLoopError, uv.Signal, loop=self.loop)
        self.assert_raises(uv.ClosedLoopError, uv.TCP, loop=self.loop)
        self.assert_raises(uv.ClosedLoopError, uv.Timer, loop=self.loop)
        self.assert_raises(uv.ClosedLoopError, uv.TTY, 0, loop=self.loop)
        self.assert_raises(uv.ClosedLoopError, uv.UDP, loop=self.loop)

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

    def test_call_later(self):
        self.callback_called = False

        # keep the loop alive
        self.prepare = uv.Prepare()
        self.prepare.start()

        def callback():
            self.callback_called = True
            self.prepare.close()

        self.loop.call_later(callback)
        self.loop.run()

        self.assert_true(self.callback_called)

    def test_current_loop(self):
        self.assertEqual(uv.Loop.get_default(), uv.Loop.get_current())

        self.loop1 = uv.Loop()
        self.loop2 = uv.Loop()

        def on_prepare1(prepare):
            self.assertEqual(self.loop1, uv.Loop.get_current())
            prepare.close()

        def on_prepare2(prepare):
            self.assertEqual(self.loop2, uv.Loop.get_current())
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

        self.assertEqual(self.loop2, uv.Loop.get_current())

        self.loop1.close()
        self.loop2.close()

    def test_double_close(self):
        self.loop.close()
        self.loop.close()

    def test_excepthook(self):
        self.loop.close()
        self.loop = uv.Loop()

        def excepthook(loop, exc_type, exc_value, exc_traceback):
            loop.stop()

        self.loop.excepthook = excepthook

        def throw_test(*_):
            raise Exception('test')

        self.prepare = uv.Prepare(on_prepare=throw_test)
        self.prepare.start()

        self.loop.run()

        self.assert_is(self.loop.exc_type, Exception)
        self.assert_equal(self.loop.exc_value.args[0], 'test')

        self.loop.reset_exception()
        self.assert_is(self.loop.exc_type, None)
        self.assert_is(self.loop.exc_value, None)

        self.prepare.close(on_closed=throw_test)

        self.loop.run()

        self.assert_is(self.loop.exc_type, Exception)
        self.assert_equal(self.loop.exc_value.args[0], 'test')
        self.loop.reset_exception()

        self.pipe = uv.Pipe()
        self.pipe.connect(common.BAD_PIPE, on_connect=throw_test)

        self.loop.run()

        self.assert_is(self.loop.exc_type, Exception)
        self.assert_equal(self.loop.exc_value.args[0], 'test')
        self.loop.reset_exception()

        # call later does no longer keep the loop alive
        #self.loop.call_later(throw_test)
        #
        #self.loop.run()
        #
        #self.assert_is(self.loop.exc_type, Exception)
        #self.assert_equal(self.loop.exc_value.args[0], 'test')
        #self.loop.reset_exception()

    def test_get_current_instantiate(self):
        uv.Loop._thread_locals.loop = None
        loop = uv.Loop.get_current()
        self.assert_is(uv.Loop.get_current(), loop)
        loop.close()

    def test_default_exists(self):
        uv.Loop.get_default()
        self.assert_raises(RuntimeError, uv.Loop, default=True)

    def test_closed(self):
        self.loop.close()
        self.assert_false(self.loop.alive)
        with self.should_raise(uv.ClosedLoopError):
            now = self.loop.now
        self.assert_equal(self.loop.handles, set())
        self.assert_raises(uv.ClosedLoopError, self.loop.fileno)
        self.assert_raises(uv.ClosedLoopError, self.loop.update_time)
        self.assert_raises(uv.ClosedLoopError, self.loop.get_timeout)
        self.assert_raises(uv.ClosedLoopError, self.loop.run)
        self.assert_is(self.loop.stop(), None)

    @common.skip_platform('win32')
    def test_fileno(self):
        self.assert_greater(self.loop.fileno(), 0)

    def test_poll_timeout(self):
        self.assert_equal(self.loop.get_timeout(), 0)
