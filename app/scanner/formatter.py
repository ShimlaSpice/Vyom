"""
Terminal formatter for VYOM scanner output.
"""

from __future__ import annotations

from app.scanner.decision_engine import TradeRecommendation


class ScannerFormatter:
    """
    Formats TradeRecommendation objects into a readable terminal report.
    """

    def format(
        self,
        recommendations: list[TradeRecommendation],
    ) -> str:

        if not recommendations:
            return "No recommendations found."

        lines: list[str] = []

        lines.append("=" * 70)
        lines.append("                     VYOM MARKET SCANNER")
        lines.append("=" * 70)
        lines.append("")

        for index, rec in enumerate(recommendations, start=1):

            lines.append("-" * 70)
            lines.append(f"{index}. {rec.symbol}")
            lines.append("-" * 70)

            lines.append(f"Action       : {rec.action}")
            lines.append(f"Score        : {rec.total_score}")
            lines.append(f"Confidence   : {rec.confidence:.2f}%")
            lines.append(f"Quality      : {rec.trade_quality}")
            lines.append(f"Risk         : {rec.risk_level}")
            lines.append("")

            if rec.entry_price is not None:
                lines.append(f"Entry        : {rec.entry_price:.2f}")

            if rec.stop_loss is not None:
                lines.append(f"Stop Loss    : {rec.stop_loss:.2f}")

            if rec.target_price is not None:
                lines.append(f"Target       : {rec.target_price:.2f}")

            if rec.risk_reward_ratio is not None:
                lines.append(f"RR Ratio     : {rec.risk_reward_ratio:.2f}")

            lines.append("")

            if rec.positive_signals:
                lines.append("Positive Signals")

                for signal in rec.positive_signals:
                    lines.append(f"  ✓ {signal}")

                lines.append("")

            if rec.negative_signals:
                lines.append("Negative Signals")

                for signal in rec.negative_signals:
                    lines.append(f"  ✗ {signal}")

                lines.append("")

            if rec.warnings:
                lines.append("Warnings")

                for warning in rec.warnings:
                    lines.append(f"  ⚠ {warning}")

                lines.append("")

            lines.append(f"Summary : {rec.summary}")
            lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)