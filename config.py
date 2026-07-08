"""Central application configuration for VYOM Trader AI."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigurationError(RuntimeError):
    """Raised when the application configuration cannot be loaded."""


@dataclass(frozen=True)
class ApplicationConfig:
    """Application metadata and runtime mode settings."""

    name: str
    version: str
    environment: str


@dataclass(frozen=True)
class PathConfig:
    """Filesystem locations used by the application."""

    root: Path
    data_directory: Path
    log_directory: Path
    asset_directory: Path


@dataclass(frozen=True)
class LoggingConfig:
    """Logging runtime configuration."""

    level: str
    rotation: str
    retention: str
    file_name: str
    backtrace: bool
    diagnose: bool


@dataclass(frozen=True)
class DatabaseConfig:
    """Database runtime configuration."""

    path: Path
    echo: bool
    pool_pre_ping: bool


@dataclass(frozen=True)
class SchedulerJobDefaults:
    """Default scheduler behavior."""

    coalesce: bool
    max_instances: int
    misfire_grace_time: int


@dataclass(frozen=True)
class SchedulerConfig:
    """Scheduler runtime configuration."""

    timezone: str
    job_defaults: SchedulerJobDefaults


@dataclass(frozen=True)
class CacheConfig:
    """Application cache configuration."""

    default_ttl_seconds: int
    max_items: int


@dataclass(frozen=True)
class Settings:
    """Fully validated application settings."""

    application: ApplicationConfig
    paths: PathConfig
    logging: LoggingConfig
    database: DatabaseConfig
    scheduler: SchedulerConfig
    cache: CacheConfig


class ConfigManager:
    """Load and validate the application settings file.

    The manager keeps the JSON schema centralized and returns immutable typed
    dataclasses so the rest of the application can depend on a stable contract.
    """

    def __init__(self, settings_path: Path | str | None = None) -> None:
        self._project_root = Path(__file__).resolve().parent
        default_path = self._project_root / "settings.json"
        env_override = os.getenv("VYOM_TRADER_AI_SETTINGS_PATH")
        raw_path = settings_path or env_override or default_path
        self._settings_path = self._resolve_absolute_path(Path(raw_path))
        self._settings: Settings | None = None

    @property
    def settings_path(self) -> Path:
        """Return the resolved settings file path."""

        return self._settings_path

    @property
    def settings(self) -> Settings:
        """Return the cached settings, loading them lazily if required."""

        if self._settings is None:
            self._settings = self.load()
        return self._settings

    def load(self) -> Settings:
        """Load settings from disk and convert them into typed dataclasses."""

        try:
            with self._settings_path.open("r", encoding="utf-8") as handle:
                raw_settings = json.load(handle)
            if not isinstance(raw_settings, Mapping):
                raise ConfigurationError("settings.json must contain a JSON object")
            self._settings = self._build_settings(dict(raw_settings))
            return self._settings
        except FileNotFoundError as exc:
            raise ConfigurationError(
                f"Settings file not found: {self._settings_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise ConfigurationError(
                f"Invalid JSON in settings file: {self._settings_path}"
            ) from exc
        except OSError as exc:
            raise ConfigurationError(
                f"Unable to read settings file: {self._settings_path}"
            ) from exc

    def reload(self) -> Settings:
        """Force a fresh reload of the settings file."""

        self._settings = None
        self._settings = self.load()
        return self._settings

    def _build_settings(self, raw: dict[str, Any]) -> Settings:
        """Convert the raw JSON mapping into immutable settings objects."""

        application = raw.get("application", {})
        paths = raw.get("paths", {})
        logging = raw.get("logging", {})
        database = raw.get("database", {})
        scheduler = raw.get("scheduler", {})
        cache = raw.get("cache", {})

        data_directory = self._resolve_relative_to_root(paths.get("data_directory", "data"))
        log_directory = self._resolve_relative_to_root(paths.get("log_directory", "logs"))
        asset_directory = self._resolve_relative_to_root(paths.get("asset_directory", "assets"))
        database_path = self._resolve_relative_to_root(
            database.get("path", "data/vyom_trader_ai.db")
        )

        return Settings(
            application=ApplicationConfig(
                name=str(application.get("name", "VYOM Trader AI Web")),
                version=str(application.get("version", "0.1.0")),
                environment=str(application.get("environment", "development")),
            ),
            paths=PathConfig(
                root=self._project_root,
                data_directory=data_directory,
                log_directory=log_directory,
                asset_directory=asset_directory,
            ),
            logging=LoggingConfig(
                level=str(logging.get("level", "INFO")),
                rotation=str(logging.get("rotation", "10 MB")),
                retention=str(logging.get("retention", "14 days")),
                file_name=str(logging.get("file_name", "vyom_trader_ai.log")),
                backtrace=bool(logging.get("backtrace", False)),
                diagnose=bool(logging.get("diagnose", False)),
            ),
            database=DatabaseConfig(
                path=database_path,
                echo=bool(database.get("echo", False)),
                pool_pre_ping=bool(database.get("pool_pre_ping", True)),
            ),
            scheduler=SchedulerConfig(
                timezone=str(scheduler.get("timezone", "Asia/Kolkata")),
                job_defaults=SchedulerJobDefaults(
                    coalesce=bool(scheduler.get("coalesce", True)),
                    max_instances=int(scheduler.get("max_instances", 1)),
                    misfire_grace_time=int(scheduler.get("misfire_grace_time", 60)),
                ),
            ),
            cache=CacheConfig(
                default_ttl_seconds=int(cache.get("default_ttl_seconds", 300)),
                max_items=int(cache.get("max_items", 5000)),
            ),
        )

    def _resolve_absolute_path(self, value: Path) -> Path:
        """Normalize settings file paths to an absolute path."""

        return value if value.is_absolute() else (self._project_root / value).resolve()

    def _resolve_relative_to_root(self, value: str | Path) -> Path:
        """Resolve a project-relative path against the repository root."""

        path = Path(value)
        return path if path.is_absolute() else (self._project_root / path).resolve()
