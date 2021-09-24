from markets.binance.binance_market import BinanceMarket
from markets.markets import Markets
from programs.program import Program


class MovingAverage(Program):
    def __init__(self):
        super().__init__()
        self.buy_price = None
        self.sell_price = None

    async def init(self, markets: Markets):
        self.every(self.loop, seconds=5)

        b: BinanceMarket = markets["BNCE"]
        # self.buy_price = b.best_ask_price("BTCUSDT")
        # self.sell_price = b.round_down_price("BTCUSDT", self.buy_price * Decimal(1.02))
        # await b.quick_buy_at("BTCUSDT", self.buy_price, 1)
        # await b.quick_sell_at("BTCUSDT", self.sell_price, 1)

    async def loop(self, markets: Markets):
        b: BinanceMarket = markets["BNCE"]
        print(b.best_ask_price("BTCUSDT"))
