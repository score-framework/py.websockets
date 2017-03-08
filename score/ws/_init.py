# Copyright © 2015-2017 STRG.AT GmbH, Vienna, Austria
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

from score.init import ConfiguredModule, parse_time_interval, parse_bool
from .worker import WebsocketWorker


defaults = {
    'serve.ip': '0.0.0.0',
    'serve.port': 8081,
    'stop_timeout': None,
    'reuse_port': False,
}


def init(confdict, ctx):
    """
    Initializes this module acoording to :ref:`our module initialization
    guidelines <module_initialization>` with the following configuration keys:
    """
    conf = dict(defaults.items())
    conf.update(confdict)
    host = conf['serve.ip']
    port = int(conf['serve.port'])
    stop_timeout = conf['stop_timeout']
    if stop_timeout is not None:
        stop_timeout = parse_time_interval(stop_timeout)
    reuse_port = parse_bool(conf['reuse_port'])
    return ConfiguredWsModule(ctx, host, port, stop_timeout, reuse_port)


class ConfiguredWsModule(ConfiguredModule):
    """
    This module's :class:`configuration class <score.init.ConfiguredModule>`.
    """

    def __init__(self, ctx, host, port, stop_timeout, reuse_port):
        import score.ws
        super().__init__(score.ws)
        self.ctx = ctx
        self.host = host
        self.port = port
        self.stop_timeout = stop_timeout
        self.reuse_port = reuse_port

    def create_worker(self, handler):
        return WebsocketWorker(self, handler)
