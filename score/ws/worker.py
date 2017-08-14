import asyncio
import websockets
import score.serve
import concurrent


class AsyncioWorker(score.serve.AsyncioWorker):

    def __init__(self, conf, handler):
        if not asyncio.iscoroutinefunction(handler):
            raise ValueError('Handler must be a coroutine function')
        self.conf = conf
        self.handler = handler

    @asyncio.coroutine
    def create_connection(self, protocol, uri):
        with self.conf.ctx.Context() as ctx:
            ctx.websocket = protocol
            coroutine = self.handler(ctx)
            future = self.loop.create_task(coroutine)
            self.connections.append(future)
            try:
                yield from future
            except websockets.ConnectionClosed:
                pass
            except concurrent.futures.CancelledError:
                pass
            except Exception as e:
                self.conf.log.exception(e)
            finally:
                self.connections.remove(future)

    def _prepare(self):
        self.connections = []

    @asyncio.coroutine
    def _start(self):
        extra_kwargs = {}
        if self.conf.reuse_port:
            extra_kwargs['reuse_port'] = True
        self.server = yield from websockets.serve(
            self.create_connection,
            self.conf.host, self.conf.port, loop=self.loop, **extra_kwargs)

    @asyncio.coroutine
    def _pause(self):
        if self.connections and self.conf.stop_timeout != 0:
            self.server.server.close()
            if self.conf.stop_timeout is None:
                yield from asyncio.wait(self.connections, loop=self.loop)
            else:
                all_closed = asyncio.wait(self.connections, loop=self.loop)
                try:
                    yield from asyncio.wait_for(
                        asyncio.shield(all_closed, loop=self.loop),
                        self.conf.stop_timeout, loop=self.loop)
                except asyncio.TimeoutError:
                    pass
        self.server.close()
        yield from self.server.wait_closed()

    def _cleanup(self, exception):
        pass


class TwistedAutobahnWorker(score.serve.Worker):

    def __init__(self, conf, server_protocol):
        self.conf = conf
        self.server_protocol = server_protocol

    def prepare(self):
        """
        Implements the transition from STOPPED to PAUSED.
        """
        from autobahn.twisted.websocket import WebSocketServerFactory
        from twisted.internet import reactor
        self.server_factory = WebSocketServerFactory()
        self.server_factory.protocol = self.server_protocol
        self.listener = reactor.listenTCP(self.conf.port, self.server_factory,
                                          interface=self.conf.host)

    def start(self):
        """
        Implements the transition from PAUSED to RUNNING.
        """
        from twisted.internet import reactor
        from threading import Thread, Barrier
        self.reactor_barrier = Barrier(2)

        def start():
            # concerning the installSignalHandlers argument:
            # "exceptions.ValueError: signal only works in main thread"
            # http://twistedmatrix.com/trac/wiki/FrequentlyAskedQuestions
            reactor.run(installSignalHandlers=0)
            self.reactor_barrier.wait()
        Thread(target=start).start()

    def stop(self):
        """
        Implements the transition from PAUSED to STOPPED.
        """

    def pause(self):
        """
        Implements the transition from RUNNING to PAUSED.
        """
        from twisted.internet import reactor
        reactor.callFromThread(reactor.stop)
        self.reactor_barrier.wait()
        self.listener.stopListening()

    def cleanup(self, exception):
        """
        Called when an exception occured. Due to the nature of threading, it is
        not entirely clear, in which state the worker was, when this specific
        exception occurred.
        """
        if exception:
            from twisted.internet import reactor
            reactor.callFromThread(reactor.stop)


class AsyncioAutobahnWorker(score.serve.AsyncioWorker):

    def __init__(self, conf, server_protocol):
        self.conf = conf
        self.server_protocol = server_protocol

    def _prepare(self):
        self.connections = []

    def connection_received(self):
        connection = self.server_factory()
        original_onConnect = connection.onConnect
        original_onClose = connection.onClose
        event = asyncio.Event(loop=self.loop)
        wait_coroutine = None

        def onConnect(*args, **kwargs):
            nonlocal wait_coroutine
            wait_coroutine = event.wait()
            self.connections.append(wait_coroutine)
            return original_onConnect(*args, **kwargs)

        def onClose(*args, **kwargs):
            event.set()
            if wait_coroutine is not None:
                self.connections.remove(wait_coroutine)
            return original_onClose(*args, **kwargs)

        connection.onConnect = onConnect
        connection.onClose = onClose
        return connection

    @asyncio.coroutine
    def _start(self):
        from autobahn.asyncio.websocket import WebSocketServerFactory
        import txaio
        txaio.config.loop = self.loop
        self.server_factory = WebSocketServerFactory(loop=self.loop)
        self.server_factory.protocol = self.server_protocol
        self.server = yield from self.loop.create_server(
            self.connection_received, self.conf.host, self.conf.port)

    @asyncio.coroutine
    def _pause(self):
        if self.connections and self.conf.stop_timeout != 0:
            self.server.close()
            if self.conf.stop_timeout is None:
                yield from asyncio.wait(self.connections, loop=self.loop)
            else:
                all_closed = asyncio.wait(self.connections, loop=self.loop)
                try:
                    yield from asyncio.wait_for(
                        asyncio.shield(all_closed, loop=self.loop),
                        self.conf.stop_timeout, loop=self.loop)
                except asyncio.TimeoutError:
                    pass

    def _cleanup(self, exception):
        pass
