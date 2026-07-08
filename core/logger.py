"""Production logging configuration for VYOM Trader AI."""

from __future__ import annotations

import sys
from typing import Any

from loguru import logger

from config import Settings


class LoggerManager:
    """Configure log sinks and ensure the log directory exists."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._configured = False

    @property
    def logger(self) -> Any:
        """Expose the shared Loguru logger instance."""

        return logger

    def configure(self) -> None:
        """Install console and file sinks once per process."""

        if self._configured:
            return

        self._ensure_log_directory()
        logger.remove()
        logger.add(
            sys.stderr,
            level=self._settings.logging.level.upper(),
            backtrace=self._settings.logging.backtrace,
            diagnose=self._settings.logging.diagnose,
            enqueue=True,
        )
        logger.add(
            self._settings.paths.log_directory / self._settings.logging.file_name,
            level=self._settings.logging.level.upper(),
            rotation=self._settings.logging.rotation,
            retention=self._settings.logging.retention,
            compression="zip",
            enqueue=True,
            backtrace=self._settings.logging.backtrace,
            diagnose=self._settings.logging.diagnose,
        )
        self._configured = True
        logger.debug("Logging configured for {}", self._settings.application.name)

    def _ensure_log_directory(self) -> None:
        """Create the logging directory if it does not already exist."""

        self._settings.paths.log_directory.mkdir(parents=True, exist_ok=True)
