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

import collections
import errno
import socket
import ssl

from . import abstract, common, error
from .handles import poll


class CertRequirements(common.Enumeration):
    """
    Certificate requirements configuration enumeration.
    """

    NONE = ssl.CERT_NONE
    """
    Certificate is ignored.

    :type: uv.secure.CertRequirements
    """

    OPTIONAL = ssl.CERT_OPTIONAL
    """
    Certificate is optional but validated if provided.

    :type: uv.secure.CertRequirements
    """

    REQUIRED = ssl.CERT_REQUIRED
    """
    Certificate is required and validated.

    :type: uv.secure.CertRequirements
    """


class Protocols(common.Enumeration):
    """
    Secure protocols configuration enumeration.
    """

    SSLv2 = getattr(ssl, 'PROTOCOL_SSLv2', 0)
    """
    Secure Sockets Layer Protocol Version 2

    :type: uv.secure.Protocols
    """

    SSLv3 = getattr(ssl, 'PROTOCOL_SSLv3', 1)
    """
    Secure Sockets Layer Protocol Version 3

    :type: uv.secure.Protocols
    """

    SSLv23 = getattr(ssl, 'PROTOCOL_SSLv23', 2)
    """
    Secure Sockets Layer Protocol Version 2 or 3

    :type: uv.secure.Protocols
    """

    TLSv1 = getattr(ssl, 'PROTOCOL_TLSv1', 3)
    """
    Transport Layer Security Protocol Version 1

    :type: uv.secure.Protocols
    """


class SecureConnectRequest(object):
    """
    Request to connect to a secure stream.
    """

    def __init__(self, secure, address, on_connect):
        """
        :param secure:
            secure stream to establish a connection on
        :param address:
            address to connect to
        :param on_connect:
            callback which should run after a connection has been
            established
        """
        self.stream = secure
        self.address = address
        self.on_connect = on_connect or common.dummy_callback

        self.stream.do_connect(self)

    def cancel(self):
        raise error.ArgumentError(message='unable to cancel secure connect request')


class SecureWriteRequest(object):
    """
    Request to write data to a secure stream.
    """

    def __init__(self, secure, buffers, on_write=None):
        """
        :param secure:
            secure stream handle
        :type secure:
            uv.secure.Secure
        """
        self.secure = secure
        self.buffer = buffers if isinstance(buffers, bytes) else b''.join(buffers)
        self.on_write = on_write or common.dummy_callback
        self.length = len(self.buffer)
        self.position = 0
        self.secure.do_write(self)

    def cancel(self):
        raise error.ArgumentError(message='unable to cancel ssl write request')


class SecureHandshakeRequest(object):
    """
    Request to issue the handshake on a secure stream.
    """

    __slots__ = ['secure', 'on_handshake']

    def __init__(self, secure, on_handshake=None):
        self.secure = secure
        self.on_handshake = on_handshake or common.dummy_callback
        """
        :type:
            ((uv.secure.SecureHandshakeRequest, uv.StatusCodes,
              ssl.SSLError) -> None) |
            ((Any, uv.secure.SecureHandshakeRequest, uv.StatusCodes,
              ssl.SSLError) -> None)
        """
        self.secure.do_handshake(self)

    def cancel(self):
        raise error.ArgumentError(message='unable to cancel ssl handshake')


