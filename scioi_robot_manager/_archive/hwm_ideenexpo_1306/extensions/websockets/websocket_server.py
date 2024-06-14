import asyncio
import websockets
import json
import threading


class WebsocketClass:
    def __init__(self, host, port, start=False):
        self.host = host
        self.port = port
        self.server = None
        self.clients = set()
        self.running = False
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_loop)
        self.message_callback = None
        self.connection_callback = None

        if start:
            self.run()

    def _start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _handler(self, websocket, path):
        self.clients.add(websocket)
        if self.connection_callback:
            self.loop.call_soon_threadsafe(self.connection_callback, websocket)
        try:
            async for message in websocket:
                if self.message_callback:
                    self.loop.call_soon_threadsafe(self.message_callback, message)
        finally:
            self.clients.remove(websocket)

    async def _run_server(self):
        self.server = await websockets.serve(self._handler, self.host, self.port)
        self.running = True
        await self.server.wait_closed()

    def run(self):
        if not self.running:
            self.thread.start()
            self.loop.call_soon_threadsafe(asyncio.create_task, self._run_server())

    async def _send(self, message):
        if self.clients:
            await asyncio.wait([client.send(message) for client in self.clients])

    def send(self, message):
        if isinstance(message, dict):
            message = json.dumps(message)
        asyncio.run_coroutine_threadsafe(self._send(message), self.loop)

    def stop(self):
        if self.running:
            for task in asyncio.all_tasks(loop=self.loop):
                task.cancel()
            self.loop.stop()
            self.server.close()
            self.running = False

    def set_message_callback(self, callback):
        self.message_callback = callback

    def set_connection_callback(self, callback):
        self.connection_callback = callback
