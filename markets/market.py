import abc
from decimal import Decimal
from typing import Optional


class Market:
    def __init__(self,
                 name: str):
        __metaclass__ = abc.ABCMeta
        self.name = name

    @abc.abstractmethod
    async def fetch_balance(self,
                            asset: str) -> Optional[Decimal]:
        pass

    @abc.abstractmethod
    def best_bid_price(self,
                       symbol: str) -> Decimal:
        pass

    @abc.abstractmethod
    def best_bid_quantity(self,
                          symbol: str) -> Decimal:
        pass

    @abc.abstractmethod
    def best_ask_price(self,
                       symbol: str) -> Decimal:
        pass

    @abc.abstractmethod
    def best_ask_quantity(self,
                          symbol: str) -> Decimal:
        pass

    @abc.abstractmethod
    def base_volume(self,
                    symbol: str) -> Decimal:
        pass

    @abc.abstractmethod
    def quote_volume(self,
                     symbol: str) -> Decimal:
        pass
