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

from .library import ffi, uv_buffer_set


class Buffers(tuple):
    __slots__ = []

    def __new__(cls, buffers):
        """
        :type buffers: list[bytes] | bytes
        :rtype: uv.Buffers
        """
        buffers = [buffers] if isinstance(buffers, bytes) else buffers
        c_buffers = [ffi.new('char[]', buf) for buf in buffers]
        uv_buffers = ffi.new('uv_buf_t[]', len(buffers))
        for index, buf in enumerate(buffers):
            uv_buffer_set(ffi.addressof(uv_buffers[index]), c_buffers[index], len(buf))
        return tuple.__new__(cls, (c_buffers, uv_buffers))

    def __len__(self):
        return len(self[0])

    @property
    def c_buffers(self):
        """
        :rtype: list[ffi.CData]
        """
        return self[0]

    @property
    def uv_buffers(self):
        """
        :rtype: ffi.CData
        """
        return self[1]