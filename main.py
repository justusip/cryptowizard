import asyncio
import time

from markets.binance.binance_market import BinanceMarket
from markets.markets import Markets
from misc.console import log
from programs.ma import MovingAverage
from programs.program import Program
from ui.server import Server

TAG = "Core"


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

        # Real Account - Use with precaution!
        self.markets.append(
            BinanceMarket(
                "yyJA1NNpb0GKYvt8ZQXU8ndeYBftNi1wHUjbvXrd4jyergodkbIiVnG74yyu9oYU",
                "9VLpQLMg0GCSnn0PQ8pNaDo8xVKNYN4Vzu4cEFa3ENqifHTpzImUBqpNe8Ebry6E"
            )
        )

        # Testnet Account
        # self.markets.append(
        #     BinanceMarket(
        #         "U0mgeLBjMFvL2OwFoKAvYCvdZjYD7LtFIuAlNc0dgrk4EE0r2v5rI25m7TZwCtvJ",
        #         "tkq6hF0C6OAsUl3EFgdpXxeqLEVFgoFQeQrWtklaM4F6n8KmYD3V96ULPGcqMX97"
        #     )
        # )

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
