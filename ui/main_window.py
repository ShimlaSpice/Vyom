"""Primary desktop window for VYOM Trader AI."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QStatusBar, QVBoxLayout, QWidget

from core.container import ApplicationContainer


class MainWindow(QMainWindow):
    """Compose the initial professional shell of the desktop application."""

    def __init__(self, container: ApplicationContainer) -> None:
        super().__init__()
        self._container = container
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the window chrome and static application shell."""

        self.setWindowTitle(self._container.settings.application.name)
        self.resize(1280, 800)
        self.setStatusBar(QStatusBar(self))

        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(self._container.settings.application.name, central_widget)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title.setStyleSheet("font-size: 28px; font-weight: 700;")

        subtitle = QLabel(
            "Architecture scaffold for a production desktop trading platform.",
            central_widget,
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 14px; color: #666666;")

        status = QLabel(
            f"Environment: {self._container.settings.application.environment} | "
            f"Database: {self._container.settings.database.path}",
            central_widget,
        )
        status.setWordWrap(True)
        status.setStyleSheet("font-size: 12px; color: #888888;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(status)
        layout.addStretch(1)

        self.setCentralWidget(central_widget)
