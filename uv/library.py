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

import collections
import os
import sys
import weakref

from . import __version__


if os.environ.get('PYTHON_MOCK_LIBUV', None) == 'True':  # pragma: no cover
    from types import ModuleType

    from .helpers.mock import Mock

    uvcffi = ModuleType('uvcffi')
    uvcffi.__version__ = __version__
    uvcffi.ffi = Mock()
    uvcffi.lib = Mock()

    sys.modules['uvcffi'] = uvcffi

    c_library_version = __version__
else:
    import uvcffi

    c_library_version = uvcffi.ffi.string(uvcffi.lib.PYTHON_UV_CFFI_VERSION).decode()


if uvcffi.__version__ != __version__:  # pragma: no cover
    raise RuntimeError('incompatible cffi base library (%s)' % uvcffi.__version__)

if c_library_version != __version__:  # pragma: no cover
    raise RuntimeError('incompatible cffi c library (%s)' % c_library_version)


trace_uvcffi = os.environ.get('PYTHON_TRACE_LIBUV', None) == 'True'

if trace_uvcffi:  # pragma: no cover
    from .helpers.tracer import LIBTracer, FFITracer

    lib = LIBTracer()
    ffi = FFITracer()
else:
    ffi = uvcffi.ffi
    lib = uvcffi.lib


Version = collections.namedtuple('Version', ['string', 'major', 'minor', 'patch'])
version_string = ffi.string(lib.uv_version_string()).decode()
version_hex = lib.uv_version()
version_major = (version_hex >> 16) & 0xff
version_minor = (version_hex >> 8) & 0xff
version_patch = version_hex & 0xff
version = Version(version_string, version_major, version_minor, version_patch)


def uv_buffer_set(uv_buffer, c_base, length):
    """
    Set libuv buffer information.

    :param uv_buffer:
        libuv buffer
    :param c_base:
        buffer base which should be set
    :param length:
        buffer length which should be set

    :type uv_buffer:
        ffi.CData[uv_buf_t]
    :type c_base:
        ffi.CData[char*]
    :type length:
        int
    """
    lib.py_uv_buf_set(uv_buffer, c_base, length)


UVBuffer = collections.namedtuple('UVBuffer', ['base', 'length'])


def uv_buffer_get(uv_buffer):
    """
    Get libuv buffer information.

    :param uv_buffer:
        libuv buffer

    :type uv_buffer:
        ffi.CData[uv_buf_t]

    :return:
        buffer information `(base, len)`
    :rtype:
        UVBuffer[ffi.CData[char*], int]
    """
    length_pointer = ffi.new('unsigned long*')
    return UVBuffer(lib.py_uv_buf_get(uv_buffer, length_pointer), length_pointer[0])


_c_dependencies = weakref.WeakKeyDictionary()


def c_require(structure, *requirements):
    try:
        _c_dependencies[structure].append(requirements)
    except KeyError:
        _c_dependencies[structure] = [requirements]


def make_uv_buffers(iterable_or_bytes):
    if isinstance(iterable_or_bytes, bytes):
        buffers = (iterable_or_bytes, )
    elif isinstance(iterable_or_bytes, (list, tuple)):
        buffers = iterable_or_bytes
    elif isinstance(iterable_or_bytes, collections.Iterable):
        buffers = [bytes(item) for item in iterable_or_bytes]
    else:
        raise Exception('fix me')
    c_buffers = [ffi.new('char[]', item) for item in buffers]
    uv_buffers = ffi.new('uv_buf_t[]', len(buffers))
    c_require(uv_buffers, c_buffers)
    for index, c_base in enumerate(c_buffers):
        lib.py_uv_buf_set(uv_buffers + index, c_base, len(c_base) - 1)
    return uv_buffers
