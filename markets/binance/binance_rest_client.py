import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import aiohttp

from misc.console import log, debug, error

TAG = "BNRS"
verbose = True

class BinanceRestClient:
    BASE_URL = "https://api.binance.com"

    # BASE_URL = "https://testnet.binance.vision"

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        self.session = aiohttp.ClientSession(
            headers={
                "Accept": "application/json;charset=utf-8",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
                "X-MBX-APIKEY": self.key
            }
        )

    def hash(self, string):
        return hmac.new(self.secret.encode("utf-8"), string.encode("utf-8"), hashlib.sha256).hexdigest()

    def time(self):
        return int(time.time() * 1000)

    async def request(self, method, path, params):
        url = self.BASE_URL + path + "?" + urlencode(params, True)
        debug(TAG, f"&r[&a->&r][{method[:3]}] {path} {params}")
        async with {
            "GET": self.session.get,
            "POST": self.session.post,
            "PUT": self.session.put,
            "DELETE": self.session.delete
        }.get(method, "GET")(url=url, params={}) as res:
            if res.status < 200 or res.status > 300:
                try:
                    res_json = await res.json()
                    raise Exception(f"Error {res.status}: {res_json}")
                except ValueError:
                    raise Exception(f"Error {res.status}")
            else:
                try:
                    res_json = await res.json()
                    debug(TAG, f"&r[&c<-&r][{res.status}] "
                               f"{res_json if len(str(res_json)) < 128 else f'(hidden - {len(str(res_json))} bytes)'}")
                    return res_json
                except ValueError:
                    raise Exception("Response formatting error.")

    async def send_unsigned(self, path, params=None):
        if params is None:
            params = {}
        return await self.request("GET", path, params)

    async def send_signed(self, method, path, params=None):
        if params is None:
            params = {}
        params["timestamp"] = self.time()
        params["signature"] = self.hash(urlencode(params, True))
        return await self.request(method, path, params)
