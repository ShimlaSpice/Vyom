from __future__ import annotations

from datetime import datetime

from app.dashboard.models import DashboardData
from app.research.models import ResearchReport


class DashboardDataProvider:

    def build(
        self,
        reports: list[ResearchReport],
    ) -> DashboardData:

        buy = sum(1 for r in reports if r.action == "BUY")
        watch = sum(1 for r in reports if r.action == "WATCH")
        reject = sum(1 for r in reports if r.action == "NO TRADE")

        reports.sort(
            key=lambda report: report.overall_score,
            reverse=True,
        )

        return DashboardData(
            generated_at=datetime.now().strftime("%d-%b-%Y %H:%M:%S"),

            total_scanned=len(reports),

            buy_count=buy,

            watch_count=watch,

            reject_count=reject,

            top_opportunities=reports[:10],

            market_summary="",

            ai_summary="",
        )