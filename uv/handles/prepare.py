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

from .. import common, error, handle, library
from ..library import ffi, lib

__all__ = ['Prepare']


@ffi.callback('uv_prepare_cb')
def uv_prepare_cb(uv_prepare):
    prepare = library.detach(uv_prepare)
    """ :type: uv.Prepare """
    if prepare is not None:
        try:
            prepare.on_prepare(prepare)
        except:
            prepare.loop.handle_exception()


@handle.HandleTypes.PREPARE
class Prepare(handle.Handle):
    """
    Prepare handles will run the given callback once per loop iteration,
    right before polling for IO.

    :raises uv.UVError: error while initializing the handle

    :param loop: event loop the handle should run on
    :param on_prepare: callback called right before polling for IO

    :type loop: uv.Loop
    :type on_prepare: ((uv.Prepare) -> None) | ((Any, uv.Prepare) -> None)
    """

    __slots__ = ['uv_prepare', 'on_prepare']

    def __init__(self, loop=None, on_prepare=None):
        self.uv_prepare = ffi.new('uv_prepare_t*')
        super(Prepare, self).__init__(self.uv_prepare, loop)
        self.on_prepare = on_prepare or common.dummy_callback
        """
        Callback which called before polling for IO.

        .. function:: on_prepare(Prepare)

        :readonly: False
        :type: ((uv.Prepare) -> None) | ((Any, uv.Prepare) -> None)
        """
        code = lib.uv_prepare_init(self.loop.uv_loop, self.uv_prepare)
        if code < 0:
            self.set_closed()
            raise error.UVError(code)

    def start(self, on_prepare=None):
        """
        Starts the handle.

        :raises uv.UVError: error while starting the handle
        :raises uv.HandleClosedError: handle has already been closed or is closing

        :param on_prepare: callback called before polling for IO
        :type on_prepare: ((uv.Prepare) -> None) | ((Any, uv.Prepare) -> None)
        """
        if self.closing: raise error.ClosedHandleError()
        self.on_prepare = on_prepare or self.on_prepare
        code = lib.uv_prepare_start(self.uv_prepare, uv_prepare_cb)
        if code < 0: raise error.UVError(code)
        self.set_pending()

    def stop(self):
        """
        Stops the handle, the callback will no longer be called.

        :raises uv.UVError: error while stopping the handle
        """
        if self.closing: return
        code = lib.uv_prepare_stop(self.uv_prepare)
        if code < 0: raise error.UVError(code)
        self.clear_pending()

    __call__ = start
