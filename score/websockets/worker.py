import score.serve
import concurrent
import score.asyncio
import asyncio
import websockets


class WebsocketsWorker(score.asyncio.Worker):

    def __init__(self, websockets, asyncio, handler):
        if not asyncio.iscoroutinefunction(handler):
            raise ValueError('Handler must be a coroutine function')
        score.asyncio.Worker.__init__(self, asyncio)
        self.websockets = websockets
        self.handler = handler

    @asyncio.coroutine
    def create_connection(self, protocol, uri):
        with self.websockets.ctx.Context() as ctx:
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
                self.websockets.log.exception(e)
            finally:
                self.connections.remove(future)

    def _prepare(self):
        self.connections = []

    @asyncio.coroutine
    def _start(self):
        extra_kwargs = {}
        if self.websockets.reuse_port:
            extra_kwargs['reuse_port'] = True
        self.server = yield from websockets.serve(
            self.create_connection,
            self.websockets.host, self.websockets.port, loop=self.loop,
            **extra_kwargs)

    @asyncio.coroutine
    def _pause(self):
        if self.connections and self.websockets.stop_timeout != 0:
            self.server.server.close()
            if self.websockets.stop_timeout is None:
                yield from asyncio.wait(self.connections, loop=self.loop)
            else:
                all_closed = asyncio.wait(self.connections, loop=self.loop)
                try:
                    yield from asyncio.wait_for(
                        asyncio.shield(all_closed, loop=self.loop),
                        self.websockets.stop_timeout, loop=self.loop)
                except asyncio.TimeoutError:
                    pass
        self.server.close()
        yield from self.server.wait_closed()

    def _cleanup(self, exception):
        pass
