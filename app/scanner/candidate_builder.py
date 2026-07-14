"""Candidate Builder for Vyom."""

from __future__ import annotations

from typing import Any

from app.scanner.technical_indicators import TechnicalIndicatorEngine


def build_candidate(
    symbol: str,
    dataframe: Any,
) -> dict[str, Any]:
    """
    Build a normalized candidate dictionary from market data.

    This function is shared by:
    - test_pipeline.py
    - paper_trade.py
    - scanner.py
    - Future Dashboard
    """

    candidate = {
        "symbol": symbol,
    }

    if dataframe is None:
        return candidate

    if hasattr(dataframe, "empty") and dataframe.empty:
        return candidate

    indicator_engine = TechnicalIndicatorEngine()

    indicator_result = indicator_engine.calculate(dataframe)

    candidate.update(indicator_result.to_mapping())

    candidate["dataframe"] = dataframe

    return candidate
