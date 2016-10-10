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

from . import abstract, base, common, error
from .library import lib
from .loop import Loop

__all__ = ['UVRequest']


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
class UVRequest(object):
    """
    The base class of all libuv based requests.

    :raises uv.LoopClosedError:
        loop has already been closed

    :param loop:
        loop where the request should run on
    :param arguments:
        arguments passed to the libuv request initializer
    :param uv_handle:
        libuv handle the requests belongs to
    :param request_init:
        libuv function for request initialization

    :type loop:
        Loop
    :type arguments:
        tuple
    :type uv_handle:
        ffi.CData
    :type request_init:
        callable
    """

    __slots__ = ['__weakref__', 'loop', 'finished', 'base_request']

    uv_request_type = None
    uv_request_init = None

    def __init__(self, loop, arguments, uv_handle=None, request_init=None):
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
                                             self.__class__.uv_request_type,
                                             request_init or
                                             self.__class__.uv_request_init,
                                             arguments,
                                             uv_handle=uv_handle)
        self.set_pending()

    @property
    def type(self):
        """
        Type of the request. Returns a subclass of :class:`uv.UVRequest`.

        :type: type
        """
        return RequestType(self.base_request.uv_request.type).cls

    def cancel(self):
        """
        :raises uv.UVError: error while canceling request
        """
        code = self.base_request.cancel()
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)

    def set_pending(self):
        """
        .. warning::
            This method is only for internal purposes and is not part
            of the official API.
        """
        self.loop.structure_set_pending(self)

    def clear_pending(self):
        """
        .. warning::
            This method is only for internal purposes and is not part
            of the official API.
        """
        self.loop.structure_clear_pending(self)


RequestType.cls = UVRequest

abstract.Request.register(UVRequest)
