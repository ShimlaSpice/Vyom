#!/usr/bin/env python3
"""Integration script for the V0.7 market-data → indicators → scoring → decision pipeline."""

from __future__ import annotations

import sys
from typing import Any

from app.market.market_data_provider import MarketDataProvider
from app.scanner.decision_engine import DecisionEngine
from app.scanner.scoring import ScoringEngine
from app.scanner.technical_indicators import TechnicalIndicatorEngine


def normalize_symbol(symbol: str) -> str:
    """Return an exchange-qualified ticker for Indian equities when needed."""

    cleaned = symbol.strip().upper()
    if cleaned.endswith((".NS", ".BO", ".NSE")):
        return cleaned
    return f"{cleaned}.NS"


def build_candidate(symbol: str, dataframe: Any) -> dict[str, Any]:
    """Create a scoring candidate from a downloaded OHLCV frame."""

    candidate: dict[str, Any] = {"symbol": symbol}
    if dataframe is None:
        return candidate

    if hasattr(dataframe, "empty") and dataframe.empty:
        return candidate

    try:
        indicator_result = TechnicalIndicatorEngine().calculate(dataframe)
        candidate.update(indicator_result.to_mapping())
        candidate["dataframe"] = dataframe
    except Exception as exc:  # pragma: no cover - defensive guard
        candidate["pipeline_error"] = str(exc)
    return candidate


def format_recommendation(symbol: str, recommendation: Any) -> str:
    """Render a recommendation object into a readable multi-line string."""

    lines = [
        f"=== {symbol} ===",
        f"Action: {recommendation.action}",
        f"Quality: {recommendation.trade_quality}",
        f"Confidence: {recommendation.confidence:.2f}%",
        f"Risk: {recommendation.risk_level}",
        f"Summary: {recommendation.summary}",
        f"Positive signals: {', '.join(recommendation.positive_signals) if recommendation.positive_signals else 'None'}",
        f"Negative signals: {', '.join(recommendation.negative_signals) if recommendation.negative_signals else 'None'}",
        f"Warnings: {', '.join(recommendation.warnings) if recommendation.warnings else 'None'}",
        f"Entry: {recommendation.entry_price} | Stop: {recommendation.stop_loss} | Target: {recommendation.target_price} | RR: {recommendation.risk_reward_ratio}",
    ]
    return "\n".join(lines)


def main() -> int:
    """Run the live market-data pipeline for the configured symbols."""

    symbols = ["BEL", "RELIANCE", "TCS"]
    provider = MarketDataProvider(symbols=symbols, cache_ttl_seconds=300, timeout=20, max_retries=2, retry_delay_seconds=1.0)
    qualified_symbols = [normalize_symbol(symbol) for symbol in symbols]
    scoring_engine = ScoringEngine()
    decision_engine = DecisionEngine()

    for symbol, qualified_symbol in zip(symbols, qualified_symbols, strict=True):
        print(f"Processing {symbol}...", flush=True)
        try:
            frame_map = provider.fetch_ohlcv(symbols=[qualified_symbol], period="2mo", interval="1d")
            dataframe = frame_map.get(qualified_symbol)
            candidate = build_candidate(symbol, dataframe)
            print("\nDEBUG Candidate")
            print(candidate.keys())
            print(candidate)
            print()
            score_result = scoring_engine.score_stock(candidate)
            recommendation = decision_engine.make_recommendation(score_result)
            print(format_recommendation(symbol, recommendation), flush=True)
            print(flush=True)
        except Exception as exc:  # pragma: no cover - defensive guard
            print(f"ERROR processing {symbol}: {exc}", flush=True)
            print(flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
