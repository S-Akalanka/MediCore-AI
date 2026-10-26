from decimal import Decimal
from typing import Any

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure

from nawaloka.agents.messages import ChartSpec

MAX_CATEGORIES = 20
MAX_PIE_SLICES = 8


def _frame(spec: ChartSpec, rows: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)[[spec.x, spec.y]].copy()
    frame[spec.y] = frame[spec.y].map(lambda v: float(v) if isinstance(v, Decimal) else v)
    return frame


def _group_small_slices(frame: pd.DataFrame, spec: ChartSpec) -> pd.DataFrame:
    if len(frame) <= MAX_PIE_SLICES:
        return frame
    ordered = frame.sort_values(spec.y, ascending=False)
    top = ordered.head(MAX_PIE_SLICES - 1)
    other = pd.DataFrame({spec.x: ["Other"], spec.y: [ordered[spec.y].iloc[MAX_PIE_SLICES - 1 :].sum()]})
    return pd.concat([top, other], ignore_index=True)


def build_figure(spec: ChartSpec, rows: list[dict[str, Any]]) -> Figure:
    """Render a bar, line or pie figure from a chart spec and result rows."""
    frame = _frame(spec, rows)
    labels = {spec.x: spec.x_label, spec.y: spec.y_label}
    if spec.chart_type == "line":
        figure = px.line(frame.sort_values(spec.x), x=spec.x, y=spec.y, title=spec.title, labels=labels, markers=True)
    elif spec.chart_type == "pie":
        figure = px.pie(_group_small_slices(frame, spec), names=spec.x, values=spec.y, title=spec.title)
    else:
        top = frame.sort_values(spec.y, ascending=False).head(MAX_CATEGORIES)
        figure = px.bar(top, x=spec.x, y=spec.y, title=spec.title, labels=labels)
    figure.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    return figure
