from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MarketSnapshot:

    nifty50: float = 0.0
    banknifty: float = 0.0
    india_vix: float = 0.0
    usd_inr: float = 0.0
    gold: float = 0.0
    crude: float = 0.0

    market_sentiment: str = "NEUTRAL"