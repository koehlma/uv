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

"""
This package aims to provide an object oriented CFFI based wrapper around
the libuv asynchronous IO library. It supports all handles as well as
filesystem operations, dns utility functions and miscellaneous utilities.

There are no plans to support the thread pool work scheduling and the
threading and synchronization utilities because Python already provides
nice solutions for those things in the standard library.

Based on Python's standard library's SSL module this package also provides
support for asynchronous SSL sockets.

As you may have noticed this package is not totally PEP-8 conform when it
comes to the maximum line length of 79 characters – instead we are using
a maximum line length of 90 characters. This allows us to use longer and
more expressive variable names without ugly line breaking stunts and
overall makes the code more readable.
"""

__version__ = '0.0.4.dev0'
__project__ = 'Python libuv CFFI Bindings'
__author__ = 'Maximilian Köhl'
__email__ = 'mail@koehlma.de'

from .library import version as uv_version

from .error import UVError, HandleClosedError, LoopClosedError, StatusCode
from .handle import Handle
from .loop import RunMode, Loop
from .request import Request

from .handles.async import Async
from .handles.check import Check
from .handles.idle import Idle
from .handles.pipe import Pipe
from .handles.poll import Poll, PollEvent
from .handles.prepare import Prepare
from .handles.process import Process
from .handles.signal import Signal, Signals
from .handles.stream import Stream
from .handles.tcp import TCP
from .handles.timer import Timer
from .handles.tty import TTY
from .handles.udp import UDP

from . import dns
from . import fs
from . import misc
