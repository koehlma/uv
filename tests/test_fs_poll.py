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

import os
import tempfile

from common import TestCase

import uv

U_TIME = (4200, 4200)


class TestFSPoll(TestCase):
    def test_fs_poll_change(self):
        def on_change(fs_poll, status, previous_stat, current_stat):
            self.assert_equal(status, uv.error.StatusCodes.SUCCESS)
            self.assert_not_equal(previous_stat.mtim, current_stat.mtim)
            fs_poll.close()

        def on_timeout(timer):
            os.utime(self.temp_file.name, U_TIME)
            timer.close()

        self.fs_poll = uv.FSPoll(interval=2000, on_change=on_change)
        self.timer = uv.Timer(on_timeout=on_timeout)

        with tempfile.NamedTemporaryFile() as temp_file:
            self.temp_file = temp_file
            self.fs_poll.path = temp_file.name
            self.fs_poll.start()
            self.timer.start(1000)
            self.loop.run()

    def test_fs_poll_stop(self):
        self.fs_poll = uv.FSPoll()

        with tempfile.NamedTemporaryFile() as temp_file:
            self.fs_poll.path = temp_file.name
            self.fs_poll.start()
            self.fs_poll.stop()
            self.loop.run()

    def test_closed(self):
        self.fs_poll = uv.FSPoll()
        self.fs_poll.close()

        self.assert_raises(uv.ClosedHandleError, self.fs_poll.start)
        self.assert_is(self.fs_poll.stop(), None)

    def test_path_none(self):
        self.fs_poll = uv.FSPoll()

        self.assert_raises(uv.error.ArgumentError, self.fs_poll.start)
