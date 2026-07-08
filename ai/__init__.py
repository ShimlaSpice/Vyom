"""AI domain package."""

# AI logic is separated from UI and data access so local models, rules, or
# orchestration strategies can evolve independently.

from ai.engine import AIDecisionEngine

__all__ = ["AIDecisionEngine"]
