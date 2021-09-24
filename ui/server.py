from aiohttp import web
import socketio

from misc.console import *

TAG = " UI "


class Server:
    def __init__(self):
        self.app = web.Application()
        self.runner = web.AppRunner(self.app)
        self.io = socketio.AsyncServer()
        self.io.attach(self.app)

        @self.io.event
        def connect(sid, environ):
            log(TAG, f"Client {environ['REMOTE_ADDR']} with SID {sid} is connected.")

        @self.io.event
        def disconnect(sid):
            log(TAG, f"Client {sid} is disconnected.")

        @self.io.event
        def owo(sid, data):
            print(data)
            pass

    async def start(self):
        address = "localhost"
        port = 2255
        await self.runner.setup()
        await web.TCPSite(self.runner, address, port).start()
        log(TAG, f"Started interfacing server on {address}:{port}")

    async def stop(self):
        await self.runner.cleanup()
        log(TAG, f"Stopped interfacing server.")
