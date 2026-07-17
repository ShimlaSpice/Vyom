from __future__ import annotations

import customtkinter as ctk


class StatusBar(ctk.CTkFrame):

    def __init__(self, master):

        super().__init__(
            master,
            height=32,
            corner_radius=0,
        )

        self.grid_columnconfigure(0, weight=1)

        self.status = ctk.CTkLabel(
            self,
            text="VYOM Ready",
            anchor="w",
            font=("Segoe UI", 12),
        )

        self.status.grid(
            row=0,
            column=0,
            padx=12,
            pady=6,
            sticky="ew",
        )

    def set_status(self, text: str):

        self.status.configure(text=text)