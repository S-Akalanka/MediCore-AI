from dataclasses import dataclass, field
from datetime import date
from typing import Any

from loguru import logger

from nawaloka.agents.interpreter import interpret
from nawaloka.dashboard.panels import Panel
from nawaloka.db.client import run_query


@dataclass
class PanelResult:
    panel: Panel
    rows: list[dict[str, Any]] = field(default_factory=list)
    insight: str = ""
    error: str = ""


def get_date_bounds() -> tuple[date, date]:
    """Return the earliest and latest appointment dates in the data."""
    row = run_query("SELECT MIN(appointment_date) AS first, MAX(appointment_date) AS last FROM appointments")[0]
    return row["first"], row["last"]


def load_panel(panel: Panel, start: date, end: date, with_insight: bool = True) -> PanelResult:
    """Run a panel query for a date range and optionally add a plain English insight."""
    try:
        rows = run_query(panel.sql, {"start": start, "end": end})
    except Exception as exc:
        logger.error("Panel {} failed: {}", panel.key, exc)
        return PanelResult(panel, error="This panel could not be loaded.")
    if not rows:
        return PanelResult(panel, insight="No data for the selected dates.")
    insight = interpret(panel.question, panel.sql, rows).summary if with_insight else ""
    return PanelResult(panel, rows=rows, insight=insight)
