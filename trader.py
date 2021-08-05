import asyncio
import math
import time

from comm.client import Client
from comm.streamer import Streamer
from misc.state import State


class RedFox:
    def __init__(self, client: Client, streamer: Streamer):
        self.opportunities = []
        self.client: Client = client
        self.streamer: Streamer = streamer
        pass

    def on_calculate(self, market):
        self.opportunities = []
        input = 100
        base = "BNB"
        start = time.time()
        for asset_a in market.assets:
            for asset_b in market.assets:
                if asset_a == asset_b:
                    continue
                if asset_a == base or asset_b == base:
                    continue

                route = [base, asset_a, asset_b, base]
                waypoints = []
                output = input
                for i in range(1, len(route)):
                    from_asset = route[i - 1]
                    to_asset = route[i]
                    ticker = market.cache_table[from_asset][to_asset]
                    if ticker is None:
                        break
                    # if ticker.quote_volume is None \
                    #         or market.convert(ticker.quote_asset, "USDT") is None \
                    #         or ticker.quote_volume * market.convert(ticker.quote_asset, "USDT") < 10000:
                    #     break
                    output = math.floor(float(output) / ticker.step_qty) * ticker.step_qty
                    output *= ticker.price_commissioned if ticker.quote_asset == to_asset else ticker.inv_price_commissioned
                    to_usd = market.convert(to_asset, "USDT")
                    output_usd = output * to_usd if to_usd else None

                    waypoints.append({
                        "symbol": ticker.symbol,
                        "asset": to_asset,
                        "price": ticker.best_bid_price,
                        "output": output_usd if to_usd else 0,
                        "change": ((output_usd - input) / input * 100) if to_usd else 0,
                        "withdrawable": (math.floor(
                            float(output) / ticker.step_qty) * ticker.step_qty) * to_usd if to_usd else 0
                    })
                else:
                    if output <= input:
                        continue
                    self.opportunities.append({
                        "route": route,
                        "waypoints": waypoints,
                        "output": output
                    })

        if len(self.opportunities) == 0:
            return
        self.opportunities = sorted(self.opportunities, key=lambda o: o["output"], reverse=True)
        print(
            f"{len(self.opportunities)} opportunities on {input} {base} (Calculated in {(time.time() - start) * 1000:.0f} ms)")
        for i in range(min(len(self.opportunities), 10)):
            print(("+{:.3f}% | {} -> {} -> {} -> {} | " +
                   "[{:8.3f}] -> {} {:10.4f} -> [{:8.3f} ({:.3f}%)]        " +
                   "[{:8.3f}] -> {} {:10.4f} -> [{:8.3f} ({:.3f}%)]        " +
                   "[{:8.3f}] -> {} {:10.4f} -> [{:8.3f} ({:.3f}%)]").format(
                (self.opportunities[i]["output"] - input) / input * 100,
                base,
                *[o["asset"].ljust(6) for o in self.opportunities[i]["waypoints"]],
                input,
                *[a for o in self.opportunities[i]["waypoints"] for a in
                  [o["symbol"].ljust(12), o["price"], o["output"], o["change"], o["withdrawable"]]]
            ))

    async def on_trade(self):
        while State.ok():
            while len(self.opportunities) == 0:
                await asyncio.sleep(1)

            opportunity = self.opportunities[0]

            # TODO all fetch current prices first via REST api
            # TODO risk assessment

            for i in range(1, len(opportunity["route"])):
                from_point = opportunity["route"][i - 1]
                to_point = opportunity["route"][i]
                waypoint = opportunity["waypoints"][i - 1]
                print(f"Trading from {from_point} to {to_point}")
                print("{}@depth20@100ms".format(waypoint["symbol"]))
                async with self.streamer.subscribe(["{}@depth20@100ms".format(waypoint["symbol"])]) as f:
                    async for msg in f:
                        for bid in msg["bids"]:
                            print(bid[0])

                # a = self.client.send_signed("POST", "/api/v3/order", {
                #     "symbol": "BTCBUSD",
                #     "side": "BUY",
                #     "type": "LIMIT",
                #     "timeInForce": "GTC",
                #     "quantity": .001234,
                #     "price": 100000
                # })
                await asyncio.sleep(.5)

            print(f"Trade completed.")
            await asyncio.sleep(.5)
