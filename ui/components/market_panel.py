from __future__ import annotations

import customtkinter as ctk


class MarketPanel(ctk.CTkFrame):

    def __init__(self, master):

        super().__init__(
            master,
            corner_radius=10,
        )

        self._build()

    def _build(self):

        ctk.CTkLabel(
            self,
            text="Market Overview",
            font=("Segoe UI", 18, "bold"),
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 10),
        )

        rows = [
            ("NIFTY 50", "--"),
            ("BANK NIFTY", "--"),
            ("INDIA VIX", "--"),
            ("USD/INR", "--"),
            ("GOLD", "--"),
            ("CRUDE", "--"),
        ]

        for title, value in rows:

            row = ctk.CTkFrame(
                self,
                fg_color="transparent",
            )

            row.pack(
                fill="x",
                padx=15,
                pady=5,
            )

            ctk.CTkLabel(
                row,
                text=title,
                font=("Segoe UI", 14),
            ).pack(
                side="left",
            )

            ctk.CTkLabel(
                row,
                text=value,
                font=("Segoe UI", 14, "bold"),
            ).pack(
                side="right",
            )