.. module:: score.websockets
.. role:: confkey
.. role:: confdefault

****************
score.websockets
****************

A module providing a :class:`score.serve.Worker`, which launches a websocket
server using the websockets_ library.

.. _websockets: https://pypi.python.org/pypi/websockets


Quickstart
==========

The module defaults are suitable for development, so you just need to write
your :class:`Worker <score.serve.Worker>` class and load it into
:mod:`score.serve`:

.. code-block:: ini

    [score]
    modules =
        score.asyncio
        score.ctx
        score.websockets
        myapplication

    [serve]
    modules = myapplication


.. code-block:: python

    import asyncio
    from score.init import ConfiguredModule
    from score.websockets import Worker

    class Myapplication(ConfiguredModule):

        def __init__(self, websockets, asyncio):
            super().__init__('myapplication')
            self.websockets = websockets
            self.asyncio = asyncio

        def score_serve_workers(self):
            return Worker(self.websockets,
                          self.asyncio,
                          self.echo_service)

        @asyncio.coroutine
        def echo_service(self, ctx):
            for message in (yield from ctx.websocket):
                yield from ctx.websocket.send(message)

After starting your application, you can access your echo server as
"ws://localhost:8081".


API
===

.. autofunction:: init

.. autoclass:: ConfiguredWebsocketsModule()
