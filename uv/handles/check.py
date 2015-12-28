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

from ..library import ffi, lib, detach

from ..common import dummy_callback
from ..error import UVError, HandleClosedError
from ..handle import Handle, HandleType

__all__ = ['Check']


@ffi.callback('uv_check_cb')
def uv_check_cb(uv_check):
    check = detach(uv_check)
    with check.loop.callback_context:
        check.on_check(check)


@HandleType.CHECK
class Check(Handle):
    """
    Check handles will run the given callback once per loop iteration,
    right after polling for IO.

    :raises uv.UVError: error while initializing the handle

    :param loop: event loop the handle should run on
    :param on_check: callback called right after polling for IO

    :type loop: uv.Loop
    :type on_check: ((uv.Check) -> None) | ((Any, uv.Check) -> None)
    """

    __slots__ = ['uv_check', 'on_check']

    def __init__(self, loop=None, on_check=None):
        self.uv_check = ffi.new('uv_check_t*')
        super(Check, self).__init__(self.uv_check, loop)
        self.on_check = on_check or dummy_callback
        """
        Callback called right after polling for IO once per loop iteration.

        .. function:: on_check(Check)

        :readonly: False
        :type: ((uv.Check) -> None) | ((Any, uv.Check) -> None)
        """
        code = lib.uv_check_init(self.loop.uv_loop, self.uv_check)
        if code < 0:
            self.destroy()
            raise UVError(code)

    def start(self, on_check=None):
        """
        Starts the handle.

        :raises uv.UVError: error while starting the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param on_check: callback called right after polling for IO
        :type on_check: ((uv.Check) -> None) | ((Any, uv.Check) -> None)
        """
        if self.closing: raise HandleClosedError()
        self.on_check = on_check or self.on_check
        code = lib.uv_check_start(self.uv_check, uv_check_cb)
        if code < 0: raise UVError(code)

    def stop(self):
        """
        Stops the handle, the callback will no longer be called.

        :raises uv.UVError: error while stopping the handle
        """
        if self.closing: return
        code = lib.uv_check_stop(self.uv_check)
        if code < 0: raise UVError(code)

    __call__ = start
