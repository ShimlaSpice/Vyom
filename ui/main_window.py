"""Primary desktop window for VYOM Trader AI."""

from __future__ import annotations

from dataclasses import dataclass

try:
    import pyqtgraph as pg
except Exception:  # pragma: no cover - optional dependency fallback
    pg = None

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.container import ApplicationContainer


@dataclass(slots=True)
class TickerData:
    """Top ticker summary shown in the header."""

    label: str
    value: str
    change: str
    positive: bool


@dataclass(slots=True)
class OpportunityData:
    """Ranked opportunity entry."""

    rank: int
    symbol: str
    name: str
    score: int
    action: str
    action_positive: bool


@dataclass(slots=True)
class AlertData:
    """Recent market alert entry."""

    symbol: str
    reason: str
    time: str
    severity: str


@dataclass(slots=True)
class HeadlineData:
    """News headline entry."""

    title: str
    source: str
    time: str


class GlowLogo(QWidget):
    """Render a neon-style circular brand mark."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(66, 66)

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        center = rect.center()

        outer = QRadialGradient(center, 33)
        outer.setColorAt(0.0, QColor("#1a4cff"))
        outer.setColorAt(0.35, QColor("#1d2358"))
        outer.setColorAt(0.7, QColor("#080c19"))
        outer.setColorAt(1.0, QColor("#050914"))
        painter.setBrush(outer)
        painter.setPen(QPen(QColor("#2f6bff"), 2))
        painter.drawEllipse(rect.adjusted(4, 4, -4, -4))

        glow = QRadialGradient(center, 24)
        glow.setColorAt(0.0, QColor(120, 102, 255, 230))
        glow.setColorAt(0.55, QColor(35, 72, 255, 110))
        glow.setColorAt(1.0, QColor(20, 40, 100, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect.adjusted(10, 10, -10, -10))

        path = QPainterPath()
        path.moveTo(center.x() - 12, center.y() - 12)
        path.lineTo(center.x() - 2, center.y() + 12)
        path.lineTo(center.x() + 2, center.y() + 12)
        path.lineTo(center.x() + 12, center.y() - 12)
        path.lineTo(center.x() + 5, center.y() - 12)
        path.lineTo(center.x(), center.y() + 2)
        path.lineTo(center.x() - 5, center.y() - 12)
        path.closeSubpath()
        painter.setBrush(QColor("#7ce1ff"))
        painter.setPen(QPen(QColor("#8a67ff"), 2))
        painter.drawPath(path)


class GaugeWidget(QWidget):
    """Circular mood gauge with central score."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value = 86
        self._label = "BULLISH"
        self._subtitle = "Strong Buying Interest"
        self.setMinimumSize(160, 160)

    def set_value(self, value: int, label: str, subtitle: str) -> None:
        self._value = max(0, min(100, value))
        self._label = label
        self._subtitle = subtitle
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(12, 12, -12, -12)
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2

        painter.setPen(QPen(QColor(45, 55, 74), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, int(radius), int(radius))

        span = 360 * (self._value / 100.0)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor("#7fffd0"))
        gradient.setColorAt(1.0, QColor("#2ad2d6"))
        painter.setPen(QPen(gradient, 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(QRectF(rect), 90 * 16, -span * 16)

        painter.setPen(QColor("#eef4ff"))
        painter.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        painter.drawText(QRectF(rect), Qt.AlignmentFlag.AlignCenter, str(self._value))

        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        painter.setPen(QColor("#52f0a2"))
        bottom_rect = QRectF(rect.left(), rect.center().y() + 12, rect.width(), 20)
        painter.drawText(bottom_rect, Qt.AlignmentFlag.AlignHCenter, self._label)

        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Normal))
        painter.setPen(QColor("#8190a8"))
        subtitle_rect = QRectF(rect.left(), rect.center().y() + 30, rect.width(), 18)
        painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignHCenter, self._subtitle)


class SparklineWidget(QWidget):
    """Small sparkline used inside compact cards."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._values: list[float] = []
        self._line_color = QColor("#4df8a2")
        self.setMinimumHeight(72)

    def set_values(self, values: list[float], line_color: str = "#4df8a2") -> None:
        self._values = values[:]
        self._line_color = QColor(line_color)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        if len(self._values) < 2:
            return

        values = self._values
        min_value = min(values)
        max_value = max(values)
        span = max(1e-6, max_value - min_value)
        margin = 8.0
        width = self.width() - margin * 2
        height = self.height() - margin * 2

        points = []
        for index, value in enumerate(values):
            x = margin + (index / (len(values) - 1)) * width
            y = margin + height - ((value - min_value) / span) * height
            points.append(QPointF(x, y))

        path = QPainterPath(points[0])
        for point in points[1:]:
            path.lineTo(point)

        fill_path = QPainterPath(path)
        fill_path.lineTo(points[-1].x(), self.height() - margin)
        fill_path.lineTo(points[0].x(), self.height() - margin)
        fill_path.closeSubpath()

        fill = QLinearGradient(0, margin, 0, self.height() - margin)
        base = QColor(self._line_color)
        fill.setColorAt(0.0, QColor(base.red(), base.green(), base.blue(), 80))
        fill.setColorAt(1.0, QColor(base.red(), base.green(), base.blue(), 0))
        painter.setBrush(fill)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(fill_path)

        painter.setPen(QPen(self._line_color, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPath(path)


class AIBadgeWidget(QWidget):
    """Glow-style AI orb used in the summary card."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(92, 156)

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = self.rect().center()
        outer = QRadialGradient(center, 42)
        outer.setColorAt(0.0, QColor(62, 194, 255, 175))
        outer.setColorAt(0.36, QColor(20, 112, 205, 110))
        outer.setColorAt(0.6, QColor(14, 35, 68, 70))
        outer.setColorAt(1.0, QColor(8, 14, 22, 0))
        painter.setBrush(outer)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, 40, 40)

        core = QRadialGradient(center, 24)
        core.setColorAt(0.0, QColor("#4cf8ff"))
        core.setColorAt(0.45, QColor("#3a4cf8"))
        core.setColorAt(1.0, QColor("#11182f"))
        painter.setBrush(core)
        painter.setPen(QPen(QColor("#2ce8ff"), 2))
        painter.drawEllipse(center, 24, 24)

        painter.setPen(QPen(QColor("#7af2ff"), 1.2))
        for i in range(3):
            radius = 18 + i * 7
            painter.drawEllipse(center, radius, radius)

        path = QPainterPath()
        path.moveTo(center.x() - 11, center.y() - 9)
        path.lineTo(center.x() - 4, center.y() + 6)
        path.lineTo(center.x() + 0, center.y() - 2)
        path.lineTo(center.x() + 4, center.y() + 6)
        path.lineTo(center.x() + 11, center.y() - 9)
        painter.setPen(QPen(QColor("#c5f2ff"), 2.6))
        painter.drawPath(path)

        painter.setPen(QColor("#35e7ff"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 28, self.width(), 38), Qt.AlignmentFlag.AlignHCenter, "AI")

        spark = QPainterPath()
        spark.moveTo(18, 112)
        spark.cubicTo(26, 106, 29, 100, 34, 104)
        spark.cubicTo(41, 110, 43, 98, 50, 95)
        spark.cubicTo(57, 92, 61, 103, 67, 98)
        spark.cubicTo(74, 93, 78, 87, 84, 90)
        painter.setPen(QPen(QColor("#20ef8c"), 1.6))
        painter.drawPath(spark)


