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

from . import base, common, error, library
from .library import ffi, lib
from .loop import Loop

__all__ = ['Request']


class RequestType(common.Enumeration):
    UNKNOWN = lib.UV_UNKNOWN_REQ
    CONNECT = lib.UV_CONNECT
    WRITE = lib.UV_WRITE
    SHUTDOWN = lib.UV_SHUTDOWN
    FS = lib.UV_FS
    WORK = lib.UV_WORK
    GETADDRINFO = lib.UV_GETADDRINFO
    GETNAMEINFO = lib.UV_GETNAMEINFO
    UDP_SEND = lib.UV_UDP_SEND

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

    __slots__ = ['__weakref__', 'uv_request', '_c_reference', 'finished', 'loop',
                 'base_request']

    uv_request_type = None
    uv_request_init = None

    def __init__(self, loop, *arguments, **keywords):
        uv_handle = keywords.get('uv_handle')
        request_init = keywords.get('request_init')
        self.loop = loop or Loop.get_current()
        """
        Loop where the request is running on.

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
            raise error.ClosedLoopError()
        self.base_request = base.BaseRequest(self, self.loop.base_loop,
                                             self.uv_request_type,
                                             request_init or self.uv_request_init,
                                             arguments,
                                             uv_handle=uv_handle)
        self.set_pending()

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
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def set_pending(self):
        """
        .. warning::
            This method is only for internal purposes and is not part
            of the official API. It deactivates the garbage collection
            for the request which means the request and the associated
            loop are excluded form garbage collection. You should never
            call it directly!
        """
        self.loop.structure_set_pending(self)

    def clear_pending(self):
        """
        .. warning::
            This method is only for internal purposes and is not part
            of the official API. It reactivates the garbage collection
            for the request. You should never call it directly!
        """
        self.loop.structure_clear_pending(self)


RequestType.cls = Request
