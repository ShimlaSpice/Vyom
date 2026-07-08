"""AI decision engine boundaries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class DecisionContext:
    """Describe the input for a future AI inference run."""

    symbol: str
    horizon: str


class AIDecisionEngine:
    """Encapsulate AI scoring and explainability boundaries."""

    def build_context(self, symbol: str, horizon: str) -> DecisionContext:
        """Build a typed AI decision context."""

        return DecisionContext(symbol=symbol, horizon=horizon)

    def evaluate(self, context: DecisionContext) -> dict[str, str]:
        """Reserve the AI inference boundary for future implementation."""

        raise NotImplementedError("AI decisioning is not implemented yet")