class PaletteButton(QPushButton):
    """Pill-style tab button used in the market overview header."""

    def __init__(self, text: str, active: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("NavPill")
        self.setCheckable(True)
        self.setChecked(active)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(48, 28)


class SidebarButton(QPushButton):
    """Navigation item used in the left rail."""

    def __init__(self, text: str, glyph: str, active: bool = False, badge: str | None = None) -> None:
        super().__init__()
        self._text_label: QLabel | None = None
        self._badge_label: QLabel | None = None
        self._glyph_label: QLabel | None = None
        self._layout: QHBoxLayout | None = None
        self.setCheckable(True)
        self.setChecked(active)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(39)
        self.setProperty("sidebarButton", True)

        layout = QHBoxLayout(self)
        self._layout = layout
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        icon = QLabel(glyph, self)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(22, 22)
        icon.setObjectName("SideGlyph")
        layout.addWidget(icon)
        self._glyph_label = icon

        label = QLabel(text, self)
        label.setObjectName("SideLabel")
        layout.addWidget(label)
        self._text_label = label
        layout.addStretch(1)

        if badge is not None:
            badge_label = QLabel(badge, self)
            badge_label.setObjectName("NavBadge")
            badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge_label.setFixedSize(24, 18)
            badge_label.setStyleSheet(
                "background: #ff4d4d; color: white; border-radius: 9px; font-size: 10px; font-weight: 700;"
            )
            layout.addWidget(badge_label)
            self._badge_label = badge_label

    def set_collapsed(self, collapsed: bool) -> None:
        """Toggle between the full-width and icon-only rail states."""

        if self._text_label is not None:
            self._text_label.setVisible(not collapsed)
        if self._badge_label is not None:
            self._badge_label.setVisible(not collapsed)
        if self._glyph_label is not None:
            self._glyph_label.setFixedSize(24 if collapsed else 22, 24 if collapsed else 22)
        if self._layout is not None:
            self._layout.setContentsMargins(10 if collapsed else 12, 0, 10 if collapsed else 12, 0)
            self._layout.setSpacing(0 if collapsed else 10)


class MainWindow(QMainWindow):
    """Compose the screenshot-matched premium dashboard."""

    def __init__(self, container: ApplicationContainer) -> None:
        super().__init__()
        self._container = container
        self._sidebar_frame: QFrame | None = None
        self._sidebar_brand_name: QLabel | None = None
        self._sidebar_brand_tag: QLabel | None = None
        self._sidebar_footer_label: QLabel | None = None
        self._sidebar_footer_version: QLabel | None = None
        self._sidebar_buttons: list[SidebarButton] = []
        self._top_ticker_labels: dict[str, dict[str, QLabel]] = {}
        self._overview_plot = None
        self._overview_curve = None
        self._overview_baseline = None
        self._overview_fill = None
        self._mood_gauge = GaugeWidget()
        self._mood_sparkline = SparklineWidget()
        self._sidebar_expanded_width = 224
        self._sidebar_collapsed_width = 78
        self._sidebar_collapsed = False
        self._sidebar_idle_timer = QTimer(self)
        self._sidebar_idle_timer.setSingleShot(True)
        self._sidebar_idle_timer.setInterval(5000)
        self._sidebar_idle_timer.timeout.connect(self._collapse_sidebar)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(15_000)
        self._refresh_timer.timeout.connect(self.refresh_dashboard)

        self._ticker_data = [
            TickerData("NIFTY 50", "25,321.45", "+1.22%", True),
            TickerData("BANKNIFTY", "57,042.80", "-0.41%", False),
            TickerData("INDIA VIX", "11.20", "-3.12%", False),
            TickerData("SENSEX", "83,098.38", "+1.18%", True),
        ]
        self._opportunities = [
            OpportunityData(1, "BEL", "Bharat Electronics", 94, "BUY", True),
            OpportunityData(2, "HAL", "Hindustan Aeronautics", 92, "BUY", True),
            OpportunityData(3, "TATAMOTORS", "Tata Motors", 90, "BUY", True),
            OpportunityData(4, "ICICI BANK", "ICICI Bank Ltd.", 88, "WATCH", False),
            OpportunityData(5, "TCS", "Tata Consultancy", 87, "WATCH", False),
        ]
        self._alerts = [
            AlertData("BEL", "Resistance Broken", "09:31 AM", "sell"),
            AlertData("HAL", "High Volume Spike", "09:29 AM", "info"),
            AlertData("TCS", "RSI Crossed Above 60", "09:27 AM", "warn"),
            AlertData("ICICI BANK", "Target 1 Achieved", "09:24 AM", "info"),
            AlertData("RELIANCE", "News Alert", "09:21 AM", "warn"),
        ]
        self._headlines = [
            HeadlineData("RBI keeps repo rate unchanged at 6.50%", "Economic Times", "09:30 AM"),
            HeadlineData("BEL secures 22,463 Cr defence contract", "Moneycontrol", "09:22 AM"),
            HeadlineData("India's manufacturing PMI rises to 58.7", "LiveMint", "09:18 AM"),
            HeadlineData("Global markets rally as US inflation eases", "Reuters", "09:15 AM"),
        ]
        self._sectors = [
            ("IT", 1.85),
            ("AUTO", 1.45),
            ("DEFENCE", 1.28),
            ("BANKING", -0.25),
            ("PHARMA", -0.35),
            ("METAL", -0.65),
            ("REALTY", -0.85),
        ]
        self._heatmap_tiles = [
            ("RELIANCE", +1.35),
            ("HDFCBANK", -0.15),
            ("TCS", +1.05),
            ("ICICIBANK", +0.65),
            ("INFY", +1.45),
            ("HINDUNILVR", +0.35),
            ("SBIN", -0.25),
            ("BHARTIARTL", +0.75),
            ("LT", +0.55),
            ("AXISBANK", -0.35),
            ("BAJFINANCE", +0.75),
            ("ITC", +0.25),
            ("ASIANPAINT", +0.45),
            ("SUNPHARMA", -0.15),
        ]

        self._build_ui()
        self.refresh_dashboard()
        self._refresh_timer.start()

    def _build_ui(self) -> None:
        self.setWindowTitle(f"{self._container.settings.application.name} | Dashboard")
        self.resize(1535, 720)
        self.setMinimumSize(1400, 700)

        central = QWidget(self)
        central.setObjectName("rootWindow")
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(12)

        sidebar = self._build_sidebar()
        content = self._build_content_area()

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)
        central.installEventFilter(self)
        sidebar.installEventFilter(self)

        self.setStyleSheet(
            """
            QWidget#rootWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #040812, stop:0.4 #07101b, stop:1 #060912);
                color: #eef4ff;
                font-family: Segoe UI, Arial, sans-serif;
            }
            QFrame#Sidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(9, 14, 24, 0.98), stop:1 rgba(7, 11, 18, 0.98));
                border: 1px solid rgba(76, 101, 133, 0.18);
                border-radius: 20px;
            }
            QFrame#TopBar, QFrame#Card {
                background: rgba(9, 14, 24, 0.88);
                border: 1px solid rgba(85, 114, 152, 0.18);
                border-radius: 14px;
            }
            QFrame#MiniCard {
                background: rgba(11, 17, 29, 0.96);
                border: 1px solid rgba(81, 109, 142, 0.18);
                border-radius: 12px;
            }
            QLabel#BrandTitle {
                font-size: 26px;
                font-weight: 700;
                color: #f2f5ff;
                letter-spacing: 0.6px;
            }
            QLabel#BrandSubtitle {
                font-size: 11px;
                color: #a4b1c8;
                line-height: 1.2;
            }
            QLabel#TopTickerName {
                font-size: 12px;
                color: #aab6cb;
                letter-spacing: 0.2px;
            }
            QLabel#TopTickerValue {
                font-size: 15px;
                color: #f2f6ff;
                font-weight: 600;
            }
            QLabel#TopTickerChange {
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton[property="sidebarButton"]:checked QLabel#SideLabel {
                color: #56e5ff;
            }
            QPushButton[property="sidebarButton"]:checked QLabel#SideGlyph {
                color: #56e5ff;
            }
            QPushButton[property="sidebarButton"] {
                text-align: left;
                background: transparent;
                border: none;
                border-radius: 12px;
                color: #c3cde1;
            }
            QPushButton[property="sidebarButton"]:hover {
                background: rgba(83, 160, 198, 0.10);
            }
            QPushButton[property="sidebarButton"]:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(18, 144, 184, 0.20), stop:1 rgba(26, 96, 159, 0.25));
                border: 1px solid rgba(82, 205, 255, 0.14);
            }
            QLabel#SectionTitle {
                color: #f5f8ff;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0.3px;
            }
            QLabel#MutedLabel {
                color: #8f9db3;
                font-size: 11px;
            }
            QLabel#Chip {
                color: #d7e1f1;
                background: rgba(22, 29, 41, 0.98);
                border: 1px solid rgba(82, 106, 137, 0.20);
                border-radius: 10px;
                padding: 7px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#ChipGreen {
                color: #2def84;
                background: rgba(22, 37, 27, 0.98);
                border: 1px solid rgba(58, 179, 102, 0.30);
                border-radius: 10px;
                padding: 7px 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QLabel#ChipRed {
                color: #ff5c5c;
                background: rgba(39, 19, 23, 0.98);
                border: 1px solid rgba(202, 72, 72, 0.30);
                border-radius: 10px;
                padding: 7px 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QLabel#ChipOrange {
                color: #f7b047;
                background: rgba(47, 35, 18, 0.98);
                border: 1px solid rgba(204, 140, 54, 0.30);
                border-radius: 10px;
                padding: 7px 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QLineEdit#SearchBar {
                background: rgba(11, 16, 26, 0.96);
                color: #e9f0ff;
                border: 1px solid rgba(84, 110, 140, 0.30);
                border-radius: 14px;
                padding: 11px 16px;
                font-size: 13px;
            }
            QLineEdit#SearchBar:focus {
                border: 1px solid rgba(103, 240, 255, 0.55);
            }
            QPushButton#NavPill {
                background: rgba(17, 23, 35, 0.90);
                color: #c6d0e3;
                border: 1px solid rgba(82, 109, 140, 0.20);
                border-radius: 10px;
                padding: 5px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton#NavPill:checked {
                background: rgba(35, 193, 221, 0.18);
                border: 1px solid rgba(53, 224, 255, 0.45);
                color: #64efff;
            }
            QToolButton#TopIcon {
                background: rgba(12, 18, 28, 0.95);
                border: 1px solid rgba(84, 112, 144, 0.22);
                border-radius: 18px;
                color: #dce5f7;
                font-size: 18px;
                font-weight: 600;
            }
            QToolButton#TopIcon:hover {
                background: rgba(31, 44, 65, 0.95);
            }
            QLabel#BodyText {
                color: #dce8ff;
                font-size: 11px;
            }
            QLabel#BodyTiny {
                color: #a7b5ca;
                font-size: 10px;
            }
            QLabel#SideGlyph {
                color: #8fb6ff;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#SideLabel {
                color: #edf3ff;
                font-size: 13px;
            }
            QLabel#SidebarAppName {
                color: #f2f5ff;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 0.8px;
            }
            QLabel#SidebarAppTag {
                color: #9daec7;
                font-size: 10px;
                letter-spacing: 0.3px;
            }
            """
        )
        self._expand_sidebar()
        self._restart_sidebar_timer()

    def _build_sidebar(self) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName("Sidebar")
        frame.setFixedWidth(self._sidebar_expanded_width)
        self._sidebar_frame = frame
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        brand = QVBoxLayout()
        brand.setContentsMargins(0, 0, 0, 0)
        brand.setSpacing(8)
        brand.addWidget(GlowLogo(frame), 0, Qt.AlignmentFlag.AlignHCenter)

        app_name = QLabel("VYOM TRADER AI", frame)
        app_name.setObjectName("SidebarAppName")
        app_name.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        app_name.setWordWrap(True)
        app_name.setMinimumHeight(22)
        self._sidebar_brand_name = app_name
        brand.addWidget(app_name)

        app_tag = QLabel("Intraday trading intelligence platform", frame)
        app_tag.setObjectName("SidebarAppTag")
        app_tag.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        app_tag.setWordWrap(True)
        app_tag.setMinimumHeight(16)
        self._sidebar_brand_tag = app_tag
        brand.addWidget(app_tag)
        layout.addLayout(brand)

        layout.addSpacing(4)

        nav_items = [
            ("Dashboard", "⌂", True, None),
            ("Live Market", "∿", False, None),
            ("AI Scanner", "◌", False, None),
            ("Top Opportunities", "★", False, None),
            ("Chart Analysis", "⌇", False, None),
            ("Watchlist", "▣", False, None),
            ("Portfolio", "▤", False, None),
            ("News Center", "◫", False, None),
            ("Alerts Center", "🔔", False, "12"),
            ("Risk Dashboard", "⚑", False, None),
            ("Analytics", "◔", False, None),
            ("Settings", "⚙", False, None),
            ("Logs", "◌", False, None),
            ("Help & Support", "?", False, None),
        ]

        for text, glyph, active, badge in nav_items:
            glyph = {
                "Dashboard": "D",
                "Live Market": "M",
                "AI Scanner": "AI",
                "Top Opportunities": "O",
                "Chart Analysis": "C",
                "Watchlist": "W",
                "Portfolio": "P",
                "News Center": "N",
                "Alerts Center": "A",
                "Risk Dashboard": "R",
                "Analytics": "Y",
                "Settings": "S",
                "Logs": "L",
                "Help & Support": "H",
            }.get(text, glyph)
            button = SidebarButton(text, glyph, active=active, badge=badge)
            button.setObjectName("SidebarButton")
            button.installEventFilter(self)
            button.clicked.connect(lambda _checked=False, b=button: self._set_active_nav(b))
            self._sidebar_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch(1)

        footer = QVBoxLayout()
        footer.setSpacing(3)
        footer_label = QLabel("VYOM TRADER AI", frame)
        footer_label.setObjectName("BodyText")
        footer_version = QLabel(f"v{self._container.settings.application.version}", frame)
        footer_version.setObjectName("BodyTiny")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        footer_version.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._sidebar_footer_label = footer_label
        self._sidebar_footer_version = footer_version
        footer.addWidget(footer_label)
        footer.addWidget(footer_version)
        layout.addLayout(footer)

        return frame

    def _build_content_area(self) -> QWidget:
        area = QWidget(self)
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_top_bar())
        layout.addWidget(self._build_dashboard_grid(), 1)
        return area

    def _build_top_bar(self) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName("TopBar")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        brand = QVBoxLayout()
        title = QLabel("VYOM TRADER AI", frame)
        title.setObjectName("BrandTitle")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        subtitle = QLabel("AI-POWERED INTRADAY TRADING INTELLIGENCE PLATFORM", frame)
        subtitle.setObjectName("BrandSubtitle")
        subtitle.setWordWrap(True)
        subtitle.setMaximumWidth(420)
        subtitle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        brand.addWidget(title)
        brand.addWidget(subtitle)
        layout.addLayout(brand, 1)

        search = QLineEdit(frame)
        search.setObjectName("SearchBar")
        search.setPlaceholderText("Search stocks, news, sectors...")
        search.setFixedWidth(300)
        layout.addWidget(search)

        layout.addSpacing(10)

        for ticker in self._ticker_data:
            layout.addWidget(self._build_ticker_card(ticker))

        bell = self._build_icon_button("🔔", badge="12")
        gear = self._build_icon_button("⚙")
        layout.addWidget(bell)
        layout.addWidget(gear)

        return frame

    def _build_ticker_card(self, ticker: TickerData) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName("MiniCard")
        frame.setFixedWidth(126)
        frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(1)

        name = QLabel(ticker.label, frame)
        name.setObjectName("TopTickerName")
        value = QLabel(ticker.value, frame)
        value.setObjectName("TopTickerValue")
        change = QLabel(ticker.change, frame)
        change.setObjectName("TopTickerChange")
        change.setStyleSheet(f"color: {'#31eb7e' if ticker.positive else '#ff4a4a'};")

        layout.addWidget(name)
        layout.addWidget(value)
        layout.addWidget(change)
        self._top_ticker_labels[ticker.label] = {"value": value, "change": change}
        return frame

    def _build_icon_button(self, glyph: str, badge: str | None = None) -> QWidget:
        container = QFrame(self)
        container.setFixedSize(42, 42)
        container.setObjectName("MiniCard")
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        button = QToolButton(container)
        button.setObjectName("TopIcon")
        button.setText(glyph)
        button.setFixedSize(40, 40)
        layout.addWidget(button, 0, 0, Qt.AlignmentFlag.AlignCenter)

        if badge is not None:
            badge_label = QLabel(badge, container)
            badge_label.setObjectName("navBadge")
            badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge_label.setFixedSize(22, 18)
            badge_label.move(24, 0)
            badge_label.raise_()
        return container

    def _build_dashboard_grid(self) -> QWidget:
        grid_host = QWidget(self)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(2, 1.35)
        grid.setColumnStretch(3, 1.55)
        grid.setColumnStretch(4, 1.45)
        grid.setRowStretch(0, 4)
        grid.setRowStretch(1, 3)

        overview = self._build_market_overview_card()
        mood_stack = self._build_mood_stack()
        opportunities = self._build_opportunities_card()
        alerts = self._build_alerts_card()
        sector = self._build_sector_card()
        heatmap = self._build_heatmap_card()
        ai_summary = self._build_ai_summary_card()
        news = self._build_news_card()

        grid.addWidget(overview, 0, 0, 1, 2)
        grid.addWidget(mood_stack, 0, 2, 1, 1)
        grid.addWidget(opportunities, 0, 3, 1, 1)
        grid.addWidget(alerts, 0, 4, 1, 1)
        grid.addWidget(sector, 1, 0, 1, 1)
        grid.addWidget(heatmap, 1, 1, 1, 2)
        grid.addWidget(ai_summary, 1, 3, 1, 1)
        grid.addWidget(news, 1, 4, 1, 1)

        return grid_host

    def _card(self, title: str, subtitle: str | None = None, *, min_height: int = 0) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame(self)
        frame.setObjectName("Card")
        if min_height > 0:
            frame.setMinimumHeight(min_height)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title_label = QLabel(title, frame)
        title_label.setObjectName("SectionTitle")
        title_row.addWidget(title_label)
        title_row.addStretch(1)
        if subtitle:
            sub = QLabel(subtitle, frame)
            sub.setObjectName("MutedLabel")
            title_row.addWidget(sub)
        layout.addLayout(title_row)
        return frame, layout

    def _build_market_overview_card(self) -> QFrame:
        frame, layout = self._card("MARKET OVERVIEW", min_height=320)

        tabs = QHBoxLayout()
        tabs.setSpacing(6)
        for index, label in enumerate(["1D", "5D", "1M", "YTD", "1Y", "5Y"]):
            tabs.addWidget(PaletteButton(label, active=(label == "YTD"), parent=frame))
        tabs.addStretch(1)
        layout.addLayout(tabs)

        top_cards = QHBoxLayout()
        top_cards.setSpacing(10)
        card_specs = [
            ("NIFTY 50", "25,321.45", "+1.22%", True),
            ("BANKNIFTY", "57,042.80", "-0.41%", False),
            ("FINNIFTY", "25,321.45", "+0.85%", True),
            ("MIDCPNIFTY", "12,856.10", "+1.05%", True),
        ]
        for name, value, change, positive in card_specs:
            top_cards.addWidget(self._build_mini_stats_card(name, value, change, positive))
        layout.addLayout(top_cards)

        if pg is not None:
            self._overview_plot = pg.PlotWidget(frame)
            self._overview_plot.setBackground((0, 0, 0, 0))
            self._overview_plot.showGrid(x=True, y=True, alpha=0.14)
            self._overview_plot.setMenuEnabled(False)
            self._overview_plot.setMouseEnabled(x=False, y=False)
            self._overview_plot.setFixedHeight(195)
            self._overview_plot.setContentsMargins(0, 0, 0, 0)
            self._overview_plot.getPlotItem().hideButtons()
            self._overview_plot.getPlotItem().setContentsMargins(0, 0, 0, 0)
            self._overview_plot.getPlotItem().showAxis("left", True)
            self._overview_plot.getPlotItem().showAxis("bottom", True)
            self._overview_plot.getAxis("left").setTextPen(QColor("#94a3bc"))
            self._overview_plot.getAxis("bottom").setTextPen(QColor("#94a3bc"))
            self._overview_plot.getAxis("left").setPen(QColor(50, 60, 85, 120))
            self._overview_plot.getAxis("bottom").setPen(QColor(50, 60, 85, 120))
            self._overview_plot.getAxis("left").setStyle(tickFont=QFont("Segoe UI", 8))
            self._overview_plot.getAxis("bottom").setStyle(tickFont=QFont("Segoe UI", 8))
            self._overview_plot.setYRange(24950, 25500)
            self._overview_plot.setXRange(0, 40)
            self._overview_curve = self._overview_plot.plot(pen=pg.mkPen("#35e7ff", width=2))
            self._overview_baseline = self._overview_plot.plot(pen=pg.mkPen(color=(0, 0, 0, 0)))
            self._overview_fill = pg.FillBetweenItem(
                self._overview_curve,
                self._overview_baseline,
                brush=pg.mkBrush(20, 160, 190, 55),
            )
            self._overview_plot.addItem(self._overview_fill)
            layout.addWidget(self._overview_plot)
        else:
            fallback = QLabel("Charting unavailable", frame)
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setMinimumHeight(190)
            layout.addWidget(fallback)

        return frame

    def _build_mini_stats_card(self, name: str, value: str, change: str, positive: bool) -> QFrame:
        card = QFrame(self)
        card.setObjectName("MiniCard")
        card.setFixedHeight(86)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(2)

        label = QLabel(name, card)
        label.setObjectName("TopTickerName")
        val = QLabel(value, card)
        val.setObjectName("TopTickerValue")
        ch = QLabel(change, card)
        ch.setObjectName("TopTickerChange")
        ch.setStyleSheet(f"color: {'#34ef77' if positive else '#ff4d4d'};")
        layout.addWidget(label)
        layout.addWidget(val)
        layout.addStretch(1)
        layout.addWidget(ch)
        return card

    def _build_mood_stack(self) -> QFrame:
        stack = QFrame(self)
        stack_layout = QVBoxLayout(stack)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        stack_layout.setSpacing(12)
        stack_layout.addWidget(self._build_market_mood_card())
        stack_layout.addWidget(self._build_market_breadth_card())
        return stack

    def _build_market_mood_card(self) -> QFrame:
        frame, layout = self._card("MARKET MOOD", min_height=228)
        layout.setSpacing(6)
        layout.addWidget(self._mood_gauge, 0, Qt.AlignmentFlag.AlignHCenter)
        self._mood_gauge.set_value(86, "BULLISH", "Strong Buying Interest")
        self._mood_sparkline.set_values(
            [12, 18, 16, 19, 22, 21, 24, 27, 25, 29, 33, 31, 35, 38, 36, 39],
            "#35e7ff",
        )
        layout.addWidget(self._mood_sparkline)
        return frame

    def _build_market_breadth_card(self) -> QFrame:
        frame, layout = self._card("MARKET BREADTH", min_height=116)

        stats = QHBoxLayout()
        stats.setSpacing(10)
        stats.addWidget(self._breadth_stat("ADVANCE", "1,632", "#35e7ff"))
        stats.addWidget(self._breadth_stat("DECLINE", "918", "#ff4d4d"))
        stats.addWidget(self._breadth_stat("UNCHANGED", "124", "#94a3bc"))
        layout.addLayout(stats)

        bar = QFrame(frame)
        bar.setFixedHeight(12)
        bar.setStyleSheet(
            "background: rgba(20, 27, 41, 1); border: 1px solid rgba(70, 85, 110, 0.2); border-radius: 6px;"
        )
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)

        green = QFrame(bar)
        green.setStyleSheet("background: #2fc061; border-top-left-radius: 5px; border-bottom-left-radius: 5px;")
        red = QFrame(bar)
        red.setStyleSheet("background: #aa3232; border-top-right-radius: 5px; border-bottom-right-radius: 5px;")
        green.setFixedWidth(63)
        red.setFixedWidth(35)
        bar_layout.addWidget(green)
        bar_layout.addWidget(red)
        layout.addWidget(bar)

        footer = QHBoxLayout()
        pos = QLabel("63%", frame)
        pos.setStyleSheet("color: #35e7ff; font-size: 11px; font-weight: 700;")
        neg = QLabel("35%", frame)
        neg.setStyleSheet("color: #ff4d4d; font-size: 11px; font-weight: 700;")
        footer.addWidget(pos)
        footer.addStretch(1)
        footer.addWidget(neg)
        layout.addLayout(footer)
        return frame

    def _breadth_stat(self, title: str, value: str, color: str) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        title_label = QLabel(title, widget)
        title_label.setStyleSheet("color: #8fa0b8; font-size: 10px; font-weight: 600;")
        value_label = QLabel(value, widget)
        value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: 700;")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return widget

    def _build_opportunities_card(self) -> QFrame:
        frame, layout = self._card("TOP 5 OPPORTUNITIES", min_height=320)
        for entry in self._opportunities:
            layout.addWidget(self._opportunity_row(entry))

        footer = QLabel("View All Opportunities  →", frame)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #55dfff; font-size: 11px; font-weight: 600; padding-top: 2px;")
        layout.addStretch(1)
        layout.addWidget(footer)
        return frame

    def _opportunity_row(self, entry: OpportunityData) -> QWidget:
        row = QFrame(self)
        row.setObjectName("MiniCard")
        row.setFixedHeight(50)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        rank = QLabel(str(entry.rank), row)
        rank.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rank.setFixedSize(22, 22)
        rank.setStyleSheet(
            "background: rgba(61, 91, 222, 1); color: white; font-size: 11px; font-weight: 700; border-radius: 11px;"
        )
        layout.addWidget(rank)

        text = QVBoxLayout()
        symbol = QLabel(entry.symbol, row)
        symbol.setStyleSheet("color: #f4f8ff; font-size: 11px; font-weight: 700;")
        name = QLabel(entry.name, row)
        name.setStyleSheet("color: #7e8da6; font-size: 9px;")
        text.addWidget(symbol)
        text.addWidget(name)
        layout.addLayout(text, 1)

        score = QLabel(str(entry.score), row)
        score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score.setFixedSize(22, 22)
        score.setStyleSheet(
            "background: rgba(24, 123, 58, 0.9); color: #9fffd0; font-size: 10px; font-weight: 700; border-radius: 6px;"
        )
        layout.addWidget(score)

        action = QLabel(entry.action, row)
        action.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action.setFixedSize(40, 22)
        action.setObjectName("ChipGreen" if entry.action_positive else "ChipOrange")
        layout.addWidget(action)
        return row

    def _build_alerts_card(self) -> QFrame:
        frame, layout = self._card("RECENT ALERTS", min_height=320)
        for alert in self._alerts:
            layout.addWidget(self._alert_row(alert))
        footer = QLabel("View All Alerts  →", frame)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #55dfff; font-size: 11px; font-weight: 600; padding-top: 2px;")
        layout.addStretch(1)
        layout.addWidget(footer)
        return frame

    def _alert_row(self, alert: AlertData) -> QWidget:
        row = QFrame(self)
        row.setObjectName("MiniCard")
        row.setFixedHeight(49)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        icon = QLabel("▲" if alert.severity == "sell" else "↗" if alert.severity == "info" else "△", row)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(22, 22)
        if alert.severity == "sell":
            icon.setStyleSheet("background: rgba(203, 72, 72, 0.25); color: #ff5b5b; border-radius: 11px;")
        elif alert.severity == "warn":
            icon.setStyleSheet("background: rgba(195, 170, 72, 0.24); color: #ffe86e; border-radius: 11px;")
        else:
            icon.setStyleSheet("background: rgba(53, 223, 255, 0.16); color: #35e7ff; border-radius: 11px;")
        layout.addWidget(icon)

        text = QVBoxLayout()
        symbol = QLabel(alert.symbol, row)
        symbol.setStyleSheet("color: #f4f8ff; font-size: 11px; font-weight: 700;")
        reason = QLabel(alert.reason, row)
        reason.setStyleSheet("color: #7e8da6; font-size: 9px;")
        text.addWidget(symbol)
        text.addWidget(reason)
        layout.addLayout(text, 1)

        time = QLabel(alert.time, row)
        time.setStyleSheet("color: #8ea0b8; font-size: 9px;")
        layout.addWidget(time)
        return row

    def _build_sector_card(self) -> QFrame:
        frame, layout = self._card("SECTOR PERFORMANCE", min_height=268)
        tabs = QHBoxLayout()
        tabs.setSpacing(6)
        for label in ["1D", "1W", "1M", "1Y"]:
            tabs.addWidget(PaletteButton(label, active=(label == "1D"), parent=frame))
        tabs.addStretch(1)
        layout.addLayout(tabs)

        for name, value in self._sectors:
            layout.addWidget(self._sector_row(name, value))
        return frame

    def _sector_row(self, name: str, value: float) -> QWidget:
        row = QWidget(self)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        label = QLabel(name, row)
        label.setStyleSheet("color: #dce4f1; font-size: 10px;")
        label.setFixedWidth(58)
        h.addWidget(label)

        bar_bg = QFrame(row)
        bar_bg.setFixedHeight(6)
        bar_bg.setStyleSheet("background: rgba(20, 28, 40, 0.95); border-radius: 3px;")
        bar_bg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        inner = QFrame(bar_bg)
        inner.setFixedHeight(6)
        inner.setStyleSheet(
            f"background: {'#27ba5f' if value >= 0 else '#c53e3e'}; border-radius: 3px;"
        )
        inner.setFixedWidth(max(18, min(120, int(abs(value) * 34 + 40))))
        bar_layout = QHBoxLayout(bar_bg)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.addWidget(inner)
        bar_layout.addStretch(1)
        h.addWidget(bar_bg, 1)

        val = QLabel(f"{value:+.2f}%", row)
        val.setStyleSheet(
            f"color: {'#31ef86' if value >= 0 else '#ff4e4e'}; font-size: 10px; font-weight: 600;"
        )
        val.setFixedWidth(56)
        h.addWidget(val)
        return row

    def _build_heatmap_card(self) -> QFrame:
        frame, layout = self._card("HEATMAP", min_height=268)
        selector = QHBoxLayout()
        selector.setSpacing(8)
        selector.addWidget(PaletteButton("NIFTY 50", active=True, parent=frame))
        selector.addWidget(PaletteButton("BANKNIFTY", parent=frame))
        selector.addWidget(PaletteButton("FINNIFTY", parent=frame))
        selector.addStretch(1)
        layout.addLayout(selector)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        cols = 4
        for index, (symbol, value) in enumerate(self._heatmap_tiles):
            r = index // cols
            c = index % cols
            grid.addWidget(self._heatmap_tile(symbol, value), r, c)

        layout.addLayout(grid)
        return frame

    def _heatmap_tile(self, symbol: str, value: float) -> QFrame:
        tile = QFrame(self)
        tile.setMinimumSize(78, 62)
        tile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tile.setObjectName("HeatmapTile")
        tile.setStyleSheet(
            "QFrame#HeatmapTile { border-radius: 8px; }"
            + (
                f"QFrame#HeatmapTile {{ background: rgba(35, 114, 55, {0.22 + min(0.45, abs(value) / 2):.2f}); border: 1px solid rgba(73, 171, 100, 0.18); }}"
                if value >= 0
                else f"QFrame#HeatmapTile {{ background: rgba(112, 36, 46, {0.22 + min(0.45, abs(value) / 2):.2f}); border: 1px solid rgba(189, 73, 73, 0.18); }}"
            )
        )
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(0)
        symbol_label = QLabel(symbol, tile)
        symbol_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        symbol_label.setStyleSheet("color: #f8fbff; font-size: 8px; font-weight: 700;")
        value_label = QLabel(f"{value:+.2f}%", tile)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(
            f"color: {'#bfffd8' if value >= 0 else '#ffc2c2'}; font-size: 8px; font-weight: 600;"
        )
        layout.addWidget(symbol_label)
        layout.addWidget(value_label)
        return tile

    def _build_ai_summary_card(self) -> QFrame:
        frame, layout = self._card("AI SUMMARY", min_height=268)
        body = QVBoxLayout()
        body.setSpacing(10)
        bullets = [
            "Market is bullish with strong buying in IT, Auto and Defence sectors.",
            "Nifty holding above 25,200 key support.",
            "FII buying observed in Auto and Capital Goods.",
            "Top opportunity today: BEL, HAL, TATAMOTORS",
        ]
        for index, line in enumerate(bullets):
            body.addWidget(self._summary_bullet(line, index == len(bullets) - 1))
        body.addStretch(1)
        layout.addLayout(body)
        return frame

    def _ai_orb_widget(self) -> QFrame:
        return AIBadgeWidget(self)

    def _summary_bullet(self, text: str, highlight: bool = False) -> QWidget:
        row = QWidget(self)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        dot = QLabel("◉" if highlight else "•", row)
        dot.setStyleSheet("color: #35e7ff; font-size: 10px;")
        h.addWidget(dot)

        label = QLabel(text, row)
        label.setWordWrap(True)
        label.setStyleSheet(
            "color: #c9d3e3; font-size: 10px; line-height: 1.3;"
            + ("font-weight: 700; color: #f0b430;" if highlight else "")
        )
        h.addWidget(label, 1)
        return row

    def _build_news_card(self) -> QFrame:
        frame, layout = self._card("NEWS HEADLINES", min_height=268)
        for headline in self._headlines:
            layout.addWidget(self._news_row(headline))
        return frame

    def _news_row(self, headline: HeadlineData) -> QWidget:
        row = QWidget(self)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        bullet = QLabel("◆", row)
        bullet.setStyleSheet("color: #f0a93a; font-size: 10px;")
        h.addWidget(bullet)

        text = QVBoxLayout()
        title = QLabel(headline.title, row)
        title.setWordWrap(True)
        title.setStyleSheet("color: #eef4ff; font-size: 10px; font-weight: 600;")
        source = QLabel(headline.source, row)
        source.setStyleSheet("color: #8e9eb6; font-size: 9px;")
        text.addWidget(title)
        text.addWidget(source)
        h.addLayout(text, 1)

        time = QLabel(headline.time, row)
        time.setStyleSheet("color: #92a3ba; font-size: 9px;")
        h.addWidget(time)
        return row

    def _set_active_nav(self, selected: SidebarButton) -> None:
        for button in self._sidebar_buttons:
            button.setChecked(button is selected)
        self._expand_sidebar()
        self._restart_sidebar_timer()

    def _expand_sidebar(self) -> None:
        self._sidebar_collapsed = False
        if self._sidebar_frame is not None:
            self._sidebar_frame.setFixedWidth(self._sidebar_expanded_width)
        if self._sidebar_brand_name is not None:
            self._sidebar_brand_name.setVisible(True)
        if self._sidebar_brand_tag is not None:
            self._sidebar_brand_tag.setVisible(True)
        if self._sidebar_footer_label is not None:
            self._sidebar_footer_label.setVisible(True)
        if self._sidebar_footer_version is not None:
            self._sidebar_footer_version.setVisible(True)
        for button in self._sidebar_buttons:
            button.set_collapsed(False)

    def _collapse_sidebar(self) -> None:
        self._sidebar_collapsed = True
        if self._sidebar_frame is not None:
            self._sidebar_frame.setFixedWidth(self._sidebar_collapsed_width)
        if self._sidebar_brand_name is not None:
            self._sidebar_brand_name.setVisible(False)
        if self._sidebar_brand_tag is not None:
            self._sidebar_brand_tag.setVisible(False)
        if self._sidebar_footer_label is not None:
            self._sidebar_footer_label.setVisible(False)
        if self._sidebar_footer_version is not None:
            self._sidebar_footer_version.setVisible(False)
        for button in self._sidebar_buttons:
            button.set_collapsed(True)

    def _restart_sidebar_timer(self) -> None:
        self._sidebar_idle_timer.start()

    def eventFilter(self, obj, event):  # noqa: N802 - Qt naming
        if obj is self._sidebar_frame or obj is self.centralWidget() or obj in self._sidebar_buttons:
            if event.type() == QEvent.Type.Enter:
                self._expand_sidebar()
                self._restart_sidebar_timer()
            elif event.type() == QEvent.Type.MouseButtonPress:
                self._expand_sidebar()
                self._restart_sidebar_timer()
        return super().eventFilter(obj, event)

    def refresh_dashboard(self) -> None:
        """Refresh the live header chart and text widgets."""

        if self._overview_curve is not None and pg is not None:
            series = self._container.market_service.build_price_series("NIFTY 50", points=60)
            self._overview_curve.setData(series)
            if self._overview_baseline is not None:
                self._overview_baseline.setData([min(series) - 18] * len(series))
            self._overview_plot.setYRange(min(series) - 8, max(series) + 8)
        self._mood_sparkline.set_values(
            [12, 18, 16, 19, 22, 21, 24, 27, 25, 29, 33, 31, 35, 38, 36, 39],
            "#35e7ff",
        )
