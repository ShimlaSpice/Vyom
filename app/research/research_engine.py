from __future__ import annotations

from app.news.news_engine import NewsEngine
from app.research.models import ResearchReport


class ResearchEngine:
    """
    Central research engine.

    Every future module must use this class.

    Scanner
    Dashboard
    AI Analyst
    Validation
    Alerts
    """

    def __init__(self) -> None:
        self.news_engine = NewsEngine()

    def build_report(
        self,
        recommendation,
    ) -> ResearchReport:

        news = self.news_engine.get_news(
            recommendation.symbol,
        )

        report = ResearchReport(
            symbol=recommendation.symbol,

            overall_score=recommendation.total_score,

            technical_score=recommendation.technical_score,

            momentum_score=recommendation.momentum_score,

            volume_score=recommendation.volume_score,

            market_score=recommendation.market_score,

            news_score=recommendation.news_score,

            action=recommendation.action,

            confidence=recommendation.confidence,

            risk=recommendation.risk_level,

            entry=recommendation.entry_price or 0,

            stop_loss=recommendation.stop_loss or 0,

            target=recommendation.target_price or 0,

            positive_points=recommendation.positive_signals,

            negative_points=recommendation.negative_signals,

            news=news,

            ai_summary=recommendation.summary,
        )

        return report