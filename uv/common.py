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

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import platform
import sys

from collections import OrderedDict

from . import library
from .library import ffi

is_py2 = sys.version_info[0] == 2
is_py3 = sys.version_info[0] == 3


is_pypy = platform.python_implementation().lower() == 'pypy'
is_cpython = platform.python_implementation().lower() == 'cpython'


def with_metaclass(meta, *bases):
    class Metaclass(meta):
        def __new__(cls, name, _, attributes):
            return meta(name, bases, attributes)
    return type.__new__(Metaclass, str('Metaclass'), (), {})


class _EnumerationMeta(type):
    _members = []
    _value_member_map = {}

    def __prepare__(mcs, *args, **kwargs):
        return OrderedDict()

    def __new__(mcs, name, bases, attributes):
        members = [(name, value) for name, value in attributes.items()
                   if not (hasattr(value, '__get__') or hasattr(value, '__set__') or
                           hasattr(value, '__delete__') or name.startswith('_'))]
        for name, value in members: del attributes[name]
        attributes['_members'] = members
        attributes['_value_member_map'] = {}
        cls = type.__new__(mcs, name, bases, attributes)
        for name, value in members:
            cls._value_member_map[name] = cls(value)
            setattr(cls, name, cls._value_member_map[name])
        return cls

    def __call__(cls, value):
        try: return cls._value_member_map[value]
        except KeyError: return cls.__new__(cls, value)

    def __iter__(cls):
        return cls._members

try:
    from enum import IntEnum as Enumeration
except ImportError:
    class Enumeration(with_metaclass(_EnumerationMeta, int)): pass


is_posix = os.name == 'posix'
is_nt = os.name == 'nt'
is_linux = sys.platform.startswith('linux')
is_win32 = sys.platform == 'win32'


def dummy_callback(*arguments, **keywords): pass


class Buffers(tuple):
    __slots__ = []

    def __new__(cls, buffers):
        """
        :type buffers: list[bytes] | bytes
        :rtype: uv.Buffers
        """
        buffers = [buffers] if isinstance(buffers, bytes) else buffers
        c_buffers = [ffi.new('char[]', buf) for buf in buffers]
        uv_buffers = ffi.new('uv_buf_t[]', len(buffers))
        for index, buf in enumerate(buffers):
            library.uv_buffer_set(ffi.addressof(uv_buffers[index]), c_buffers[index],
                                  len(buf))
        return tuple.__new__(cls, (c_buffers, uv_buffers))

    def __len__(self):
        return len(self[0])

    @property
    def c_buffers(self):
        """
        :rtype: list[ffi.CData]
        """
        return self[0]

    @property
    def uv_buffers(self):
        """
        :rtype: ffi.CData
        """
        return self[1]