class Secure:
    def __init__(self, keyfile=None, certfile=None, family=socket.AF_INET,
                 cert_requirement=CertRequirements.NONE, server_side=False,
                 ssl_version=Protocols.SSLv23, ca_certs=None, ciphers=None,
                 server_hostname=None, context=None, connection=None):
        """
        :param keyfile:
        :param certfile:
        :param server_side:
        :param cert_requirement:
        :param ssl_version:
        :param ca_certs:
        :param ciphers:
        :param server_hostname:
        :param context:

        :type stream:
            uv.TCP | uv.Pipe
        :return:
        """

        self.keyfile = keyfile
        self.certfile = certfile
        self.family = family
        self.cert_requirement = cert_requirement
        self.ssl_version = ssl_version
        self.ca_certs = ca_certs
        self.ciphers = ciphers
        self.server_hostname = server_hostname
        self.context = context
        self.server_side = server_side

        self._socket = connection or socket.socket(family=family, type=socket.SOCK_STREAM)
        self._socket.setblocking(False)
        self._ssl = None

        self.connected = False
        self.wrapped = False


        """
        self.ssl = ssl.SSLSocket(sock, keyfile=keyfile, certfile=certfile,
                                 ca_certs=ca_certs,
                                 cert_reqs=cert_requirement, ssl_version=ssl_version,
                                 server_side=server_side, ciphers=ciphers,
                                 do_handshake_on_connect=False,  _context=context,
                                 server_hostname=server_hostname)
        """

        self.poll = poll.Poll(self._socket.fileno())


        self.on_read = common.dummy_callback
        self.on_connection = common.dummy_callback

        self.writable = True
        self.readable = True
        self.ipc = False

        self._connect_request = None
        self._handshake_request = None
        self._pending_connections = collections.deque()
        """
        :type: SecureHandshakeRequest | None
        """
        self._pending_writes = collections.deque()
        self._reading = False
        self._writing = False



    def _update_poll(self):
        events = 0
        if self._reading:
            events |= poll.PollEvent.READABLE
        if self._writing:
            events |= poll.PollEvent.WRITABLE
        if events:
            self.poll.start(events, on_event=self._on_event)
        else:
            self.poll.stop()

    def _on_event(self, poll_handle, status, events):
        if status == error.StatusCodes.SUCCESS:
            if events & poll.PollEvent.READABLE:
                self._on_read()
            elif events & poll.PollEvent.WRITABLE:
                self._on_write()
        else:
            self._on_error()

    def _on_read(self):
        try:
            data = self._ssl.recv(2 ** 16)
            code = error.StatusCodes.SUCCESS if data else error.StatusCodes.EOF
        except ssl.SSLError as ssl_error:
            if ssl_error.args[0] == errno.EAGAIN:
                data = b''
                code = error.StatusCodes.SUCCESS
            else:
                data = ssl_error
                code = error.StatusCodes.get(ssl_error.args[0])
        self.on_read(self, code, data)

    def _on_write(self):
        try:
            while True:
                request = self._pending_writes[0]
                """ :type: SecureWriteRequest """
                count = self._ssl.send(request.buffer[request.position:])
                request.position += count
                if request.position >= request.length:
                    self._pending_writes.popleft()
                    request.on_write(request, error.StatusCodes.SUCCESS)
        except IndexError:
            self._writing = False
            self._update_poll()
        except OSError as os_error:
            if os_error.args[0] == errno.EAGAIN:
                pass

    def _on_error(self):
        pass

    def read_start(self, on_read=None):
        self.on_read = on_read or self.on_read
        self._reading = True
        self._update_poll()

    def read_stop(self):
        self._reading = False
        self._update_poll()

    def write(self, buffers, on_write=None):
        return SecureWriteRequest(self, buffers, on_write)



    def do_write(self, request):
        self._pending_writes.append(request)
        self._writing = True
        self._update_poll()

    def shutdown(self):
        self._reading = False
        self._writing = False
        self._update_poll()
        self.ssl.unwrap()

    def connect(self, address, on_connect=None):
        return SecureConnectRequest(self, address, on_connect)

    def bind(self, address):
        try:
            self._socket.bind(address)
        except OSError as os_error:
            status_code = error.StatusCodes.from_error_number(os_error.errno)
        else:
            status_code = 0
        if status_code != error.StatusCodes.SUCCESS:
            raise error.UVError(status_code)

    def listen(self, backlog=5, on_connection=None):
        if self._pending_connections is None:
            self._pending_connections = collections.deque()
        self.on_connection = on_connection or self.on_connection
        self._socket.listen(backlog)
        self.poll.start(poll.PollEvent.READABLE, self._do_listen)

    def _do_listen(self, poll_handle, status, events):
        try:
            while True:
                connection = self._socket.accept()
                self._pending_connections.append(connection)
                self.on_connection(self, error.StatusCodes.SUCCESS)
        except socket.error as socket_error:
            pass

    def accept(self, cls=None, server_side=True, *arguments, **keywords):
        keywords['server_side'] = server_side
        if self._pending_connections:
            connection, _ = self._pending_connections.popleft()
            keywords['connection'] = connection
            secure = Secure(*arguments, **keywords)
            secure._setup_ssl()
            return secure
        else:
            raise error.TemporaryUnavailableError()

    def _setup_ssl(self):
        self.connected = True
        self._ssl = ssl.SSLSocket(self._socket,
                                      keyfile=self.keyfile,
                                      certfile=self.certfile,
                                      server_side=self.server_side,
                                      cert_reqs=self.cert_requirement,
                                      ssl_version=self.ssl_version,
                                      ca_certs=self.ca_certs,
                                      do_handshake_on_connect=False,
                                      ciphers=self.ciphers,
                                      server_hostname=self.server_hostname,
                                      _context=self.context)

    def do_connect(self, request):
        """
        :type request:
            SecureConnectRequest
        """
        try:
            error_number = self._socket.connect(request.address)
        except socket.error as socket_error:
            if socket_error.args[0] == errno.EINPROGRESS:
                error_number = 0
            else:
                error_number = socket_error.args[0]
        if error_number == 0:
            self._connect_request = request
            self.poll.start(poll.PollEvent.WRITABLE, self._do_connect)
        else:
            status_code = error.StatusCodes.from_error_number(error_number)
            raise error.UVError(status_code)

    def _do_connect(self, poll_handle, status, events):
        self.poll.stop()
        error_number = self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        status_code = error.StatusCodes.from_error_number(error_number)
        if status_code == error.StatusCodes.SUCCESS:
            self._setup_ssl()
        self._connect_request.on_connect(self._connect_request, status_code)

    def handshake(self, on_handshake=None):
        return SecureHandshakeRequest(self, on_handshake)

    def do_handshake(self, request):
        self._handshake_request = request
        events = poll.PollEvent.READABLE | poll.PollEvent.WRITABLE
        self.poll.start(events, self._do_handshake)

    def _do_handshake(self, poll_handle, status, events):
        if status != error.StatusCodes.SUCCESS:
            code = error.StatusCodes.get(status)
            self._handshake_request.on_handshake(self._handshake_request, code, None)
        else:
            try:
                self._ssl.do_handshake()
            except ssl.SSLError as ssl_error:
                if ssl_error.args[0] == ssl.SSL_ERROR_WANT_READ:
                    self.poll.start(poll.PollEvent.READABLE, self._do_handshake)
                elif ssl_error.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                    self.poll.start(poll.PollEvent.WRITABLE, self._do_handshake)
                else:
                    self.poll.stop()
                    code = error.StatusCodes.get(-ssl_error.args[0])
                    request = self._handshake_request
                    request.on_handshake(request, code, ssl_error)
            else:
                request = self._handshake_request
                request.on_handshake(request, error.StatusCodes.SUCCESS, None)
                self._update_poll()


    """
    def handshake(self, callback=None):
        self.poll.start(PollEvent.READABLE | PollEvent.WRITABLE, self._do_handshake)
        self.on_handshake = callback or self.on_handshake

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

    def read_start(self, callback=None):
        self.on_read = callback or self.on_read
        self.readable = True
        self._update_events()

    def read_stop(self):
        self.readable = False
        self._update_events()
    """

    def close(self):
        self.poll.close()


abstract.Request.register(SecureWriteRequest)
abstract.Request.register(SecureHandshakeRequest)
abstract.Stream.register(Secure)
