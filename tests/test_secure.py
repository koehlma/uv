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

import common

import uv


KEYFILE = common.resolve_path('server.key')
CERTFILE = common.resolve_path('server.crt')


@common.skip_interpreter('pypy')
class TestSecure(common.TestCase):
    def test_secure(self):
        def on_client_handshake(handshake_request, status, ssl_error):
            import sys
            print('client handshake:', status, file=sys.stderr)
            self.client.close()

        def on_connect(connect_request, status):
            self.client.handshake(on_handshake=on_client_handshake)
            import sys
            print('client connection:', status, file=sys.stderr)

        def on_server_handshake(handshake_request, status, ssl_error):
            import sys
            print('handshake server:', status, file=sys.stderr)
            self.server.close()

        def on_connection(secure_server, status):
            connection = secure_server.accept(keyfile=KEYFILE, certfile=CERTFILE)
            connection.handshake(on_handshake=on_server_handshake)
            import sys
            print('sever connection:', status, file=sys.stderr)

        self.server = uv.secure.Secure()
        self.server.bind((common.TEST_IPV4, common.TEST_PORT2))
        self.server.listen(5, on_connection=on_connection)

        self.client = uv.secure.Secure()
        self.client.connect((common.TEST_IPV4, common.TEST_PORT2), on_connect=on_connect)

        try:
            self.loop.run()
        finally:
            self.server._socket.close()
            self.client._socket.close()
