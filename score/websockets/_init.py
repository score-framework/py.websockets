# Copyright © 2015-2018 STRG.AT GmbH, Vienna, Austria
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


defaults = {
    'host': '0.0.0.0',
    'port': 8081,
    'stop_timeout': None,
    'reuse_port': False,
}


def init(confdict, ctx):
    """
    Initializes this module acoording to :ref:`our module initialization
    guidelines <module_initialization>` with the following configuration keys:

    :confkey:`host` :confdefault:`0.0.0.0`
        The hostname to listen for connnections on.

    :confkey:`port` :confdefault:`8081`
        The port to listen for connnections on.

    :confkey:`stop_timeout` :confdefault:`None`
        Defines how long the module will wait for connections to close
        when pausing the worker. The value will be interpreted through
        a call to :func:`score.init.parse_time_interval`.

        The default value `None` indicates that the module will wait
        indefinitely. If you want to the server to terminate immediately,
        without waiting for open connections at all, you must pass "0".

    :confkey:`reuse_port` :confdefault:`False`
        Whether the ``reuse_port`` keyword argument should be passed to the
        underlying event loop's :meth:`create_server()
        <asyncio.AbstractEventLoop.create_server>` method.

    """
    conf = dict(defaults.items())
    conf.update(confdict)
    host = conf['host']
    port = int(conf['port'])
    stop_timeout = conf['stop_timeout']
    if stop_timeout == 'None':
        stop_timeout = None
    if stop_timeout is not None:
        stop_timeout = parse_time_interval(stop_timeout)
    reuse_port = parse_bool(conf['reuse_port'])
    return ConfiguredWebsocketsModule(ctx, host, port, stop_timeout, reuse_port)


class ConfiguredWebsocketsModule(ConfiguredModule):
    """
    This module's :class:`configuration class <score.init.ConfiguredModule>`.
    """

    def __init__(self, ctx, host, port, stop_timeout, reuse_port):
        import score.websockets
        super().__init__(score.websockets)
        self.ctx = ctx
        self.host = host
        self.port = port
        self.stop_timeout = stop_timeout
        self.reuse_port = reuse_port
