import asyncio
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from markets.binance.binance_market import BinanceMarket
from markets.markets import Markets
from misc.console import log
from programs.ma import MovingAverage
from programs.program import Program
from ui.server import Server

TAG = "Core"

dotenv_path = Path(".").resolve() / '.env'
load_dotenv(dotenv_path)


class Core:
    def __init__(self):
        self.server = None
        self.markets: Markets = Markets()
        self.programs = [Program]

    async def main(self):
        start = time.time()
        log(TAG, "Initializing...")

        self.server = Server()
        await self.server.start()

        self.markets.append(
            BinanceMarket(
                os.environ.get("BINANCE_API_KEY"),
                os.environ.get("BINANCE_SECRET")
            )
        )

        await self.markets.init()
        self.markets.run()

        log(TAG, f"{len(self.markets)} market(s) ready.")
        log(TAG, f"Initialized. ({(time.time() - start) * 1000 :.0f}ms)")

        self.programs = [
            MovingAverage()
        ]

        log(TAG, f"{len(self.programs)} program(s) loaded.")
        for program in self.programs:
            await program.init(self.markets)
        log(TAG, f"{len(self.programs)} program(s) up and running.")
        while True:
            for program in self.programs:
                await program.run_schedules(self.markets)
                await asyncio.sleep(.1)

        await self.server.stop()


if __name__ == "__main__":
    core = Core()
    asyncio.run(core.main())
