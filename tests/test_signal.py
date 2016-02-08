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

import os
import signal
import threading

import common

import uv


@common.skip_platform('win32')
class TestSignal(common.TestCase):
    def test_signal(self):
        self.signum = None

        def on_signal(signal_handle, signum):
            self.signum = signum
            signal_handle.stop()

        self.signal = uv.Signal(on_signal=on_signal)
        self.signal.start(signal.SIGUSR1)

        self.assert_equal(self.signal.signum, signal.SIGUSR1)

        thread = threading.Thread(target=self.loop.run)
        thread.start()

        os.kill(os.getpid(), signal.SIGUSR1)

        thread.join()

        self.assert_equal(self.signum, signal.SIGUSR1)

    def test_closed(self):
        self.signal = uv.Signal()
        self.signal.close()

        try:
            signum = self.signal.signum
        except uv.ClosedHandleError:
            pass
        else:
            self.assert_true(False)
        self.assert_raises(uv.ClosedHandleError, self.signal.start, 2)
        self.assert_is(self.signal.stop(), None)