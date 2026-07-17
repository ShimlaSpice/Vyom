from __future__ import annotations

import customtkinter as ctk


class NewsPanel(ctk.CTkFrame):

    def __init__(self, master):

        super().__init__(
            master,
            corner_radius=10,
        )

        self._build()

    def _build(self):

        ctk.CTkLabel(
            self,
            text="Latest News",
            font=("Segoe UI", 18, "bold"),
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 10),
        )

        self.news = ctk.CTkTextbox(
            self,
            height=220,
        )

        self.news.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15),
        )

        self.news.insert(
            "end",
            "Waiting for News Engine...\n"
        )

        self.news.configure(state="disabled")