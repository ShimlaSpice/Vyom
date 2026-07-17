from __future__ import annotations

import customtkinter as ctk


class AIPanel(ctk.CTkFrame):

    def __init__(self, master):

        super().__init__(
            master,
            corner_radius=10,
        )

        self._build()

    def _build(self):

        ctk.CTkLabel(
            self,
            text="AI Insights",
            font=("Segoe UI", 18, "bold"),
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 10),
        )

        self.insights = ctk.CTkTextbox(
            self,
            height=220,
        )

        self.insights.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15),
        )

        self.insights.insert(
            "end",
            "Waiting for AI Engine...\n"
        )

        self.insights.configure(state="disabled")