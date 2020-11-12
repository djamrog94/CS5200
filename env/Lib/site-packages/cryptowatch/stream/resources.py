from marshmallow import Schema, fields, pprint, post_load
from decimal import Decimal


# Common to all marketUpdates


class MarketSchema(Schema):
    exchangeId = fields.Str()
    currencyPairId = fields.Str()
    marketId = fields.Str()


# Common to orderbook related updates


class BidAskResource:
    def __init__(self, priceStr, amountStr):
        self.price = Decimal(priceStr)
        self.amount = Decimal(amountStr)

    def __repr__(self):
        return "{}@{}".format(self.price, self.amount)


class BidAskSchema(Schema):
    priceStr = fields.Str()
    amountStr = fields.Str()

    @post_load
    def make_asset(self, data, **kwargs):
        return BidAskResource(**data)


# OrderBook Delta Market Update Object Serialization


class OrderbookDeltaResource:
    def __init__(self, marketUpdate):
        self.exchange_id = marketUpdate.get("market").get("exchangeId")
        self.currency_pair_id = marketUpdate.get("market").get("currencyPairId")
        self.market_id = marketUpdate.get("market").get("marketId")
        self.book = marketUpdate.get("orderBookDeltaUpdate")

    def __repr__(self):
        return "<OrderbookDelta(Exchange#{self.exchange_id}:Pair#{self.currency_pair_id})>".format(
            self=self
        )


class OrderBookDeltaUpdateResource:
    def __init__(self, bids, asks, seqNum=0):
        self.bids = bids
        self.asks = asks
        self.seq_num = seqNum


class BidAskDeltaResource(Schema):
    def __init__(self, removeStr, set):
        self.remove = removeStr
        self.set = set

    def __repr__(self):
        return "<BidAskDeltaResource()>"


class BidAskDeltaSchema(Schema):
    removeStr = fields.List(fields.Str(), missing=[])
    set = fields.List(fields.Nested(BidAskSchema), missing=[])

    @post_load
    def make_asset(self, data, **kwargs):
        return BidAskDeltaResource(**data)


class OrderBookDeltaUpdateSchema(Schema):
    seqNum = fields.Int(missing=0)
    bids = fields.Nested(BidAskDeltaSchema)
    asks = fields.Nested(BidAskDeltaSchema)

    @post_load
    def make_asset(self, data, **kwargs):
        return OrderBookDeltaUpdateResource(**data)


class OrderbookDeltaMarketUpdateMessage(Schema):
    market = fields.Nested(MarketSchema)
    orderBookDeltaUpdate = fields.Nested(OrderBookDeltaUpdateSchema)


class OrderbookDeltaMarketUpdateSchema(Schema):
    marketUpdate = fields.Nested(OrderbookDeltaMarketUpdateMessage)

    @post_load
    def make_asset(self, data, **kwargs):
        return OrderbookDeltaResource(**data)


# OrderBook Snapshot Market Update Object Serialization


class OrderbookSnapshotResource:
    def __init__(self, marketUpdate):
        self.exchange_id = marketUpdate.get("market").get("exchangeId")
        self.currency_pair_id = marketUpdate.get("market").get("currencyPairId")
        self.market_id = marketUpdate.get("market").get("marketId")
        self.book = marketUpdate.get("orderBookUpdate")

    def __repr__(self):
        return "<Orderbook(Exchange#{self.exchange_id}:Pair#{self.currency_pair_id})>".format(
            self=self
        )


class OrderBookSnapshotUpdateResource:
    def __init__(self, bids, asks, seqNum=0):
        self.bids = bids
        self.asks = asks
        self.seq_num = seqNum


class OrderBookSnapshotUpdateSchema(Schema):
    seqNum = fields.Int(missing=0)
    bids = fields.List(fields.Nested(BidAskSchema))
    asks = fields.List(fields.Nested(BidAskSchema))

    @post_load
    def make_asset(self, data, **kwargs):
        return OrderBookSnapshotUpdateResource(**data)


class OrderbookSnapshotMarketUpdateMessage(Schema):
    market = fields.Nested(MarketSchema)
    orderBookUpdate = fields.Nested(OrderBookSnapshotUpdateSchema)


class OrderbookSnapshotMarketUpdateSchema(Schema):
    marketUpdate = fields.Nested(OrderbookSnapshotMarketUpdateMessage)

    @post_load
    def make_asset(self, data, **kwargs):
        return OrderbookSnapshotResource(**data)


# OrderBook Spread Market Update Object Serialization


class SpreadResource:
    def __init__(self, marketUpdate):
        self.exchange_id = marketUpdate.get("market").get("exchangeId")
        self.currency_pair_id = marketUpdate.get("market").get("currencyPairId")
        self.market_id = marketUpdate.get("market").get("marketId")
        self.spread = marketUpdate.get("orderBookSpreadUpdate")

    def __repr__(self):
        return "<Spread(Exchange#{self.exchange_id}:Pair#{self.currency_pair_id})>".format(
            self=self
        )


