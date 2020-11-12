import logging
import cryptowatch as cw
import asyncio
import queue
from decimal import Decimal


class OrderbookWatcher:

    def __init__(self, market="KRAKEN:BTCUSD", delta_qsize=10000):
        # Orderbook related data structure
        self.delta_queue = queue.Queue(maxsize=delta_qsize)
        self.asks = {}
        self.bids = {}
        # Market related
        self.market = market.lower()
        self.exchange, self.pair = self.market.split(":")
        # Get market Id
        instruments = cw.instruments.get(self.pair)
        self.market_id = [
            m.id for m in instruments.instrument.markets if m.exchange == self.exchange
        ].pop()
        self.quote = instruments.instrument.quote.symbol
        self.base = instruments.instrument.base.symbol

    def watch(self):
        # Subscribe to orderbook delta updates
        delta_resource = "markets:{}:book:deltas".format(self.market_id)
        cw.stream.subscriptions = [delta_resource]
        # For each delta, update the orderbook
        cw.stream.on_orderbook_delta_update = self._queue_orderbook_deltas
        cw.stream.connect()
        asyncio.run(self._process_deltas(self.delta_queue, self.on_update, self.asks, self.bids))


    def _queue_orderbook_deltas(self, delta_update):
        """
            For each orderbook delta, queue the deltas to be applied.
        """
        self.delta_queue.put_nowait(delta_update)


    @staticmethod
    async def _process_deltas(delta_queue, callback, asks, bids):
        while True:
            delta_update = delta_queue.get()
            # If no delta operation to apply,
            # wait 500ms for a new delta update.
            if delta_update is None:
                await asyncio.sleep(0.5)
            # Concurrently update asks and bids.
            await asyncio.gather(
                asyncio.create_task(
                    OrderbookWatcher._update_asks(asks, delta_update.marketUpdate.orderBookDeltaUpdate.asks)
                ),
                asyncio.create_task(
                    OrderbookWatcher._update_bids(bids, delta_update.marketUpdate.orderBookDeltaUpdate.bids)
                ),
            )
            delta_queue.task_done()
            # Call default orderbook update callback
            callback()


    def on_update(self):
        ## Print orderbook, only top 20 on each side, with mid-price
        top_20_asks = [
            "{:.2f}    {:2.8f}".format(float(p), float(a)) for p, a in self.asks.items()
        ][:20]
        top_20_bids = [
            "{:.2f}    {:2.8f}".format(float(p), float(a)) for p, a in self.bids.items()
        ][:20]
        top_20_asks.reverse()
        best_ask = Decimal(next(iter(self.asks)))
        best_bid = Decimal(next(iter(self.bids)))
        mid_price = (best_ask + best_bid) / 2
        spread = best_ask - best_bid
        # Clear the screen
#        print(chr(27) + "[2J", flush=True)
        print("> {}".format(self.market.upper()), flush=True)
        CSI = "\x1B["
        print(CSI + "31;40m" + "\n".join(top_20_asks) + CSI + "0m", flush=True)
        print(
            CSI
            + "1;40m"
            + " {:.1f} {}".format(mid_price, self.quote.upper())
            + CSI
            + "0m"
            + " spread:{}".format(spread),
            flush=True,
        )
        print(CSI + "32;40m" + "\n".join(top_20_bids) + CSI + "0m", flush=True)


    @staticmethod
    async def _update_asks(asks, ask_ops):
        ## Update asks
        # Add new ask entries
        for entry in ask_ops.set:
            asks[str(entry.priceStr)] = entry.amountStr
        # If we added new element, re-sort the ASKS, from lowest to highest
        if len(ask_ops.set):
            asks = {
                k: v
                for k, v in sorted(asks.items(), key=lambda x: (float(x[0]), len(x[0])))
            }
        # Remove any traded ask entries
        for price in ask_ops.removeStr:
            try:
                del asks[str(price)]
            except:
                pass


    @staticmethod
    async def _update_bids(bids, bid_ops):
        ## Update bids
        # Add new bid entries
        for entry in bid_ops.set:
            bids[str(entry.priceStr)] = entry.amountStr
        # If we added new element, re-sort the BIDS, from highest to lowest
        if len(bid_ops.set):
            bids = {
                k: v
                for k, v in sorted(bids.items(), key=lambda x: float(x[0]), reverse=True)
            }
        # Remove any traded bid entries
        for price in bid_ops.removeStr:
            try:
                del bids[str(price)]
            except:
                pass

