"""Regression tests for the 0.2 desktop dashboard slice."""

from __future__ import annotations

import json
from pathlib import Path

from config import ConfigManager
from core.database import DatabaseManager
from market.service import MarketService


def _write_settings(tmp_path: Path) -> Path:
    """Create an isolated settings file for tests."""

    data_directory = tmp_path / "data"
    log_directory = tmp_path / "logs"
    asset_directory = tmp_path / "assets"
    database_path = data_directory / "vyom_trader_ai.db"

    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "application": {
                    "name": "VYOM Trader AI",
                    "version": "0.2.0",
                    "environment": "test",
                },
                "paths": {
                    "data_directory": str(data_directory),
                    "log_directory": str(log_directory),
                    "asset_directory": str(asset_directory),
                },
                "logging": {
                    "level": "INFO",
                    "rotation": "10 MB",
                    "retention": "14 days",
                    "file_name": "vyom_trader_ai.log",
                    "backtrace": False,
                    "diagnose": False,
                },
                "database": {
                    "path": str(database_path),
                    "echo": False,
                    "pool_pre_ping": True,
                },
                "scheduler": {
                    "timezone": "Asia/Kolkata",
                    "coalesce": True,
                    "max_instances": 1,
                    "misfire_grace_time": 60,
                },
                "cache": {
                    "default_ttl_seconds": 300,
                    "max_items": 100,
                },
            }
        ),
        encoding="utf-8",
    )
    return settings_path


def test_config_manager_loads_0_2_settings(tmp_path: Path) -> None:
    """Ensure the version metadata and paths load correctly."""

    settings = ConfigManager(_write_settings(tmp_path)).settings

    assert settings.application.version == "0.2.0"
    assert settings.paths.data_directory == tmp_path / "data"
    assert settings.database.path == tmp_path / "data" / "vyom_trader_ai.db"


def test_database_watchlist_round_trip(tmp_path: Path) -> None:
    """Ensure watchlist entries can be persisted and removed."""

    settings = ConfigManager(_write_settings(tmp_path)).settings
    database = DatabaseManager(settings)

    database.initialize()
    try:
        database.upsert_watchlist_item("reliance", name="Reliance Industries", notes="Core holding")
        items = database.list_watchlist_items()

        assert [item.symbol for item in items] == ["RELIANCE"]
        assert items[0].name == "Reliance Industries"
        assert database.delete_watchlist_item("RELIANCE") is True
        assert database.list_watchlist_items() == []
    finally:
        database.dispose()


def test_market_service_produces_ranked_scan_results() -> None:
    """Ensure the scanner and chart helpers return usable data."""

    service = MarketService()
    request = service.build_universe_request("NSE", "Intraday")

    results = service.scan(request, limit=5)
    series = service.build_price_series("RELIANCE", points=24)

    assert len(results) == 5
    assert results == sorted(results, key=lambda item: item.score, reverse=True)
    assert series[0] != series[-1]
    assert len(series) == 24
