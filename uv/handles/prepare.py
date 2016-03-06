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

from .. import base, common, error, handle
from ..library import lib


@base.handle_callback('uv_prepare_cb')
def uv_prepare_cb(prepare_handle):
    """
    :type prepare_handle:
        uv.Prepare
    """
    prepare_handle.on_prepare(prepare_handle)


@handle.HandleTypes.PREPARE
class Prepare(handle.UVHandle):
    """
    Prepare handles will run the given callback once per loop
    iteration, right before polling for IO.

    :raises uv.UVError:
        error while initializing the handle

    :param loop:
        event loop the handle should run on
    :param on_prepare:
        callback which should run right before polling for IO after the
        handle has been started

    :type loop:
        uv.Loop
    :type on_prepare:
        ((uv.Prepare) -> None) | ((Any, uv.Prepare) -> None)
    """

    __slots__ = ['uv_prepare', 'on_prepare']

    uv_handle_type = 'uv_prepare_t*'
    uv_handle_init = lib.uv_prepare_init

    def __init__(self, loop=None, on_prepare=None):
        super(Prepare, self).__init__(loop)
        self.uv_prepare = self.base_handle.uv_object
        self.on_prepare = on_prepare or common.dummy_callback
        """
        Callback which should run right before polling for IO after the
        handle has been started.


        .. function:: on_prepare(prepare_handle)

            :param prepare_handle:
                handle the call originates from

            :type prepare_handle:
                uv.Prepare


        :readonly:
            False
        :type:
            ((uv.Prepare) -> None) | ((Any, uv.Prepare) -> None)
        """

    def start(self, on_prepare=None):
        """
        Start the handle. The callback will run once per loop iteration
        right before polling for IO from now on.

        :raises uv.UVError:
            error while starting the handle
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param on_prepare:
            callback which should run right before polling for IO
            (overrides the current callback if specified)
        :type on_prepare:
            ((uv.Prepare) -> None) | ((Any, uv.Prepare) -> None)
        """
        if self.closing:
            raise error.ClosedHandleError()
        self.on_prepare = on_prepare or self.on_prepare
        code = lib.uv_prepare_start(self.uv_prepare, uv_prepare_cb)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.set_pending()

    def stop(self):
        """
        Stop the handle. The callback will no longer be called.

        :raises uv.UVError:
            error while stopping the handle
        """
        if self.closing:
            return
        code = lib.uv_prepare_stop(self.uv_prepare)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.clear_pending()

    __call__ = start
