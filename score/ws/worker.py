import asyncio
import websockets
import score.serve
import concurrent


class WebsocketWorker(score.serve.AsyncioWorker):

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
        self.server = yield from websockets.serve(
            self.create_connection,
            self.conf.host, self.conf.port, loop=self.loop,
            reuse_port=self.conf.reuse_port)

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
