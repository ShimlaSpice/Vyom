from __future__ import annotations

from dataclasses import dataclass, field

from app.research.models import ResearchReport


@dataclass(slots=True)
class DashboardData:

    generated_at: str

    total_scanned: int

    buy_count: int

    watch_count: int

    reject_count: int

    top_opportunities: list[ResearchReport] = field(default_factory=list)

    market_summary: str = ""

    ai_summary: str = ""