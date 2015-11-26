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

import cffi

declarations = '''
{declarations}
'''

source = '''
{source}
'''


try:
    from _uvcffi import ffi, lib
except ImportError:
    ffi = cffi.FFI()
    ffi.cdef(declarations)
    try:
        ffi.set_source('_uvcffi', source, libraries=['uv'])
        ffi.compile()
        from _uvcffi import ffi, lib
    except AttributeError or ImportError:
        lib = ffi.verify(source, libraries=['uv'], modulename='_uvcffi')
