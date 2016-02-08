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

import os.path
import sys

import common

import uv


__dir__ = os.path.dirname(__file__)

PROGRAM_HELLO = os.path.join(__dir__, 'program_hello.py')
PROGRAM_ENDLESS_LOOP = os.path.join(__dir__, 'program_endless_loop.py')


class TestProcess(common.TestCase):
    def test_process_hello(self):
        arguments = [sys.executable, PROGRAM_HELLO]

        self.buffer = b''
        self.returncode = None

        def on_exit(process_handle, returncode, term_signal):
            self.returncode = returncode

        def on_read(pipe_handle, status, length, data):
            self.buffer += data

        self.process = uv.Process(arguments, stdout=uv.PIPE, on_exit=on_exit)
        self.process.stdout.read_start(on_read)

        self.loop.run()

        self.assert_equal(self.buffer.strip(), b'hello')
        self.assert_equal(self.returncode, 1)
        self.assert_not_equal(self.process.pid, None)
        self.assert_raises(uv.error.ProcessLookupError, self.process.kill)

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
        self.assert_equal(self.term_signal, uv.Signals.SIGINT)
