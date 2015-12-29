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

import os
import unittest

import uv

from uv.common import dummy_callback, is_py3

PY2_RERAISE = '''
def reraise(exc_type, exc_value, exc_traceback):
    raise exc_type, exc_value, exc_traceback
'''

if is_py3:
    def reraise(exc_type, exc_value, exc_traceback):
        raise exc_value.with_traceback(exc_traceback)
else:
    exec(PY2_RERAISE)


if uv.is_win32:
    TEST_PIPE1 = r'\\?\pipe\python-uv-test1'
    TEST_PIPE2 = r'\\?\pipe\python-uv-test2'
else:
    TEST_PIPE1 = '/tmp/python-uv-test1'
    TEST_PIPE2 = '/tmp/python-uv-test2'

BAD_PIPE = '/path/to/unix/socket/that/really/should/not/be/there'

TEST_IPV4 = '127.0.0.1'
TEST_IPV6 = '::1'

TEST_PORT1 = 12345
TEST_PORT2 = 12346

try: os.remove(TEST_PIPE1)
except: pass

try: os.remove(TEST_PIPE2)
except: pass


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
        return True

    def run(self, mode=uv.RunModes.DEFAULT):
        self.exc_type = None
        result = super(TestLoop, self).run(mode)
        if self.exc_type is not None:
            reraise(self.exc_type, self.exc_value, self.exc_traceback)
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
