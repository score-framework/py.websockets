import asyncio
from score.serve import Service
from score.websockets import Worker
from score.init import init
import websockets


def test_start():
    @asyncio.coroutine
    def handler(ctx):
        try:
            while True:
                message = yield from ctx.websocket.recv()
                yield from ctx.websocket.send(message)
        except websockets.exceptions.ConnectionClosed:
            pass
    app = init({
        'score.init': {
            'modules': ['score.ctx', 'score.asyncio', 'score.websockets'],
        },
    })
    service = Service('test', Worker(app.websockets, app.asyncio, handler))
    try:
        service.start()
        ws = app.asyncio.await(
            websockets.connect('ws://localhost:8081', loop=app.asyncio.loop))
        app.asyncio.await(ws.send('test'))
        response = app.asyncio.await(ws.recv())
        assert response == 'test'
    finally:
        service.stop()
