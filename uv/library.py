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

from __future__ import print_function, unicode_literals, division

import os
import sys
from collections import namedtuple

from . import __version__


if os.environ.get('MOCK_UVCFFI', None) == 'True':
    from types import ModuleType

    from .mock import Mock

    uvcffi = ModuleType('uvcffi')
    uvcffi.__version__ = __version__
    uvcffi.ffi = Mock()
    uvcffi.lib = Mock()

    sys.modules['uvcffi'] = uvcffi


import uvcffi

if uvcffi.__version__ != __version__:
    raise RuntimeError('incompatible CFFI base library (%s)' % uvcffi.__version__)


trace_uvcffi = os.environ.get('TRACE_UVCFFI', None) == 'True'

if trace_uvcffi:
    from .tracer import LIBTracer, FFITracer

    lib = LIBTracer()
    ffi = FFITracer()
else:
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


def str_py2c(string):
    return ffi.new('char[]', str(string).encode())


def str_c2py(cdata):
    return ffi.string(cdata).decode()


