from __future__ import annotations

import customtkinter as ctk
from datetime import datetime


class Header(ctk.CTkFrame):

    def __init__(self, master):

        super().__init__(
            master,
            height=70,
            corner_radius=10,
        )

        self.grid_columnconfigure(0, weight=1)

        self._build()

    def _build(self):

        ctk.CTkLabel(
            self,
            text="VYOM AI Trading Dashboard",
            font=("Segoe UI", 24, "bold"),
        ).grid(
            row=0,
            column=0,
            padx=20,
            pady=18,
            sticky="w",
        )

        self.time_label = ctk.CTkLabel(
            self,
            text=datetime.now().strftime("%d %b %Y  |  %H:%M:%S"),
            font=("Segoe UI", 14),
        )

        self.time_label.grid(
            row=0,
            column=1,
            padx=20,
            sticky="e",
        )

        self.after(1000, self._update_clock)

    def _update_clock(self):

        self.time_label.configure(
            text=datetime.now().strftime("%d %b %Y  |  %H:%M:%S")
        )

        self.after(1000, self._update_clock)