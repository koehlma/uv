# -*- coding: utf-8 -*-
#
# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
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

from collections import OrderedDict


is_py2 = sys.version_info[0] == 2
is_py3 = sys.version_info[0] == 3


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
