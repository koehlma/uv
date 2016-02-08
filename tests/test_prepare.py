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


class TestPrepare(TestCase):
    def test_prepare(self):
        self.on_prepare_called = 0

        def on_prepare(prepare_handle):
            self.on_prepare_called += 1
            prepare_handle.stop()

        self.prepare = uv.Prepare(on_prepare=on_prepare)
        self.prepare.start()

        self.loop.run()

        self.assert_equal(self.on_prepare_called, 1)

    def test_closed(self):
        self.prepare = uv.Prepare()
        self.prepare.close()

        self.assert_raises(uv.ClosedHandleError, self.prepare.start)
        self.assert_is(self.prepare.stop(), None)
