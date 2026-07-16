from __future__ import annotations

import logging

from app.news.models import NewsItem

logger = logging.getLogger(__name__)


class NewsEngine:
    """
    VYOM News Intelligence Engine

    Future Sources

    - Yahoo Finance
    - Reuters
    - NSE
    - BSE
    - Moneycontrol
    - Economic Times
    """

    def get_news(
        self,
        symbol: str,
    ) -> list[NewsItem]:

        logger.info("Fetching news for %s", symbol)

        return []