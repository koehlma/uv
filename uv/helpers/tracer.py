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

from __future__ import absolute_import, division, print_function, unicode_literals

import functools
import inspect

import uvcffi


wrapper_codes = set()


class LIBTracer(object):
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


class FFITracer(object):
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
