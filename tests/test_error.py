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

import errno

import common

import uv


class TestError(common.TestCase):
    def test_code_get(self):
        self.assert_equal(uv.StatusCodes.get(0), uv.StatusCodes.SUCCESS)
        for code in uv.StatusCodes:
            self.assert_equal(uv.StatusCodes.get(code), int(code))
        self.assert_equal(uv.StatusCodes.get(42), 42)
        eagain_exception = uv.StatusCodes.EAGAIN.exception
        self.assert_is(eagain_exception, uv.error.TemporaryUnavailableError)

    def test_raise(self):
        def test1():
            raise uv.UVError(int(uv.StatusCodes.EAGAIN))

        def test2():
            raise uv.UVError(42)

        self.assert_raises(uv.error.TemporaryUnavailableError, test1)
        self.assert_raises(uv.UVError, test2)

    def test_unknown(self):
        self.assert_equal(uv.UVError(42).name, 'UNKNOWN')

    def test_name(self):
        self.assert_equal(uv.UVError(int(uv.StatusCodes.EAGAIN)).name, 'EAGAIN')

    def test_os_error_number(self):
        status_code = uv.StatusCodes.from_error_number(errno.EAGAIN)
        self.assert_is(status_code, uv.StatusCodes.EAGAIN)
