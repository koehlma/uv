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

from collections import OrderedDict, namedtuple

from uv import __version__


is_py2 = sys.version_info[0] == 2
is_py3 = sys.version_info[0] == 3


def with_metaclass(meta, *bases):
    class Metaclass(meta):
        def __new__(cls, name, _, attributes):
            return meta(name, bases, attributes)
    return type.__new__(Metaclass, str('Metaclass'), (), {})


class _EnumerationMeta(type):
    value2member = {}

    def __prepare__(mcs, cls, bases):
        return OrderedDict()

    def __new__(mcs, name, bases, attributes):
        members = [(name, value) for name, value in attributes.items()
                   if not (hasattr(value, '__get__') or hasattr(value, '__set__') or
                           hasattr(value, '__delete__') or name.startswith('_'))]
        for name, value in members: del attributes[name]
        attributes['value2member'] = {}
        cls = type.__new__(mcs, name, bases, attributes)
        for name, value in members:
            cls.value2member[name] = cls(value)
            setattr(cls, name, cls.value2member[name])
        return cls

    def __call__(cls, value):
        try: return cls.value2member[value]
        except KeyError: return cls.__new__(cls, value)


try:
    from enum import IntEnum as Enumeration
except ImportError:
    class Enumeration(with_metaclass(_EnumerationMeta, int)): pass


MOCK_CONSTANTS = {
    'UV_READABLE': 1,
    'UV_WRITABLE': 2,

    'UV_E2BIG': -7,
    'UV_EACCES': -13,
    'UV_EADDRINUSE': -98,
    'UV_EADDRNOTAVAIL': -99,
    'UV_EAFNOSUPPORT': -97,
    'UV_EAGAIN': -11,
    'UV_EAI_ADDRFAMILY': -3000,
    'UV_EAI_AGAIN': -3001,
    'UV_EAI_BADFLAGS': -3002,
    'UV_EAI_BADHINTS': -3013,
    'UV_EAI_CANCELED': -3003,
    'UV_EAI_FAIL': -3004,
    'UV_EAI_FAMILY': -3005,
    'UV_EAI_MEMORY': -3006,
    'UV_EAI_NODATA': -3007,
    'UV_EAI_NONAME': -3008,
    'UV_EAI_OVERFLOW': -3009,
    'UV_EAI_PROTOCOL': -3014,
    'UV_EAI_SERVICE': -3010,
    'UV_EAI_SOCKTYPE': -3011,
    'UV_EALREADY': -114,
    'UV_EBADF': -9,
    'UV_EBUSY': -16,
    'UV_ECANCELED': -125,
    'UV_ECHARSET': -4080,
    'UV_ECONNABORTED': -103,
    'UV_ECONNREFUSED': -111,
    'UV_ECONNRESET': -104,
    'UV_EDESTADDRREQ': -89,
    'UV_EEXIST': -17,
    'UV_EFAULT': -14,
    'UV_EFBIG': -27,
    'UV_EHOSTUNREACH': -113,
    'UV_EINTR': -4,
    'UV_EINVAL': -22,
    'UV_EIO': -5,
    'UV_EISCONN': -106,
    'UV_EISDIR': -21,
    'UV_ELOOP': -40,
    'UV_EMFILE': -24,
    'UV_EMSGSIZE': -90,
    'UV_ENAMETOOLONG': -36,
    'UV_ENETDOWN': -100,
    'UV_ENETUNREACH': -101,
    'UV_ENFILE': -23,
    'UV_ENOBUFS': -105,
    'UV_ENODEV': -19,
    'UV_ENOENT': -2,
    'UV_ENOMEM': -12,
    'UV_ENONET': -64,
    'UV_ENOPROTOOPT': -92,
    'UV_ENOSPC': -28,
    'UV_ENOSYS': -38,
    'UV_ENOTCONN': -107,
    'UV_ENOTDIR': -20,
    'UV_ENOTEMPTY': -39,
    'UV_ENOTSOCK': -88,
    'UV_ENOTSUP': -95,
    'UV_EPERM': -1,
    'UV_EPIPE': -32,
    'UV_EPROTO': -71,
    'UV_EPROTONOSUPPORT': -93,
    'UV_EPROTOTYPE': -91,
    'UV_ERANGE': -34,
    'UV_EROFS': -30,
    'UV_ESHUTDOWN': -108,
    'UV_ESPIPE': -29,
    'UV_ESRCH': -3,
    'UV_ETIMEDOUT': -110,
    'UV_ETXTBSY': -26,
    'UV_EXDEV': -18,
    'UV_UNKNOWN': -4094,
    'UV_EOF': -4095,
    'UV_ENXIO': -6,
    'UV_EMLINK': -31,
    'UV_EHOSTDOWN': -112
}


