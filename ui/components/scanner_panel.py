from __future__ import annotations

import customtkinter as ctk

from app.research.models import ResearchReport


class ScannerPanel(ctk.CTkFrame):

    def __init__(self, master):

        super().__init__(
            master,
            corner_radius=10,
        )

        self._build()

    def _build(self):

        ctk.CTkLabel(
            self,
            text="Top Opportunities",
            font=("Segoe UI", 18, "bold"),
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 10),
        )

        self.table = ctk.CTkTextbox(
            self,
            width=700,
            height=450,
        )

        self.table.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15),
        )

        self.show_reports([])

    def show_reports(
        self,
        reports: list[ResearchReport],
    ) -> None:

        self.table.configure(state="normal")

        self.table.delete("1.0", "end")

        self.table.insert(
            "end",
            f"{'Rank':<5} {'Symbol':<12} {'Action':<10} {'Score':<8} {'Conf':<8}\n"
        )

        self.table.insert(
            "end",
            "-" * 55 + "\n"
        )

        if not reports:

            self.table.insert(
                "end",
                "\nWaiting for scanner...\n",
            )

        else:

            for index, report in enumerate(reports, start=1):

                self.table.insert(
                    "end",
                    f"{index:<5}"
                    f"{report.symbol:<12}"
                    f"{report.action:<10}"
                    f"{report.overall_score:<8.1f}"
                    f"{report.confidence:<8.1f}\n"
                )

        self.table.configure(state="disabled")