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


@base.handle_callback('uv_check_cb')
def uv_check_cb(check_handle):
    """
    :type check_handle:
        uv.Check
    """
    check_handle.on_check(check_handle)


@handle.HandleTypes.CHECK
class Check(handle.UVHandle):
    """
    Check handles will run the given callback once per loop iteration,
    right after polling for IO after they have been started.

    :raises uv.UVError:
        error while initializing the handle

    :param loop:
        event loop the handle should run on
    :param on_check:
        callback which should run right after polling for IO after the
        handle has been started

    :type loop:
        uv.Loop
    :type on_check:
        ((uv.Check) -> None) | ((Any, uv.Check) -> None)
    """

    __slots__ = ['uv_check', 'on_check']

    uv_handle_type = 'uv_check_t*'
    uv_handle_init = lib.uv_check_init

    def __init__(self, loop=None, on_check=None):
        super(Check, self).__init__(loop)
        self.uv_check = self.base_handle.uv_object
        self.on_check = on_check or common.dummy_callback
        """
        Callback which should run right after polling for IO after the
        handle has been started.


        .. function:: on_check(check_handle)

            :param check_handle:
                handle the call originates from

            :type check_handle:
                uv.Check


        :readonly:
            False
        :type:
            ((uv.Check) -> None) | ((Any, uv.Check) -> None)
        """

    def start(self, on_check=None):
        """
        Start the handle. The callback will be called once per loop
        iteration right after polling for IO from now on.

        :raises uv.UVError:
            error while starting the handle
        :raises uv.ClosedHandleError:
            handle has already been closed or is closing

        :param on_check:
            callback which should run right after polling for IO
            (overrides the current callback if specified)

        :type on_check:
            ((uv.Check) -> None) | ((Any, uv.Check) -> None)
        """
        if self.closing:
            raise error.ClosedHandleError()
        self.on_check = on_check or self.on_check
        code = lib.uv_check_start(self.uv_check, uv_check_cb)
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
        code = lib.uv_check_stop(self.uv_check)
        if code != error.StatusCodes.SUCCESS:
            raise error.UVError(code)
        self.clear_pending()

    __call__ = start
