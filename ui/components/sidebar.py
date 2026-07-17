from __future__ import annotations

import customtkinter as ctk


class Sidebar(ctk.CTkFrame):

    def __init__(self, master):

        super().__init__(
            master,
            width=220,
            corner_radius=0,
        )

        self.grid_propagate(False)

        self._build()

    def _build(self):

        ctk.CTkLabel(
            self,
            text="VYOM",
            font=("Segoe UI", 28, "bold"),
        ).pack(
            pady=(30, 5),
        )

        ctk.CTkLabel(
            self,
            text="AI Trading System",
            font=("Segoe UI", 12),
        ).pack(
            pady=(0, 25),
        )

        menu = [
            "🏠 Dashboard",
            "📈 Scanner",
            "🧠 Research",
            "🌍 Market",
            "📰 News",
            "🤖 AI Analyst",
            "✔ Validation",
            "⚙ Settings",
        ]

        for item in menu:

            ctk.CTkButton(
                self,
                text=item,
                width=180,
                height=42,
                anchor="w",
            ).pack(
                padx=18,
                pady=6,
            )