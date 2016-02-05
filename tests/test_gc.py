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

import gc
import weakref

from common import TestCase, implementation_skip

import uv


@implementation_skip('pypy')
class TestGC(TestCase):
    def test_gc_loop(self):
        loop = uv.Loop()
        weak_loop = weakref.ref(loop)
        base_loop = weakref.ref(loop.base_loop)
        del loop
        gc.collect()
        self.assert_not_equal(weak_loop(), None)
        self.assert_not_equal(base_loop(), None)
        uv.Loop._thread_locals.loop = None
        gc.collect()
        self.assert_equal(weak_loop(), None)
        self.assert_equal(base_loop(), None)

    def test_gc_handle(self):
        weak_handle = weakref.ref(uv.Prepare())
        gc.collect()
        self.assert_equal(weak_handle(), None)
        prepare = uv.Prepare()
        prepare.start()
        weak_handle = weakref.ref(prepare)
        del prepare
        gc.collect()
        self.assert_not_equal(weak_handle(), None)

