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

from __future__ import print_function, unicode_literals, division, absolute_import

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

__version__ = '0.0.5.dev0'
__project__ = 'Python libuv CFFI Bindings'
__author__ = 'Maximilian Köhl'
__email__ = 'mail@koehlma.de'

from .library import version as uv_version

from .common import is_win32, is_linux, is_posix, is_nt, is_py3, is_py2

from .error import UVError, HandleClosedError, LoopClosedError, StatusCode
from .handle import Handle
from .loop import RunModes, Loop
from .request import Request

from .handles.async import *
from .handles.check import *
from .handles.idle import *
from .handles.pipe import *
from .handles.poll import *
from .handles.prepare import *
from .handles.process import *
from .handles.process import *
from .handles.signal import *
from .handles.stream import *
from .handles.tcp import *
from .handles.timer import *
from .handles.tty import *
from .handles.udp import *

from .handles.fs_event import *
from .handles.fs_poll import *

from .dns import Address, Address4, Address6, AddrInfo
from .fs import Stat

from . import dns
from . import fs
from . import misc
