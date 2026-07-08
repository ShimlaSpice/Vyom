"""Scheduler lifecycle management using APScheduler."""

from __future__ import annotations

from collections.abc import Callable
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from config import Settings


class SchedulerManager:
    """Own the application scheduler lifecycle."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._scheduler = BackgroundScheduler(
            timezone=ZoneInfo(self._settings.scheduler.timezone),
            daemon=True,
            job_defaults={
                "coalesce": self._settings.scheduler.job_defaults.coalesce,
                "max_instances": self._settings.scheduler.job_defaults.max_instances,
                "misfire_grace_time": self._settings.scheduler.job_defaults.misfire_grace_time,
            },
        )

    @property
    def scheduler(self) -> BackgroundScheduler:
        """Expose the underlying scheduler for advanced integrations."""

        return self._scheduler

    def start(self) -> None:
        """Start the scheduler if it is not already running."""

        if self._scheduler.running:
            return
        self._scheduler.start()
        logger.debug("Scheduler started")

    def shutdown(self, wait: bool = True) -> None:
        """Shut down the scheduler safely."""

        if not self._scheduler.running:
            return
        self._scheduler.shutdown(wait=wait)
        logger.debug("Scheduler stopped")

    def add_interval_job(
        self,
        job_id: str,
        job_func: Callable[..., object],
        seconds: int,
        *,
        replace_existing: bool = True,
    ) -> None:
        """Register an interval job."""

        self._scheduler.add_job(
            job_func,
            trigger="interval",
            seconds=seconds,
            id=job_id,
            replace_existing=replace_existing,
        )

    def add_cron_job(
        self,
        job_id: str,
        job_func: Callable[..., object],
        *,
        replace_existing: bool = True,
        **cron_kwargs: object,
    ) -> None:
        """Register a cron-style job."""

        self._scheduler.add_job(
            job_func,
            trigger="cron",
            id=job_id,
            replace_existing=replace_existing,
            **cron_kwargs,
        )
