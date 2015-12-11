# -*- coding: utf-8 -*-
#
# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import unittest

import uv

from uv.common import dummy_callback


class TestLoop(uv.Loop):
    def __init__(self):
        super(TestLoop, self).__init__()
        self.callback_context = self
        self.exc_type = None
        self.exc_value = None
        self.exc_traceback = None

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None and self.exc_type is None:
            self.exc_type = exc_type
            self.exc_value = exc_value
            self.exc_traceback = exc_traceback
            self.stop()

    def run(self, mode=uv.RunMode.DEFAULT):
        self.exc_type = None
        result = super(TestLoop, self).run(mode)
        if self.exc_type is not None:
            raise self.exc_type, self.exc_value, self.exc_traceback
        return result


class TestCase(unittest.TestCase):
    def setUp(self):
        self.loop = TestLoop()
        self.set_up()

    def tearDown(self):
        self.tear_down()
        if not self.loop.closed:
            self.loop.close_all_handles(dummy_callback)
            self.loop.run()
            self.loop.close()

    def set_up(self):
        pass

    def tear_down(self):
        pass

    assert_true = unittest.TestCase.assertTrue
    assert_false = unittest.TestCase.assertFalse

    assert_raises = unittest.TestCase.assertRaises

    assert_equal = unittest.TestCase.assertEqual
    assert_not_equal = unittest.TestCase.assertNotEqual
    assert_greater = unittest.TestCase.assertGreater
    assert_greater_equal = unittest.TestCase.assertGreaterEqual
    assert_less = unittest.TestCase.assertLess
    assert_less_equal = unittest.TestCase.assertLessEqual

    assert_in = unittest.TestCase.assertIn

    assert_is = unittest.TestCase.assertIs
    assert_is_not = unittest.TestCase.assertIsNot
    assert_is_instance = unittest.TestCase.assertIsInstance
    assert_is_none = unittest.TestCase.assertIsNone
    assert_is_not_none = unittest.TestCase.assertIsNotNone
