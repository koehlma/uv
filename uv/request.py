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

from . import common, error, library
from .library import ffi, lib
from .loop import Loop

__all__ = ['Request']


class RequestType(common.Enumeration):
    UNKNOWN = lib.UV_UNKNOWN_REQ
    CONNECT = lib.UV_CONNECT
    WRITE = lib.UV_WRITE
    SHUTDOWN = lib.UV_SHUTDOWN
    SEND = lib.UV_UDP_SEND
    FS = lib.UV_FS
    WORK = lib.UV_WORK
    GETADDRINFO = lib.UV_GETADDRINFO
    GETNAMEINFO = lib.UV_GETNAMEINFO

    def __call__(self, cls):
        self.cls = cls
        return cls


@RequestType.UNKNOWN
class Request(object):
    """
    Requests represent (typically) short-lived operations. These operations
    can be performed over a handle: write requests are used to write data
    on a handle; or standalone: getaddrinfo requests don’t need a handle
    they run directly on the loop. This is the base class of all requests.

    :raises uv.LoopClosedError: loop has already been closed

    :param uv_request: allocated c struct for this request
    :param loop: loop where the request should run on

    :type uv_request: ffi.CData
    :type loop: Loop
    """

    __slots__ = ['uv_request', 'attachment', 'finished', 'loop']

    def __init__(self, uv_request, loop=None):
        self.uv_request = ffi.cast('uv_req_t*', uv_request)
        self.attachment = library.attach(self.uv_request, self)
        self.loop = loop or Loop.get_current()
        """
        Loop where the handle is running on.

        :readonly: True
        :type: Loop
        """
        self.finished = False
        """
        Request has been finished.

        :readonly: True
        :type: bool
        """
        if self.loop.closed:
            self.finished = True
            raise error.LoopClosedError()
        self.loop.requests.add(self)

    @property
    def type(self):
        """
        Type of the request. Returns a subclass of :class:`uv.Request`.

        :type: type
        """
        return RequestType(self.uv_request.type).cls

    def cancel(self):
        """
        Cancel a pending request. Fails if the request is executing
        or has finished executing.

        :raises uv.UVError: error while canceling request
        """
        code = lib.uv_cancel(self.uv_request)
        if code < 0: raise error.UVError(code)

    def destroy(self):
        """
        .. warning::

            This method is used internally to free all allocated C
            resources. You should never call it directly!
        """
        if not self.finished:
            self.loop.requests.remove(self)
            self.finished = True


RequestType.cls = Request
