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

from __future__ import print_function, unicode_literals, division

from common import TestCase

import uv


class TestIdle(TestCase):
    def test_idle(self):
        def on_idle(idle):
            self.on_idle_called += 1
            if self.on_idle_called > 5: idle.close()

        self.on_idle_called = 0

        self.idle = uv.Idle(on_idle=on_idle)
        self.idle.start()

        self.loop.run()

        self.assert_equal(self.on_idle_called, 6)