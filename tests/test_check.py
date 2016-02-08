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

from common import TestCase

import uv


class TestCheck(TestCase):
    def test_check(self):
        def on_check(check):
            self.on_check_called += 1
            if self.on_timeout_called > 5: check.close()

        def on_timeout(timer):
            self.on_timeout_called += 1
            if self.on_timeout_called > 5: timer.close()

        self.on_check_called = 0
        self.on_timeout_called = 0

        self.check = uv.Check(on_check=on_check)
        self.check.start()

        self.timer = uv.Timer(on_timeout=on_timeout)
        self.timer.start(5, repeat=5)

        self.loop.run()

        self.assert_less_equal(self.on_timeout_called, self.on_check_called)

    def test_check_stop(self):
        self.check = uv.Check()
        self.check.start()
        self.check.stop()
        self.loop.run()

    def test_closed(self):
        self.check = uv.Check()
        self.check.close()

        self.assert_raises(uv.ClosedHandleError, self.check.start)
        self.assert_is(self.check.stop(), None)
