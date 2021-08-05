import asyncio
from datetime import datetime
from typing import Optional

import aiohttp

from comm.client import Client
from exchange.ticker import Ticker

from misc.console import log

TAG = "ui"


class Market:

    def __init__(self):
        self.cache_table = None
        self.tickers: [Ticker] = None
        self.assets = None
        self.last_updated = None
        self.on_updated_trigger: Optional[asyncio.Event] = None

    def on_init(self, client: Client):
        self.cache_table = {}
        self.tickers: [Ticker] = {}
        self.assets = set()

        info = client.send_unigned("/api/v3/exchangeInfo")["symbols"]
        fees = client.send_signed("GET", "/wapi/v3/tradeFee.html")
        for o in info:
            self.assets.add(o["baseAsset"])
            self.assets.add(o["quoteAsset"])

            if o["status"] == "TRADING":
                t = Ticker(o["symbol"], o["baseAsset"], o["quoteAsset"])
                self.tickers[o["symbol"]] = t
                t.min_qty = float([f for f in o["filters"] if f["filterType"] == "LOT_SIZE"][0]["minQty"])
                t.max_qty = float([f for f in o["filters"] if f["filterType"] == "LOT_SIZE"][0]["maxQty"])
                t.step_qty = float([f for f in o["filters"] if f["filterType"] == "LOT_SIZE"][0]["stepSize"])
                t.min_notional = float([f for f in o["filters"] if f["filterType"] == "MIN_NOTIONAL"][0]["minNotional"])

                t.trading_fee_maker = float([o for o in fees["tradeFee"] if o["symbol"] == t.symbol][0]["maker"])
                t.trading_fee_taker = float([o for o in fees["tradeFee"] if o["symbol"] == t.symbol][0]["taker"])

        for asset in self.assets:
            self.cache_table[asset] = {o: None for o in self.assets}

        for k, v in self.tickers.items():
            self.cache_table[v.quote_asset][v.base_asset] = v
            self.cache_table[v.base_asset][v.quote_asset] = v

        prices = client.send_unigned("/api/v3/ticker/bookTicker")
        for t in prices:
            if t["symbol"] not in self.tickers:
                continue
            ticker = self.tickers[t["symbol"]]
            ticker.price = float(t["bidPrice"])  # sell
            ticker.price_commissioned = ticker.price * (1 - .00075)
            ticker.inv_price = 1 / float(t["askPrice"])
            ticker.inv_price_commissioned = ticker.inv_price * (1 - .00075)

        log(TAG,
            f"Market definitions updated. {len(self.assets)} assets and {len(self.tickers)} active tickers were loaded.")

    async def run(self, streamer):
        # async with streamer.subscribe(["!bookTicker"]) as f:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect('wss://stream.binance.com:9443/ws/!bookTicker') as ws:
                async for data in ws:
                    msg = data.json()
                    # for msg in msgs:
                    if msg["s"] not in self.tickers:
                        continue
                    ticker = self.tickers[msg["s"]]

                    # if msg["s"] == "BTCUSDT":
                    #     print(msg["s"], msg["a"], msg["b"])
                    ticker.best_bid_price = float(msg["b"])  # sell
                    ticker.price_commissioned = ticker.best_bid_price * (1 - .00075)
                    ticker.best_sell_price = 1 / float(msg["a"])
                    ticker.inv_price_commissioned = ticker.best_sell_price * (1 - .00075)

                    # ticker.base_volume = float(msg["v"])
                    # ticker.quote_volume = float(msg["q"])
                    # self.last_updated = datetime.now()
                    self.on_updated_trigger.set()

    def convert(self, f, t):
        if f == t:
            return 1
        ticker = self.cache_table[f][t]
        if ticker is None or ticker.best_bid_price is None:
            return None
        if t == ticker.quote_asset:
            return ticker.best_bid_price
        else:
            return ticker.best_sell_price
