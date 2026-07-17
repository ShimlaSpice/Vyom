"""Dependency container for the application."""

from __future__ import annotations

from dataclasses import dataclass

from ai.engine import AIDecisionEngine
from config import ConfigManager, Settings
from core.cache import CacheManager
from core.database import DatabaseManager
from core.logger import LoggerManager
from core.scheduler import SchedulerManager     
from market.service import MarketService
from news.service import NewsService


@dataclass(slots=True)
class ApplicationContainer:
    """Group infrastructure and domain services in one place."""

    settings: Settings
    config_manager: ConfigManager
    logger_manager: LoggerManager
    database_manager: DatabaseManager
    scheduler_manager: SchedulerManager
    cache_manager: CacheManager[object]
    market_service: MarketService
    news_service: NewsService
    ai_engine: AIDecisionEngine
