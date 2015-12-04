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

from ..library import ffi, lib, detach

from ..common import dummy_callback
from ..error import UVError, HandleClosedError
from ..handle import HandleType, Handle

__all__ = ['Prepare']


@ffi.callback('uv_prepare_cb')
def uv_prepare_cb(uv_prepare):
    prepare = detach(uv_prepare)
    with prepare.loop.callback_context:
        prepare.on_prepare(prepare)


@HandleType.PREPARE
class Prepare(Handle):
    """
    Prepare handles will run the given callback once per loop iteration,
    right before polling for IO.

    :raises uv.UVError: error during the initialization of the handle

    :param loop: event loop which should be used for the handle
    :param on_prepare: callback which should be called right before polling for IO

    :type loop: Loop
    :type on_prepare: (uv.Prepare) -> None
    """
    __slots__ = ['uv_prepare', 'on_prepare']

    def __init__(self, loop=None, on_prepare=None):
        self.uv_prepare = ffi.new('uv_prepare_t*')
        super(Prepare, self).__init__(self.uv_prepare, loop)
        self.on_prepare = on_prepare or dummy_callback
        """
        Callback which should be called before polling for IO.

        .. function:: on_prepare(Prepare-Handle)

        :readonly: False
        :type: (uv.Prepare) -> None
        """
        code = lib.uv_prepare_init(self.loop.uv_loop, self.uv_prepare)
        if code < 0:
            self.destroy()
            raise UVError(code)

    def start(self, on_prepare=None):
        """
        Starts the handle.

        :raises uv.UVError: error while starting the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param on_prepare: callback which should be called before polling for IO
        :type on_prepare: (uv.Prepare) -> None
        """
        if self.closing: raise HandleClosedError()
        self.on_prepare = on_prepare or self.on_prepare
        code = lib.uv_prepare_start(self.uv_prepare, uv_prepare_cb)
        if code < 0: raise UVError(code)

    def stop(self):
        """
        Stops the handle, the callback will no longer be called.

        :raises uv.UVError: error while stopping the handle
        """
        if self.closing: return
        code = lib.uv_prepare_stop(self.uv_prepare)
        if code < 0: raise UVError(code)

    def destroy(self):
        self.uv_prepare = None
        super(Prepare, self).destroy()

    __call__ = start