class Mock(object):
    def __getattr__(self, name):
        try:
            return MOCK_CONSTANTS[name]
        except KeyError:
            return Mock()

    def __call__(self, *args):
        return args[0] if len(args) == 1 and type(args[0]) == type else 0

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


if os.environ.get('MOCK_UVCFFI', None) == 'True':
    mock = Mock()

    class _Module(object):
        __version__ = __version__
        ffi = Mock()
        lib = Mock()

    uvcffi = _Module()
else:
    import uvcffi

    del MOCK_CONSTANTS


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

trace_calls = os.environ.get('PYTHON_UV_TRACER', None) == 'True'

wrapper_codes = set()


class LIBTracer:
    def __init__(self):
        self.wrappers = {}

    def __getattr__(self, name):
        item = getattr(uvcffi.lib, name)
        if name in self.wrappers: return self.wrappers[name]
        if callable(item):
            def trace_wrapper(*arguments):
                stack = [info for info in inspect.stack()
                         if info.frame.f_code not in wrapper_codes]
                stack.reverse()
                self.on_call(stack, item, arguments)
                result = item(*arguments)
                self.on_return(stack, item, arguments, result)
                return result
            self.wrappers[name] = trace_wrapper
            wrapper_codes.add(trace_wrapper.__code__)
            return trace_wrapper
        return item

    @staticmethod
    def on_call(stack, function, arguments):
        trace = ' -> '.join(map(lambda info: info.function, stack))
        print('lib-trace      :', trace)
        print('lib-call       : {}{}'.format(function.__name__, arguments))

    @staticmethod
    def on_return(stack, function, arguments, result):
        trace = ' -> '.join(map(lambda info: info.function, stack))
        print('lib-trace      :', trace)
        print('lib-return     : {}{}: {}'.format(function.__name__, arguments, result))


class FFITracer:
    def __getattr__(self, name):
        return getattr(uvcffi.ffi, name)

    def callback(self, callback_type, function=None):
        if function is None: return functools.partial(self.callback, callback_type)

        def wrapper(*arguments):
            stack = [info for info in inspect.stack()
                     if info.frame.f_code not in wrapper_codes]
            stack.reverse()
            self.on_callback_call(stack, function, arguments)
            result = function(*arguments)
            self.on_callback_return(stack, function, arguments, result)
            return result

        wrapper_codes.add(wrapper.__code__)
        return uvcffi.ffi.callback(callback_type, wrapper)

    @staticmethod
    def on_callback_call(stack, function, arguments):
        trace = ' -> '.join(map(lambda info: info.function, stack))
        print('callback-trace :', trace)
        print('callback-call  : {}{}'.format(function.__name__, arguments))

    @staticmethod
    def on_callback_return(stack, function, arguments, result):
        trace = ' -> '.join(map(lambda info: info.function, stack))
        print('callback-trace :', trace)
        print('callback-return: {}{}: {}'.format(function.__name__, arguments, result))


if trace_calls:
    import inspect
    import functools

    lib = LIBTracer()
    ffi = FFITracer()





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


def dummy_callback(*_):
    pass


def str_py2c(string):
    return ffi.new('char[]', str(string).encode())


def str_c2py(cdata):
    return ffi.string(cdata).decode()


is_posix = os.name == 'posix'
is_nt = os.name == 'nt'
is_linux = sys.platform.startswith('linux')
is_win32 = sys.platform == 'win32'
