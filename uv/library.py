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

import os
import sys

from collections import namedtuple

from . import __version__

__all__ = ['lib', 'ffi', 'version', ]


if os.environ.get('PYTHON_MOCK_LIBUV', None) == 'True':
    from types import ModuleType

    from .helpers.mock import Mock

    uvcffi = ModuleType('uvcffi')
    uvcffi.__version__ = __version__
    uvcffi.ffi = Mock()
    uvcffi.lib = Mock()

    sys.modules['uvcffi'] = uvcffi
else:
    import uvcffi


if uvcffi.__version__ != __version__:
    raise RuntimeError('incompatible cffi base library (%s)' % uvcffi.__version__)


trace_uvcffi = os.environ.get('PYTHON_TRACE_LIBUV', None) == 'True'

if trace_uvcffi:
    from .helpers.tracer import LIBTracer, FFITracer

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


Attachment = namedtuple('Attachment', ['c_data', 'c_reference'])


def attach(c_structure, instance):
    """
    Attach a python object to a C data structure's `data` field using
    :func:`ffi.new_handle`. The returned reference must be stored in
    order to receive the original object with :func:`detach`.

    :param c_structure:
        C structure with data field of type `void*`
    :param instance:
        python instance to attach

    :type c_structure:
        ffi.CData
    :type instance:
        object

    :return:
        reference of type `void*` (needs to be stored)
    :rtype:
        ffi.CData[void*]
    """
    c_reference = ffi.new_handle(instance)
    c_structure.data = c_reference
    return c_reference


def detach(c_structure):
    """
    Detach a python object from a C data structure's data field using
    :func:`ffi.from_handle`. This might segfault on CPython if the
    referenced python object or the reference itself has been garbage
    collected. On PyPy it returns `None` in these cases.

    :param c_structure:
        C structure with data field of type `void*`

    :return:
        attached python instance if found
    :rtype:
        Optional[object]
    """
    if c_structure.data:
        try:
            # NOTE: on CPython this might segfault if the pointer is not valid
            instance = ffi.from_handle(c_structure.data)
            return instance
        except SystemError:
            pass


def mutable_c_string(string):
    return ffi.new('char[]', str(string).encode())


def str_c2py(c_string):
    return ffi.string(c_string).decode()


def uv_buffer_set(uv_buffer, c_base, length):
    lib.cross_uv_buf_set(uv_buffer, c_base, length)


def uv_buffer_get_base(uv_buffer):
    return lib.cross_uv_buf_get_base(uv_buffer)
