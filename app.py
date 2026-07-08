"""Application entry point for VYOM Trader AI."""\
#author susheel sahoo

from __future__ import annotations

import sys

from loguru import logger
from PySide6.QtWidgets import QApplication

from ai.engine import AIDecisionEngine
from config import ConfigManager
from core.cache import CacheManager
from core.container import ApplicationContainer
from core.database import DatabaseManager
from core.logger import LoggerManager
from core.scheduler import SchedulerManager
from market.service import MarketService
from news.service import NewsService
from ui.main_window import MainWindow


class TraderApplication:
    """Compose infrastructure and manage the Qt lifecycle."""

    def __init__(self, container: ApplicationContainer) -> None:
        self._container = container
        self._qt_app: QApplication | None = None
        self._main_window: MainWindow | None = None

    def run(self) -> int:
        """Start the application event loop."""

        self._bootstrap()
        self._qt_app = QApplication.instance() or QApplication(sys.argv)
        self._qt_app.setApplicationName(self._container.settings.application.name)
        self._qt_app.setApplicationVersion(self._container.settings.application.version)
        self._qt_app.setOrganizationName(self._container.settings.application.name)
        self._main_window = MainWindow(self._container)
        self._qt_app.aboutToQuit.connect(self.shutdown)
        self._main_window.show()
        return self._qt_app.exec()

    def shutdown(self) -> None:
        """Release application resources safely."""

        try:
            self._container.scheduler_manager.shutdown(wait=False)
        finally:
            self._container.database_manager.dispose()
            logger.info("Application shutdown completed")

    def _bootstrap(self) -> None:
        """Initialize infrastructure before the UI starts."""

        self._container.logger_manager.configure()
        self._container.database_manager.initialize()
        self._container.scheduler_manager.start()
        logger.info("Application bootstrap completed")


def build_container() -> ApplicationContainer:
    """Create the application's dependency graph."""

    config_manager = ConfigManager()
    settings = config_manager.settings
    logger_manager = LoggerManager(settings)
    database_manager = DatabaseManager(settings)
    scheduler_manager = SchedulerManager(settings)
    cache_manager = CacheManager(settings)
    market_service = MarketService()
    news_service = NewsService()
    ai_engine = AIDecisionEngine()

    return ApplicationContainer(
        settings=settings,
        config_manager=config_manager,
        logger_manager=logger_manager,
        database_manager=database_manager,
        scheduler_manager=scheduler_manager,
        cache_manager=cache_manager,
        market_service=market_service,
        news_service=news_service,
        ai_engine=ai_engine,
    )


def main() -> int:
    """Run the desktop application and return its exit code."""

    try:
        container = build_container()
        application = TraderApplication(container)
        return application.run()
    except Exception:
        logger.exception("VYOM Trader AI failed to start")
        return 1


if __name__ == "__main__":
    sys.exit(main())
