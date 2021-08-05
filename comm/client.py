import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import requests


class Client:
    BASE_URL = "https://api.binance.com"
    # BASE_URL = "https://testnet.binance.vision"

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        self.session = requests.session()
        self.session.headers.update({"Accept": "application/json;charset=utf-8",
                                     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
                                     "X-MBX-APIKEY": self.key})

    def hash(self, string):
        return hmac.new(self.secret.encode("utf-8"), string.encode("utf-8"), hashlib.sha256).hexdigest()

    def time(self):
        return int(time.time() * 1000)

    def request(self, method, path, params):
        url = self.BASE_URL + path + "?" + urlencode(params, True)
        response = {
            "GET": self.session.get,
            "POST": self.session.post,
            "PUT": self.session.put,
            "DELETE": self.session.delete
        }.get(method, "GET")(url=url, params={})
        if response.status_code < 200 or response.status_code > 300:
            raise Exception(f"Error {response.status_code}: {response.json()}")
        try:
            return response.json()
        except ValueError:
            raise Exception("Response formatting error.")

    def send_unigned(self, path, params=None):
        if params is None:
            params = {}
        return self.request("GET", path, params)

    def send_signed(self, method, path, params=None):
        if params is None:
            params = {}
        params["timestamp"] = self.time()
        params["signature"] = self.hash(urlencode(params, True))
        return self.request(method, path, params)
