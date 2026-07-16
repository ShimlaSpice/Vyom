from __future__ import annotations

import customtkinter as ctk


class Dashboard(ctk.CTk):

    def __init__(self) -> None:

        super().__init__()

        self.title("VYOM AI Trading System")
        self.geometry("1600x900")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()

        self._build_main_panel()

    def _build_sidebar(self):

        sidebar = ctk.CTkFrame(
            self,
            width=220,
        )

        sidebar.grid(
            row=0,
            column=0,
            sticky="ns",
        )

        ctk.CTkLabel(
            sidebar,
            text="VYOM",
            font=("Arial", 28, "bold"),
        ).pack(
            pady=(25, 10),
        )

        buttons = [
            "Dashboard",
            "Scanner",
            "Research",
            "Market",
            "News",
            "AI Analyst",
            "Validation",
            "Settings",
        ]

        for text in buttons:

            ctk.CTkButton(
                sidebar,
                text=text,
                width=180,
            ).pack(
                pady=8,
                padx=20,
            )

    def _build_main_panel(self):

        self.main = ctk.CTkFrame(self)

        self.main.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=15,
            pady=15,
        )

        ctk.CTkLabel(
            self.main,
            text="VYOM Dashboard",
            font=("Arial", 26, "bold"),
        ).pack(
            pady=20,
        )


if __name__ == "__main__":

    ctk.set_appearance_mode("dark")

    ctk.set_default_color_theme("blue")

    app = Dashboard()

    app.mainloop()