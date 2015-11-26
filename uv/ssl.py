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

import enum
import ssl
import socket

from collections import deque

from .library import dummy_callback

from .poll import Poll, PollEvent
from .stream import Stream


class CertReqs(enum.IntEnum):
    NONE = ssl.CERT_NONE
    OPTIONAL = ssl.CERT_OPTIONAL
    REQUIRED = ssl.CERT_REQUIRED


class Protocol(enum.IntEnum):
    SSLv2 = ssl.PROTOCOL_SSLv2
    SSLv3 = ssl.PROTOCOL_SSLv3
    SSLv23 = ssl.PROTOCOL_SSLv23
    TLSv1 = ssl.PROTOCOL_TLSv1


class SSL:
    def __init__(self, stream: Stream, keyfile=None, certfile=None, server_side=False,
                 cert_reqs=CertReqs.NONE, ssl_version=Protocol.SSLv23, ca_certs=None,
                 ciphers=None, server_hostname=None, context=None):
        self.stream = stream

        if stream.family is None:
            raise ValueError('invalid stream (family is None)')

        self.socket = socket.fromfd(self.stream.fileno(), stream.family,
                                    socket.SOCK_STREAM)
        self.poll = Poll(self.stream.fileno())

        self.ssl = ssl.SSLSocket(self.socket, keyfile, certfile, server_side,
                                 cert_reqs, ssl_version, ca_certs, ciphers=ciphers,
                                 do_handshake_on_connect=False, _context=context,
                                 server_hostname=server_hostname)

        self.on_handshake = dummy_callback
        self.on_read = dummy_callback

        self._pending_writes = deque()

        self.writable = False
        self.readable = False

    def handshake(self, callback: callable=None):
        self.poll.start(PollEvent.READABLE | PollEvent.WRITABLE, self._do_handshake)
        self.on_handshake = callback or self.on_handshake

    def _do_handshake(self, poll, status, events):
        try:
            self.ssl.do_handshake()
        except ssl.SSLError as error:
            if error.args[0] == ssl.SSL_ERROR_WANT_READ:
                self.poll.start(PollEvent.READABLE, self._do_handshake)
            elif error.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                self.poll.start(PollEvent.WRITABLE, self._do_handshake)
            else:
                self.poll.stop()
                self.on_handshake(self, -error.args[0], error)
        else:
            self.poll.stop()
            self.on_handshake(self, 0, None)

    def _on_read(self):
        print(self.ssl.recv(2 ** 16))

    def _on_write(self):
        pass

    def _on_error(self):
        pass

    def _on_event(self, poll, status, events):
        if status == 0:
            if events & PollEvent.READABLE:
                self._on_read()
            elif events & PollEvent.WRITABLE:
                self._on_write()
        else:
            self._on_error()

    def _update_events(self):
        self.events = 0
        if self.readable: self.events |= PollEvent.READABLE
        if self.writable: self.events |= PollEvent.WRITABLE
        if self.events == 0:
            self.poll.stop()
        else:
            self.poll.start(self.events, self._on_event)

    def getpeercert(self, binary_form=False):
        return self.ssl.getpeercert(binary_form)

    def cipher(self):
        return self.ssl.cipher()



    def read_start(self, callback: callable=None):
        self.on_read = callback or self.on_read
        self.readable = True
        self._update_events()

    def read_stop(self):
        self.readable = False
        self._update_events()
