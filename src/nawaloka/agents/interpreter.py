import json
import re
from decimal import Decimal
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from nawaloka.agents.messages import ChartSpec, Interpretation
from nawaloka.llm import get_llm

CHART_TYPES = {"bar", "line", "pie"}
PROMPT_ROWS = 30

SYSTEM_PROMPT = """You are a hospital data analyst. You receive a question, the SQL that was run, and the result rows.

Respond with JSON only:
{"summary": "<2 to 3 plain English sentences>",
 "chart": {"type": "bar|line|pie|none", "x": "<column>", "y": "<numeric column>", "title": "<title>", "x_label": "<label>", "y_label": "<label>"}}

Rules:
- The summary must cite specific values from the rows. Never invent numbers.
- Use bar for rankings and comparisons, line for trends over time, pie for shares of a whole with at most 8 categories.
- x and y must be exact column names from the result. Use type none if a chart does not make sense.
"""


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)


def validate_chart(chart: dict | None, rows: list[dict[str, Any]]) -> ChartSpec | None:
    """Turn a raw chart dict into a ChartSpec, or None if it does not fit the data."""
    if not chart or not rows:
        return None
    chart_type = str(chart.get("type", "")).lower()
    x, y = chart.get("x"), chart.get("y")
    if chart_type not in CHART_TYPES or x not in rows[0] or y not in rows[0]:
        return None
    if not any(_is_number(row[y]) for row in rows):
        return None
    return ChartSpec(
        chart_type=chart_type,
        x=x,
        y=y,
        title=chart.get("title") or f"{y} by {x}",
        x_label=chart.get("x_label") or x,
        y_label=chart.get("y_label") or y,
    )


def _plain_summary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "The query ran but returned no rows."
    return f"The query returned {len(rows)} rows."


def interpret(question: str, sql: str, rows: list[dict[str, Any]]) -> Interpretation:
    """Summarise result rows in plain English and propose a chart."""
    if not rows:
        return Interpretation(summary=_plain_summary(rows))
    payload = (
        f"Question: {question}\nSQL: {sql}\nTotal rows: {len(rows)}\n"
        f"Rows (first {PROMPT_ROWS}): {json.dumps(rows[:PROMPT_ROWS], default=str)}"
    )
    try:
        response = get_llm("interpreter", json_mode=True).invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=payload)]
        )
        match = re.search(r"\{.*\}", str(response.content), re.DOTALL)
        data = json.loads(match.group(0)) if match else {}
        summary = (data.get("summary") or "").strip() or _plain_summary(rows)
        return Interpretation(summary=summary, chart=validate_chart(data.get("chart"), rows))
    except Exception as exc:
        logger.warning("Interpreter failed, using plain summary: {}", exc)
        return Interpretation(summary=_plain_summary(rows))
