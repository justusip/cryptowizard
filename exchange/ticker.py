class Ticker:
    def __init__(self, symbol, base_asset, quote_asset):
        self.symbol = symbol
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.min_qty = None
        self.max_qty = None
        self.step_qty = None
        self.min_notional = None
        self.base_volume = None
        self.quote_volume = None
        self.trading_fee_maker = None
        self.trading_fee_taker = None
        self.price = None
        self.price_commissioned = None
        self.inv_price = None
        self.inv_price_commissioned = None