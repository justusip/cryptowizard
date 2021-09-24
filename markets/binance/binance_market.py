import asyncio
import datetime
import math
import time
from decimal import Decimal
from typing import Optional
import ntplib

import aiohttp
from aiohttp import ClientWebSocketResponse, WSMessage

from markets.binance.binance_rest_client import BinanceRestClient
from markets.market import Market
from misc.console import log, error

TAG = "BNXX"


class BinanceMarket(Market):
    def __init__(self, key, secret):
        super().__init__("BNCE")
        self.client = BinanceRestClient(key, secret)
        self.tickers: dict[str, Ticker] = {}
        self.ws: Optional[ClientWebSocketResponse] = None

    async def init(self):
        tk_google_res = ntplib.NTPClient().request('time.google.com')
        tk_google_time = tk_google_res.tx_time * 1000
        tk_google_diff = -tk_google_res.offset * 1000

        tk_binance_local = time.time() * 1000
        tk_binance_res = await self.client.send_unsigned("/api/v3/time")
        tk_binance_time = int(tk_binance_res["serverTime"])
        tk_binance_diff = tk_binance_local - tk_binance_time

        log(TAG, f"Google NTP time:     {tk_google_time:.0f} "
                 f"({abs(tk_google_diff):.0f}ms {'ahead' if tk_google_diff > 0 else 'behind'}).")
        log(TAG, f"Binance server time: {tk_binance_time:.0f} "
                 f"({abs(tk_binance_diff):.0f}ms {'ahead' if tk_binance_diff > 0 else 'behind'}).")

        if abs(tk_binance_diff) > 1000:
            raise Exception("Local time and Binance server has time difference greater than 1000ms.")

        for o in (await self.client.send_unsigned("/api/v3/exchangeInfo"))["symbols"]:
            if o["status"] != "TRADING":
                continue

            t = Ticker(o["symbol"], o["baseAsset"], o["quoteAsset"])
            self.tickers[o["symbol"]] = t

            t.qty_precision = int(o["quotePrecision"])
            t.price_precision = int(o["baseAssetPrecision"])

            def filter_val(filter_type: str, key: str):
                return [f for f in o["filters"] if f["filterType"] == filter_type][0][key]

            t.price_min = Decimal(filter_val("PRICE_FILTER", "minPrice"))
            t.price_max = Decimal(filter_val("PRICE_FILTER", "maxPrice"))
            t.price_step = Decimal(filter_val("PRICE_FILTER", "tickSize"))
            if Decimal.is_zero(t.price_min) or Decimal.is_zero(t.price_max) or Decimal.is_zero(t.price_step):
                t.price_filter_disabled = True

            t.qty_min = Decimal(filter_val("LOT_SIZE", "minQty"))
            t.qty_max = Decimal(filter_val("LOT_SIZE", "maxQty"))
            t.qty_step = Decimal(filter_val("LOT_SIZE", "stepSize"))

            t.min_notional = Decimal(filter_val("MIN_NOTIONAL", "minNotional"))

        for o in await self.client.send_signed("GET", "/sapi/v1/asset/tradeFee"):
            if o["symbol"] not in self.tickers:
                continue
            t = self.tickers[o["symbol"]]
            t.trading_fee_maker = Decimal(o["makerCommission"])
            t.trading_fee_taker = Decimal(o["takerCommission"])

        for o in await self.client.send_unsigned("/api/v3/ticker/bookTicker"):
            if o["symbol"] not in self.tickers:
                continue
            t = self.tickers[o["symbol"]]
            t.best_bid_price = Decimal(o["bidPrice"])
            t.best_bid_quantity = Decimal(o["bidQty"])
            t.best_ask_price = Decimal(o["askPrice"])
            t.best_ask_quantity = Decimal(o["askQty"])

        for o in await self.client.send_unsigned("/api/v3/ticker/24hr"):
            if o["symbol"] not in self.tickers:
                continue
            t = self.tickers[o["symbol"]]
            t.high = Decimal(o["highPrice"])
            t.low = Decimal(o["lowPrice"])
            t.base_volume = Decimal(o["volume"])
            t.quote_volume = Decimal(o["quoteVolume"])

        log(TAG, f"Market definitions updated. {len(self.tickers)} active tickers were loaded.")

    async def run(self):
        bytes_recv = 0

        async def count():
            nonlocal bytes_recv
            interval = 1
            while True:
                await asyncio.sleep(interval)
                bytes_per_sec = bytes_recv / interval
                log("WS", f"{bytes_per_sec / 1024:.3f}kb/s")
                bytes_recv = 0

        # asyncio.ensure_future(count())

        try:
            log(TAG, "Connecting to Binance's WebSocket market streams...")
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect('wss://stream.binance.com:9443/stream') as self.ws:
                    log(TAG, "Connected to Binance's WebSocket market streams.")
                    await self.ws.send_json({
                        "method": "SUBSCRIBE",
                        "params":
                            [
                                "!bookTicker",
                                "!miniTicker@arr"
                            ],
                        "id": 1
                    })
                    msg: WSMessage
                    async for msg in self.ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            bytes_recv += len(msg.data)
                            msg_json = msg.json()
                            if "stream" in msg_json:
                                payload = msg_json["data"]
                                if msg_json["stream"] == "!bookTicker":
                                    if payload["s"] not in self.tickers:
                                        continue
                                    ticker = self.tickers[payload["s"]]
                                    ticker.ws_best_last_updated = time.time()
                                    ticker.best_bid_price = Decimal(payload["b"])
                                    ticker.best_bid_quantity = Decimal(payload["B"])
                                    ticker.best_ask_price = Decimal(payload["a"])
                                    ticker.best_ask_quantity = Decimal(payload["A"])
                                elif msg_json["stream"] == "!miniTicker@arr":
                                    for p in payload:
                                        if p["s"] not in self.tickers:
                                            continue
                                        ticker = self.tickers[p["s"]]
                                        ticker.ws_24h_last_updated = time.time()
                                        ticker.high = Decimal(p["h"])
                                        ticker.low = Decimal(p["l"])
                                        ticker.base_volume = Decimal(p["v"])
                                        ticker.quote_volume = Decimal(p["q"])
                            elif "result" in msg_json:
                                pass
                            else:
                                log(TAG, msg_json)

                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            error(TAG, f"WebSocket connection was closed unexpectedly {self.ws.exception()}")
                            break
            log(TAG, "Disconnected from Binance's WebSocket market streams. Reconnecting...")
        except aiohttp.ClientError as ex:
            error(TAG, "Failed to connect to Binance's WebSocket market streams. "
                       f"Retrying in a second... ({ex})")

    async def fetch_balance(self, asset: str) -> Optional[Decimal]:
        data = await self.client.send_signed("GET", "/api/v3/account")
        for o in data["balances"]:
            if asset == o["asset"]:
                return Decimal(o["free"])
        return None

    async def quick_buy_at(self, symbol: str, ask_price: Decimal, quote_percent: float) -> bool:
        ticker = self.tickers[symbol]
        quote_balance = await self.fetch_balance(ticker.quote_asset)
        base_buy_qty = self.round_down_qty(symbol, quote_balance * Decimal(quote_percent) / ask_price)
        print(quote_balance * Decimal(quote_percent) / ask_price)
        print(base_buy_qty)
        return await self.buy(symbol, base_buy_qty, ask_price)

    async def quick_sell_at(self, symbol: str, bid_price: Decimal, base_percent: float) -> bool:
        ticker = self.tickers[symbol]
        base_balance = await self.fetch_balance(ticker.base_asset)
        base_sell_qty = self.round_down_qty(symbol, base_balance * Decimal(base_percent))
        return await self.sell(symbol, base_sell_qty, bid_price)

    def round_down_qty(self, ticker: str, amt: Decimal) -> Optional[Decimal]:
        qty_step = self.tickers[ticker].qty_step
        return math.floor(amt / qty_step) * qty_step

    def round_down_price(self, ticker: str, price: Decimal) -> Optional[Decimal]:
        price_step = self.tickers[ticker].price_step
        return math.floor(price / price_step) * price_step

    def commission(self, symbol: str) -> Decimal:
        return self.tickers[symbol].trading_fee_taker

    def best_bid_price(self, symbol: str) -> Decimal:
        return self.tickers[symbol].best_ask_price

    def best_bid_quantity(self, symbol: str) -> Decimal:
        return self.tickers[symbol].best_bid_quantity

    def best_ask_price(self, symbol: str) -> Decimal:
        return self.tickers[symbol].best_ask_price

    def best_ask_quantity(self, symbol: str) -> Decimal:
        return self.tickers[symbol].best_ask_quantity

    def high(self, symbol: str) -> Decimal:
        return self.tickers[symbol].high

    def low(self, symbol: str) -> Decimal:
        return self.tickers[symbol].low

    def base_volume(self, symbol: str) -> Decimal:
        return self.tickers[symbol].base_volume

    def quote_volume(self, symbol: str) -> Decimal:
        return self.tickers[symbol].quote_volume

    async def buy(self,
                  symbol: str,
                  quantity: Decimal,
                  price: Decimal) -> bool:
        return await self.order(symbol, True, quantity, price)

    async def sell(self,
                   symbol: str,
                   quantity: Decimal,
                   price: Decimal) -> bool:
        return await self.order(symbol, False, quantity, price)

    async def order(self,
                    symbol: str,
                    buy: bool,
                    quantity: Decimal,
                    price: Decimal) -> bool:
        ticker = self.tickers[symbol]

        if (quantity - ticker.qty_min) % ticker.qty_step != Decimal(0):
            error(TAG, "Filter 1a failed.")
            return False
        if not quantity >= ticker.qty_min:
            error(TAG, "Filter 1b failed.")
            return False
        if not quantity <= ticker.qty_max:
            error(TAG, "Filter 1c failed.")
            return False

        if not ticker.price_filter_disabled:
            if (price - ticker.price_min) % ticker.price_step != Decimal(0):
                error(TAG, "Filter 2a failed.")
                return False
            if not price >= ticker.price_min:
                error(TAG, "Filter 2b failed.")
                return False
            if not price <= ticker.price_max:
                error(TAG, "Filter 2c failed.")
                return False

        if not price * quantity >= ticker.min_notional:
            error(TAG, "Filter 3 failed.")
            return False

        # TODO PERCENT_PRICE check

        log(TAG, "->" + {
            "symbol": symbol,
            "side": "BUY" if buy else "SELL",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": f"{quantity:.{ticker.qty_precision}f}",
            "price": f"{price:.{ticker.price_precision}f}"
        }.__str__())

        log(TAG, f"{'Buying' if buy else 'Selling'} {quantity} {ticker.base_asset} at {price} {ticker.quote_asset}...")
        start = time.time()
        end = None
        response = await self.client.send_signed("POST", "/api/v3/order", params={
            "symbol": symbol,
            "side": "BUY" if buy else "SELL",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": f"{quantity:.{ticker.qty_precision}f}",
            "price": f"{price:.{ticker.price_precision}f}"
        })

        if response["status"] != "FILLED":
            while True:
                status = await self.client.send_signed("GET", "/api/v3/order", params={
                    "symbol": symbol,
                    "orderId": response["orderId"]
                })
                if status["status"] == "FILLED":
                    break
                await asyncio.sleep(.1)
            end = time.time()

        log(TAG, f"{'Bought' if buy else 'Sold'} {quantity} {ticker.base_asset} at {price} {ticker.quote_asset} "
                 f"({'instant' if end is None else f'{end - start:.2f}'}s)")
        return True


class Ticker:
    def __init__(self, symbol, base_asset, quote_asset):
        self.symbol = symbol
        self.base_asset = base_asset
        self.quote_asset = quote_asset

        self.qty_precision = None
        self.qty_min = None
        self.qty_max = None
        self.qty_step = None

        self.price_precision = None
        self.price_filter_disabled = False
        self.price_min = None
        self.price_max = None
        self.price_step = None

        self.min_notional = None
        self.percent_price = None

        self.high = None
        self.low = None
        self.base_volume = None
        self.quote_volume = None

        self.trading_fee_maker = None
        self.trading_fee_taker = None

        self.best_bid_price = None
        self.best_bid_quantity = None
        self.best_ask_price = None
        self.best_ask_quantity = None

        self.ws_best_last_updated = None
        self.ws_24h_last_updated = None
