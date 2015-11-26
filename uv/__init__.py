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

"""
This package aims to provide an object oriented CFFI based wrapper around
the LibUV asynchronous IO library. It supports all handles as well as
filesystem operations, dns utility functions and miscellaneous utilities.

There are no plans to support the thread pool work scheduling or the
threading and synchronization utilities because Python already provides
nice solutions for those things in the standard library.

Based on Python's standard library's SSL module this package also provides
support for asynchronous SSL sockets.

As you may have noticed this package is not totally PEP-8 conform when
it comes to the maximum line length of 79 characters – instead we are
using a maximum line length of 90 characters. This allows us to use
longer and more expressive variable names without ugly line breaking
stunts and overall makes the code more readable.
"""

__version__ = '0.0.4'
__project__ = 'Python LibUV CFFI Bindings'
__author__ = 'Maximilian Köhl'
__email__ = 'mail@koehlma.de'

from .library import version as uv_version

from .error import UVError, StatusCode
from .handle import Handle, handles, close_all_handles
from .loop import RunMode, Loop, loops
from .request import Request
from .stream import Stream, ShutdownRequest, ConnectRequest, WriteRequest

from .async import Async
from .check import Check
from .idle import Idle
from .pipe import Pipe
from .poll import Poll, PollEvent
from .prepare import Prepare
from .process import Process, ProcessFlags, PIPE, disable_stdio_inheritance
from .signal import Signal, Signals
from .tcp import TCP, TCPFlags
from .timer import Timer
from .tty import TTY, TTYMode
from .udp import UDP, UDPFlags, Membership

from .fs_event import FSEvent
from .fs_poll import FSPoll

#from . import ssl

from . import dns
from . import fs
from . import library
from . import misc


