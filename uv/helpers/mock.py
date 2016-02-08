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


MOCK_CONSTANTS = {
    'UV_RUN_DEFAULT': 0,
    'UV_RUN_ONCE': 1,
    'UV_RUN_NOWAIT': 2,

    'UV_READABLE': 1,
    'UV_WRITABLE': 2,

    'UV_RENAME': 1,
    'UV_CHANGE': 2,

    'UV_FS_EVENT_WATCH_ENTRY': 1,
    'UV_FS_EVENT_STAT': 2,
    'UV_FS_EVENT_RECURSIVE': 4,

    'UV_TCP_IPV6ONLY': 1,

    'UV_UDP_IPV6ONLY': 1,
    'UV_UDP_PARTIAL': 2,
    'UV_UDP_REUSEADDR': 4,

    'UV_LEAVE_GROUP': 0,
    'UV_JOIN_GROUP': 1,

    'UV_CREATE_PIPE': 1,
    'UV_READABLE_PIPE': 16,
    'UV_WRITABLE_PIPE': 32,

    'UV_PROCESS_DETACHED': 1 << 3,
    'UV_PROCESS_WINDOWS_VERBATIM_ARGUMENTS': 1 << 2,
    'UV_PROCESS_WINDOWS_HIDE': 1 << 4,

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
    def uv_version():
        return 0

    @staticmethod
    def string(string):
        return string.encode()

    @staticmethod
    def callback(*_):
        return Mock()
