from __future__ import annotations

import customtkinter as ctk

from ui.components.sidebar import Sidebar
from ui.components.header import Header
from ui.components.market_panel import MarketPanel
from ui.components.scanner_panel import ScannerPanel
from ui.components.news_panel import NewsPanel
from ui.components.ai_panel import AIPanel
from ui.components.statusbar import StatusBar


class Dashboard(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title("VYOM AI Trading System")

        self.geometry("1700x950")

        ctk.set_appearance_mode("dark")

        self.grid_columnconfigure(1, weight=1)

        self.grid_rowconfigure(0, weight=1)

        self._build_layout()

    def _build_layout(self):

        self.sidebar = Sidebar(self)

        self.sidebar.grid(
            row=0,
            column=0,
            rowspan=2,
            sticky="ns",
        )

        content = ctk.CTkFrame(self)

        content.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=10,
            pady=10,
        )

        content.grid_columnconfigure(0, weight=2)

        content.grid_columnconfigure(1, weight=1)

        content.grid_rowconfigure(2, weight=1)

        header = Header(content)

        header.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 10),
        )

        market = MarketPanel(content)

        market.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 10),
            pady=(0, 10),
        )

        scanner = ScannerPanel(content)

        scanner.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=(0, 10),
        )

        news = NewsPanel(content)

        news.grid(
            row=1,
            column=1,
            sticky="nsew",
            pady=(0, 10),
        )

        ai = AIPanel(content)

        ai.grid(
            row=2,
            column=1,
            sticky="nsew",
        )

        status = StatusBar(self)

        status.grid(
            row=1,
            column=1,
            sticky="ew",
        )


if __name__ == "__main__":

    app = Dashboard()

    app.mainloop()