from __future__ import annotations

import logging

from app.market.market_data_provider import MarketDataProvider
from app.market.models import MarketSnapshot

logger = logging.getLogger(__name__)


class MarketEngine:
    """
    Builds a market snapshot for the dashboard.
    """

    SYMBOLS = {
        "nifty50": "^NSEI",
        "banknifty": "^NSEBANK",
        "india_vix": "^INDIAVIX",
        "usd_inr": "INR=X",
        "gold": "GC=F",
        "crude": "CL=F",
    }

    def __init__(self) -> None:

        self.provider = MarketDataProvider()

    def get_snapshot(self) -> MarketSnapshot:

        frames = self.provider.fetch_ohlcv(
            symbols=self.SYMBOLS.values(),
            period="5d",
            interval="1d",
        )

        values: dict[str, float] = {}

        for field, symbol in self.SYMBOLS.items():

            frame = frames.get(symbol)

            if frame is None or frame.empty:
                values[field] = 0.0
                continue

            try:
                values[field] = float(frame["Close"].iloc[-1])
            except Exception:
                values[field] = 0.0

        sentiment = self._market_sentiment(
            values["nifty50"],
            values["india_vix"],
        )

        return MarketSnapshot(
            nifty50=values["nifty50"],
            banknifty=values["banknifty"],
            india_vix=values["india_vix"],
            usd_inr=values["usd_inr"],
            gold=values["gold"],
            crude=values["crude"],
            market_sentiment=sentiment,
        )

    def _market_sentiment(
        self,
        nifty: float,
        vix: float,
    ) -> str:

        if nifty == 0:
            return "UNKNOWN"

        if vix < 15:
            return "BULLISH"

        if vix > 20:
            return "BEARISH"

        return "NEUTRAL"