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

import os
import sys

from collections import namedtuple
from weakref import WeakKeyDictionary

from uv import __version__

import uvcffi

if uvcffi.__version__ != __version__:
    raise RuntimeError('incompatible CFFI base library (%s)' % uvcffi.__version__)


ffi = uvcffi.ffi
lib = uvcffi.lib


Version = namedtuple('Version', ['string', 'major', 'minor', 'patch'])
version_string = ffi.string(lib.uv_version_string()).decode()
version_hex = lib.uv_version()
version_major = (version_hex >> 16) & 0xff
version_minor = (version_hex >> 8) & 0xff
version_patch = version_hex & 0xff
version = Version(version_string, version_major, version_minor, version_patch)


Attachment = namedtuple('Attachment', ['data', 'reference'])


def attach(structure, instance):
    attachment = Attachment(ffi.new('py_data*'), ffi.new_handle(instance))
    lib.py_attach(attachment.data, attachment.reference)
    structure.data = attachment.data
    return attachment


def detach(structure):
    data = lib.py_detach(structure.data)
    if data: return ffi.from_handle(data.object)


def attach_loop(structure, loop):
    attachment = Attachment(ffi.new('py_loop_data*'), ffi.new_handle(loop))
    lib.py_loop_attach(attachment.data, attachment.reference)
    structure.data = attachment.data
    return attachment


def detach_loop(structure):
    data = lib.py_loop_detach(structure.data)
    if data: return ffi.from_handle(data.object)


_c_dependencies = WeakKeyDictionary()


def c_require(structure, *dependencies):
    if structure not in _c_dependencies:
        _c_dependencies[structure] = []
    _c_dependencies[structure] += dependencies


def dummy_callback(*_):
    pass


def str_py2c(string: str):
    return ffi.new('char[]', str(string).encode())


def str_c2py(cdata: ffi.CData):
    return ffi.string(cdata).decode()


is_posix = os.name == 'posix'
is_nt = os.name == 'nt'
is_linux = sys.platform.startswith('linux')
is_win32 = sys.platform == 'win32'