class OrderBookSpreadUpdateResource:
    def __init__(self, timestamp, bid, ask):
        self.timestamp = timestamp
        self.bid = bid
        self.ask = ask


class OrderBookSpreadUpdateSchema(Schema):
    timestamp = fields.Str()
    bid = fields.Nested(BidAskSchema)
    ask = fields.Nested(BidAskSchema)

    @post_load
    def make_asset(self, data, **kwargs):
        return OrderBookSpreadUpdateResource(**data)


class SpreadMarketUpdateMessage(Schema):
    market = fields.Nested(MarketSchema)
    orderBookSpreadUpdate = fields.Nested(OrderBookSpreadUpdateSchema)


class OrderbookSpreadMarketUpdateSchema(Schema):
    marketUpdate = fields.Nested(SpreadMarketUpdateMessage)

    @post_load
    def make_asset(self, data, **kwargs):
        return SpreadResource(**data)


# Candlestick Market Update Object Serialization


class CandlesResource:
    def __init__(self, marketUpdate):
        self.exchange_id = marketUpdate.get("market").get("exchangeId")
        self.currency_pair_id = marketUpdate.get("market").get("currencyPairId")
        self.market_id = marketUpdate.get("market").get("marketId")
        self.candles = marketUpdate.get("intervalsUpdate").get("intervals")

    def __repr__(self):
        return "<Candle(Exchange#{self.exchange_id}:Pair#{self.currency_pair_id})>".format(
            self=self
        )


class CandleResource:
    def __init__(self, closetime, ohlc, volumeBaseStr, volumeQuoteStr, periodName):
        self.close_timestamp = closetime
        self.period = periodName
        self.open = Decimal(ohlc.get("openStr"))
        self.high = Decimal(ohlc.get("highStr"))
        self.low = Decimal(ohlc.get("lowStr"))
        self.close = Decimal(ohlc.get("closeStr"))
        self.volume = Decimal(volumeQuoteStr)
        self.volume_base = Decimal(volumeBaseStr)


class CandleSchema(Schema):
    closetime = fields.Str()
    periodName = fields.Str()
    ohlc = fields.Dict(keys=fields.Str(), values=fields.Str())
    volumeBaseStr = fields.Str()
    volumeQuoteStr = fields.Str()

    @post_load
    def make_asset(self, data, **kwargs):
        return CandleResource(**data)


class CandlesSchema(Schema):
    intervals = fields.List(fields.Nested(CandleSchema))


class CandlesMarketUpdateMessage(Schema):
    market = fields.Nested(MarketSchema)
    intervalsUpdate = fields.Nested(CandlesSchema)


class CandleMarketUpdateSchema(Schema):
    marketUpdate = fields.Nested(CandlesMarketUpdateMessage)

    @post_load
    def make_asset(self, data, **kwargs):
        return CandlesResource(**data)


# Trade Market Update Object Serialization


class TradesResource:
    def __init__(self, marketUpdate):
        self.exchange_id = marketUpdate.get("market").get("exchangeId")
        self.currency_pair_id = marketUpdate.get("market").get("currencyPairId")
        self.market_id = marketUpdate.get("market").get("marketId")
        self.trades = marketUpdate.get("tradesUpdate").get("trades")

    def __repr__(self):
        return "<Trades(Exchange#{self.exchange_id}:Pair#{self.currency_pair_id})>".format(
            self=self
        )


class TradeResource:
    def __init__(
        self,
        timestampNano,
        timestamp,
        priceStr,
        amountStr,
        orderSide="",
        side="",
        externalId="",
    ):
        self.external_id = externalId
        self.timestamp_nano = timestampNano
        self.timestamp = timestamp
        self.price = Decimal(priceStr)
        self.amount = Decimal(amountStr)
        self.order_side = orderSide or side


class TradeSchema(Schema):
    externalId = fields.Str(missing="")
    timestamp = fields.Str()
    timestampNano = fields.Str()
    priceStr = fields.Str()
    amountStr = fields.Str()
    orderSide = fields.Str(missing="")
    side = fields.Str(missing="")

    @post_load
    def make_asset(self, data, **kwargs):
        return TradeResource(**data)


class TradesSchema(Schema):
    trades = fields.List(fields.Nested(TradeSchema))


class TradeMarketUpdateMessage(Schema):
    market = fields.Nested(MarketSchema)
    tradesUpdate = fields.Nested(TradesSchema)


class TradeMarketUpdateSchema(Schema):
    marketUpdate = fields.Nested(TradeMarketUpdateMessage)

    @post_load
    def make_asset(self, data, **kwargs):
        return TradesResource(**data)
