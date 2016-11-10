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

from score.init import (
    ConfiguredModule, ConfigurationError, parse_dotted_path,
    parse_time_interval)
from .worker import WebsocketWorker


defaults = {
    'serve.ip': '0.0.0.0',
    'serve.port': 8080,
    'stop_timeout': None,
}


def init(confdict, db=None):
    """
    Initializes this module acoording to :ref:`our module initialization
    guidelines <module_initialization>` with the following configuration keys:
    """
    conf = dict(defaults.items())
    conf.update(confdict)
    if 'handler' not in conf:
        import score.ws
        raise ConfigurationError(score.ws, 'No handler specified')
    handler = parse_dotted_path(conf['handler'])
    host = conf['serve.ip']
    port = int(conf['serve.port'])
    stop_timeout = conf['stop_timeout']
    if stop_timeout is not None:
        stop_timeout = parse_time_interval(stop_timeout)
    return ConfiguredWsModule(host, port, handler, stop_timeout)


class ConfiguredWsModule(ConfiguredModule):
    """
    This module's :class:`configuration class <score.init.ConfiguredModule>`.
    """

    def __init__(self, host, port, handler, stop_timeout):
        import score.ws
        super().__init__(score.ws)
        self.host = host
        self.port = port
        self.handler = handler
        self.stop_timeout = stop_timeout

    def score_serve_workers(self):
        if not hasattr(self, '_score_serve_workers'):

            class ConfiguredWebsocketWorker(WebsocketWorker):
                conf = self

            self._score_serve_workers = [ConfiguredWebsocketWorker()]

        return self._score_serve_workers
