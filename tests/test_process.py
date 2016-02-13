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

import json
import sys

import common

import uv


PROGRAM_HELLO = common.resolve_path('program_hello.py')
PROGRAM_ENDLESS_LOOP = common.resolve_path('program_endless_loop.py')
PROGRAM_DUMP_ENV = common.resolve_path('program_dump_env.py')


class TestProcess(common.TestCase):
    def test_process_hello(self):
        arguments = [sys.executable, PROGRAM_HELLO]

        self.buffer = b''
        self.returncode = None

        def on_exit(process_handle, returncode, term_signal):
            self.returncode = returncode

        def on_read(pipe_handle, status, data):
            self.buffer += data

        self.pipe = uv.Pipe()
        self.pipe.bind(common.TEST_PIPE1)

        self.process = uv.Process(arguments, stdout=uv.PIPE, stdio=[self.pipe],
                                  on_exit=on_exit)
        self.process.stdout.read_start(on_read)

        self.loop.run()

        self.assert_equal(self.buffer.strip(), b'hello')
        self.assert_equal(self.returncode, 1)
        self.assert_not_equal(self.process.pid, None)
        self.assert_raises(uv.error.ProcessLookupError, self.process.kill)

        self.process.close()

        self.assert_raises(uv.ClosedHandleError, self.process.kill)
        with self.should_raise(uv.ClosedHandleError):
            pid = self.process.pid

    def test_process_endless_loop(self):
        arguments = [sys.executable, PROGRAM_ENDLESS_LOOP]

        self.returncode = None
        self.term_signal = None

        def on_exit(process_handle, returncode, term_signal):
            self.returncode = returncode
            self.term_signal = term_signal

        def on_prepare(prepare_handle):
            prepare_handle.close()
            self.process.kill()

        self.process = uv.Process(arguments, on_exit=on_exit)
        self.prepare = uv.Prepare(on_prepare=on_prepare)
        self.prepare.start()

        self.loop.run()

        self.assert_is_not(self.returncode, None)
        self.assert_is_not(self.term_signal, None)

    def test_process_dump_env(self):
        arguments = [sys.executable, PROGRAM_DUMP_ENV]

        self.buffer = b''
        self.returncode = None

        def on_exit(process_handle, returncode, term_signal):
            self.returncode = returncode

        def on_read(pipe_handle, status, data):
            self.buffer += data

        env = {'hello': 'world'}
        self.process = uv.Process(arguments, env=env, stdout=uv.PIPE, on_exit=on_exit,
                                  cwd=common.resolve_path(''))
        self.process.stdout.read_start(on_read)

        self.loop.run()

        self.assert_equal(self.returncode, 0)
        self.assert_not_equal(self.process.pid, None)

        result = json.loads(self.buffer.decode())
        self.assert_equal(result['hello'], 'world')
        self.assert_true(result['cwd'].endswith('tests/data'))

    def test_unknown_file(self):
        arguments = [sys.executable, PROGRAM_HELLO]
        self.assert_raises(uv.error.ArgumentError, uv.Process, arguments, stdout='abc')
