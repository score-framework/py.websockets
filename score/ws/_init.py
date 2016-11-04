# Copyright © 2015,2016 STRG.AT GmbH, Vienna, Austria
#
# This file is part of the The SCORE Framework.
#
# The SCORE Framework and all its parts are free software: you can redistribute
# them and/or modify them under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation which is in the
# file named COPYING.LESSER.txt.
#
# The SCORE Framework and all its parts are distributed without any WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. For more details see the GNU Lesser General Public
# License.
#
# If you have not received a copy of the GNU Lesser General Public License see
# http://www.gnu.org/licenses/.
#
# The License-Agreement realised between you as Licensee and STRG.AT GmbH as
# Licenser including the issue of its valid conclusion and its pre- and
# post-contractual effects is governed by the laws of Austria. Any disputes
# concerning this License-Agreement including the issue of its valid conclusion
# and its pre- and post-contractual effects are exclusively decided by the
# competent court, in whose district STRG.AT GmbH has its registered seat, at
# the discretion of STRG.AT GmbH also the competent court, in whose district the
# Licensee has his registered seat, an establishment or assets.

import asyncio
from score.init import ConfiguredModule, ConfigurationError, parse_dotted_path
from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory


defaults = {
    'serve.ip': '0.0.0.0',
    'serve.port': 8080,
}


def init(confdict, db=None):
    """
    Initializes this module acoording to :ref:`our module initialization
    guidelines <module_initialization>` with the following configuration keys:
    """
    conf = dict(defaults.items())
    conf.update(confdict)
    if 'protocol' not in conf:
        import score.ws
        raise ConfigurationError(score.ws, 'No protocol specified')
    protocol = parse_dotted_path(conf['protocol'])
    assert issubclass(protocol, WebSocketServerProtocol)
    host = conf['serve.ip']
    port = int(conf['serve.port'])
    return ConfiguredWsModule(host, port, protocol)


class ConfiguredWsModule(ConfiguredModule):
    """
    This module's :class:`configuration class <score.init.ConfiguredModule>`.
    """

    def __init__(self, host, port, protocol):
        self.host = host
        self.port = port
        self.protocol = protocol

    def score_serve_workers(self):
        if not hasattr(self, '_score_serve_workers'):
            import score.serve
            conf = self

            class Worker(score.serve.AsyncioWorker):

                def __init__(self):
                    self.server = None

                def create_connection(self, *args, **kwargs):
                    connection = conf.protocol(*args, **kwargs)
                    connection.is_closed.add_done_callback(
                        self.connection_closed)
                    self.connections.append(connection)
                    return connection

                def connection_closed(self, future):
                    self.connections.remove(future.result())

                def _prepare(self):
                    self.connections = []

                @asyncio.coroutine
                def _start(self):
                    url = "ws://%s:%d" % (conf.host, conf.port)
                    self.factory = WebSocketServerFactory(url, loop=self.loop)
                    self.factory.protocol = self.create_connection
                    self.server = yield from self.loop.create_server(
                        self.factory, conf.host, conf.port)

                @asyncio.coroutine
                def _pause(self):
                    self.server.close()
                    for connection in self.connections:
                        connection.sendClose(4001, 'pause')  # TODO: MAGIC INT!
                    while self.connections:
                        yield from self.connections[0]

                def _cleanup(self, exception):
                    pass

            self._score_serve_workers = [Worker()]

        return self._score_serve_workers
