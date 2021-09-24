import asyncio
from typing import Optional

from markets.market import Market


class Markets:
    def __init__(self):
        self.markets: [Markets] = []

    async def init(self):
        for market in self.markets:
            await market.init()

    def run(self):
        for market in self.markets:
            asyncio.ensure_future(market.run())

    def append(self, market: Market):
        self.markets.append(market)

    def __getitem__(self, key: str) -> Optional[Market]:
        for market in self.markets:
            if market.name == key:
                return market
        return None

    def __len__(self):
        return self.markets.__len__()