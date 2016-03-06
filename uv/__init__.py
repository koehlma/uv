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

from __future__ import print_function, unicode_literals, division, absolute_import

from .metadata import __version__, __author__, __email__, __project__

from .library import version as uv_version

from .error import UVError, ClosedHandleError, ClosedLoopError, StatusCodes
from .handle import UVHandle
from .loop import RunModes, Loop
from .request import UVRequest

from . import common, error, loop, handle, request

from .abstract import Handle, Request, Stream

from .handles.async import Async
from .handles.check import Check
from .handles.idle import Idle
from .handles.pipe import PipeConnectRequest, Pipe
from .handles.poll import PollEvent, Poll
from .handles.prepare import Prepare
from .handles.process import CreatePipe, PIPE, ProcessFlags, Process
from .handles.signal import Signals, Signal
from .handles.stream import ShutdownRequest, WriteRequest, ConnectRequest, UVStream
from .handles.tcp import TCPFlags, TCPConnectRequest, TCP
from .handles.timer import Timer
from .handles.tty import ConsoleSize, TTYMode, TTY
from .handles.udp import UDPFlags, UDPMembership, UDPSendRequest, UDP

from .handles.fs_event import FSEvents, FSEventFlags, FSEvent
from .handles.fs_poll import FSPoll

from .handles import async
from .handles import check
from .handles import idle
from .handles import pipe
from .handles import process
from .handles import signal
from .handles import stream
from .handles import tcp
from .handles import timer
from .handles import tty
from .handles import udp

from .handles import fs_event
from .handles import fs_poll

from .dns import (AddressFamilies, SocketTypes, SocketProtocols, Address, Address4,
                  Address6, AddrInfo, NameInfo, getnameinfo, getaddrinfo)

from .fs import Stat

from . import dns
from . import fs
from . import misc
from . import secure
