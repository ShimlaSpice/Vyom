from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class NewsItem:
    source: str
    title: str
    url: str = ""
    published_at: datetime | None = None
    sentiment: float = 0.0
    impact: float = 0.0
    summary: str = ""
    tags: list[str] = field(default_factory=list)