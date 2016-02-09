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

import abc

from . import common


class Handle(common.with_metaclass(abc.ABCMeta)):
    @abc.abstractproperty
    def closing(self):
        pass

    @abc.abstractproperty
    def closed(self):
        pass

    @abc.abstractproperty
    def active(self):
        pass

    @abc.abstractproperty
    def referenced(self):
        pass

    @abc.abstractmethod
    def reference(self):
        pass

    @abc.abstractmethod
    def dereference(self):
        pass

    @abc.abstractmethod
    def close(self, on_closed=None):
        pass


class Request(common.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def cancel(self):
        pass


class Stream(common.with_metaclass(abc.ABCMeta)):
    @abc.abstractproperty
    def readable(self):
        pass

    @abc.abstractproperty
    def writeable(self):
        pass

    @abc.abstractmethod
    def read_start(self, on_read=None):
        pass

    @abc.abstractmethod
    def read_stop(self):
        pass

    @abc.abstractmethod
    def write(self, buffers, send_stream=None, on_write=None):
        pass

    @abc.abstractmethod
    def shutdown(self, on_shutdown=None):
        pass
