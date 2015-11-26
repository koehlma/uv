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

__version__ = '{version}'
__project__ = 'Python LibUV CFFI Bindings'
__author__ = 'Maximilian Köhl'
__email__ = 'mail@koehlma.de'


class Mock:
    def __getattr__(self, _):
        return Mock()

    def __call__(self, *args):
        if len(args) == 1 and type(args[0]) == type:
            return args[0]
        return 0

    def __or__(self, _):
        return 0

    @staticmethod
    def uv_version_string():
        return '0.0.0'

    @staticmethod
    def string(string):
        return string.encode()

    @staticmethod
    def callback(*_):
        return Mock()

lib = Mock()
ffi = Mock()
