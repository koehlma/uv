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

from uv import __version__

import uvcffi

if uvcffi.__version__ != __version__:
    raise RuntimeError('incompatible CFFI base library (%s)' % uvcffi.__version__)


ffi = uvcffi.ffi
lib = uvcffi.lib

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
