import asyncio
from typing import Optional

import aiohttp
from aiohttp import ClientWebSocketResponse

from misc.console import *
from misc.state import State

TAG = "ws"


class Feed:
    def __init__(self, streamer, streams: [str]):
        self.streamer = streamer
        self.streams = streams
        self.on_receieved_event = asyncio.Event()
        self.pending_data = None

    async def __aenter__(self):
        while self.streamer.ws is None:
            await asyncio.sleep(.1)
        streams_to_subscribe = [o for o in self.streams if o not in self.streamer.subscribedStreams]
        await self.streamer.ws.send_json({
            "method": "SUBSCRIBE",
            "params": streams_to_subscribe,
            "id": 1
        })
        print(streams_to_subscribe)
        return self

    async def __aexit__(self, type, value, traceback):
        streams_in_use = []
        for f in self.streamer.feeds:
            if f is self:
                continue
            streams_in_use.extend(f.streams)
        streams_to_unsubscribe = [o for o in self.streams if o not in streams_in_use]
        await self.streamer.ws.send_json({
            "method": "UNSUBSCRIBE",
            "params": streams_to_unsubscribe,
            "id": 1
        })
        print(streams_to_unsubscribe)

    def __aiter__(self):
        return self

    async def __anext__(self):
        await self.on_receieved_event.wait()
        self.on_receieved_event.clear()
        return self.pending_data


class Streamer:
    def __init__(self):
        self.on_update = None
        self.ws: Optional[ClientWebSocketResponse] = None
        self.tracking_id = 0
        self.feeds = []
        self.subscribedStreams = []

    async def run(self):
        while State.ok():
            try:
                log(TAG, "Connecting to Binance's WebSocket market streams...")
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect('wss://stream.binance.com:9443/stream') as self.ws:
                        log(TAG, "Connected to Binance's WebSocket market streams.")
                        async for msg in self.ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = msg.json()
                                if "stream" in data:
                                    for f in self.feeds:
                                        if data["stream"] in f.streams:
                                            f.pending_data = data["data"]
                                            f.on_receieved_event.set()
                                else:
                                    print(data)

                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                error(TAG, f"WebSocket connection was closed unexpectedly {self.ws.exception()}")
                                break
                log(TAG, "Disconnected from Binance's WebSocket market streams. Reconnecting...")
            except aiohttp.ClientError as ex:
                error(TAG, "Failed to connect to Binance's WebSocket market streams. "
                           f"Retrying in a second... ({ex})")
                await asyncio.sleep(1)

    def subscribe(self, tickers: [str]) -> Feed:
        f = Feed(self, tickers)
        self.feeds.append(f)
        return f
