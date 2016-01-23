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

from __future__ import print_function, unicode_literals, division, absolute_import

from common import TestCase

import uv


class TestReferences(TestCase):
    def test_references(self):
        loop = uv.Loop()
        self.assert_is(loop, uv.Loop._thread_locals.loop)
        self.assert_false(loop in uv.Loop._loops)
        async = uv.Async()
        self.assert_false(loop in uv.Loop._loops)
        self.assert_false(async in loop._handles)
        async.send()
        self.assert_in(loop, uv.Loop._loops)
        self.assert_in(async, loop._handles)
        loop.run(uv.RunModes.ONCE)
        self.assert_false(loop in uv.Loop._loops)
        self.assert_false(async in loop._handles)