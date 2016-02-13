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

import sys

import common

import uv


class TestTTY(common.TestCase):
    @common.skip_platform('win32')
    def test_tty(self):
        try:
            self.tty = uv.TTY(sys.stdin.fileno(), True)
            self.assert_true(bool(self.tty.console_size))
            width = self.tty.console_size.width
            height = self.tty.console_size.height
            self.tty.set_mode(uv.TTYMode.NORMAL)
            uv.tty.reset_mode()
            self.tty.close()
            self.assert_equal(self.tty.console_size, (0, 0))
            self.assert_raises(uv.ClosedHandleError, self.tty.set_mode)
        except uv.UVError or ValueError:
            pass
