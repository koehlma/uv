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
import unittest

import uv


class TestAsync(unittest.TestCase):
    def setUp(self):
        self.loop = uv.Loop()

    def test_async(self):
        self.async_called = False

        def on_async(a):
            self.async_called = True
            a.close()
            prepare.close()

        def on_prepare(p):
            threading.Thread(target=async.send).start()
            p.stop()

        async = uv.Async(self.loop, on_async)
        prepare = uv.Prepare(self.loop, on_prepare)
        prepare.start()

        self.loop.run()

        self.assertTrue(self.async_called)
