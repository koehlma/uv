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
import os.path
import tempfile

import common

import uv


@common.skip_platform('win32')
class TestFSEvent(common.TestCase):
    def test_fs_event_change(self):
        def on_event(fs_event, status, name, events):
            self.assert_equal(status, uv.error.StatusCodes.SUCCESS)
            self.assert_equal(name, os.path.basename(self.temp_file.name))
            self.assert_equal(events, uv.FSEvents.CHANGE)
            fs_event.close()

        def on_timeout(timer):
            self.temp_file.write(b'x')
            self.temp_file.flush()
            timer.close()

        self.fs_event = uv.FSEvent(on_event=on_event)
        self.timer = uv.Timer(on_timeout=on_timeout)

        with tempfile.NamedTemporaryFile() as temp_file:
            self.temp_file = temp_file
            self.fs_event.path = temp_file.name
            self.fs_event.start()
            self.timer.start(20)
            self.loop.run()

    def test_fs_event_rename(self):
        def on_event(fs_event, status, name, events):
            self.assert_equal(status, uv.error.StatusCodes.SUCCESS)
            self.assert_equal(name, os.path.basename(self.temp_file.name))
            self.assert_equal(events, uv.FSEvents.RENAME)
            fs_event.close()

        def on_timeout(timer):
            os.rename(self.temp_file.name, self.temp_file.name + '-new-name')
            timer.close()

        self.fs_event = uv.FSEvent(on_event=on_event)
        self.timer = uv.Timer(on_timeout=on_timeout)

        with tempfile.NamedTemporaryFile() as temp_file:
            self.temp_file = temp_file
            self.fs_event.path = temp_file.name
            self.fs_event.start()
            self.timer.start(20)
            self.loop.run()
            os.rename(self.temp_file.name + '-new-name', self.temp_file.name)

    def test_fs_event_stop(self):
        self.fs_event = uv.FSEvent()

        with tempfile.NamedTemporaryFile() as temp_file:
            self.fs_event.path = temp_file.name
            self.fs_event.start()
            self.fs_event.stop()
            self.loop.run()

    def test_closed(self):
        self.fs_event = uv.FSEvent()
        self.fs_event.close()

        self.assert_raises(uv.ClosedHandleError, self.fs_event.start)
        self.assert_is(self.fs_event.stop(), None)

    def test_path_none(self):
        self.fs_event = uv.FSEvent()

        self.assert_raises(uv.error.ArgumentError, self.fs_event.start)
