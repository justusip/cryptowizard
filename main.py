import asyncio

import aiohttp

from comm.client import Client
from interface.server import Server
from misc.console import log, error
from misc.state import State

TAG_WS = "WS"


def on_shutdown(signum, frame):
    State.exit()


async def main():
    # signal.signal(signal.SIGINT, on_shutdown)

    server = Server()
    await server.start()

    # Real Account - Use with precaution!
    client = Client("yyJA1NNpb0GKYvt8ZQXU8ndeYBftNi1wHUjbvXrd4jyergodkbIiVnG74yyu9oYU",
                    "9VLpQLMg0GCSnn0PQ8pNaDo8xVKNYN4Vzu4cEFa3ENqifHTpzImUBqpNe8Ebry6E")
    # Testnet Account
    # client = Client("U0mgeLBjMFvL2OwFoKAvYCvdZjYD7LtFIuAlNc0dgrk4EE0r2v5rI25m7TZwCtvJ",
    #                 "tkq6hF0C6OAsUl3EFgdpXxeqLEVFgoFQeQrWtklaM4F6n8KmYD3V96ULPGcqMX97")
    while True:
        try:
            log(TAG_WS, "Connecting to Binance's WebSocket market streams...")
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect("wss://stream.binance.com:9443/ws/!bookTicker") as ws:
                    log(TAG_WS, "Connected to Binance's WebSocket market streams.")
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            print(msg)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            error(TAG_WS, f"WebSocket connection was closed unexpectedly {ws.exception()}")
            log(TAG_WS, "Disconnected from Binance's WebSocket market streams. Reconnecting...")
        except aiohttp.ClientError as ex:
            print("owo")
            error(TAG_WS, "Failed to connect to Binance's WebSocket market streams. "
                          f"Retrying in a second... ({ex})")
            await asyncio.sleep(1)

    # market = Market()
    # market.on_init(client)
    # market.on_updated_trigger = asyncio.Event()
    #
    # async def start():
    #     while State.ok():
    #         await market.on_updated_trigger.wait()
    #         market.on_updated_trigger.clear()
    #         # await asyncio.sleep(.5)
    #         # await server.io.emit("opportunities", redfox.opportunities)
    #
    # await asyncio.gather(*[
    #     asyncio.create_task(streamer.run()),
    #     asyncio.create_task(market.run(streamer)),
    #     asyncio.create_task(start()),
    #     # asyncio.create_task(redfox.on_trade())
    # ])
    #
    # await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
