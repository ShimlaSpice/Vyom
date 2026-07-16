from __future__ import annotations

from dataclasses import dataclass, field
from app.news.models import NewsItem


@dataclass(slots=True)
class ResearchReport:
    symbol: str

    company_name: str = ""
    sector: str = ""
    industry: str = ""

    current_price: float = 0.0
    market_cap: float = 0.0

    technical_score: float = 0.0
    momentum_score: float = 0.0
    volume_score: float = 0.0
    news_score: float = 0.0
    market_score: float = 0.0
    overall_score: float = 0.0

    action: str = ""
    confidence: float = 0.0
    risk: str = ""

    entry: float = 0.0
    stop_loss: float = 0.0
    target: float = 0.0

    positive_points: list[str] = field(default_factory=list)
    negative_points: list[str] = field(default_factory=list)

    news: list[NewsItem] = field(default_factory=list)

    ai_summary: str = ""
    