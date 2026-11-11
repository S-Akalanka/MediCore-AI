from decimal import Decimal

import pytest

from nawaloka.agents.messages import ChartSpec
from nawaloka.dashboard import service
from nawaloka.dashboard.charts import MAX_CATEGORIES, MAX_PIE_SLICES, build_figure
from nawaloka.dashboard.panels import PANELS


def test_dashboard_has_five_panels_with_date_filters():
    assert len(PANELS) == 5
    assert len({p.key for p in PANELS}) == 5
    for panel in PANELS:
        assert ":start" in panel.sql and ":end" in panel.sql


@pytest.mark.parametrize("chart_type", ["bar", "line", "pie"])
def test_figure_has_title_and_labels(chart_type):
    spec = ChartSpec(chart_type, "name", "value", "My Title", "Name Label", "Value Label")
    rows = [{"name": f"n{i}", "value": Decimal(i)} for i in range(1, 4)]
    figure = build_figure(spec, rows)
    assert figure.layout.title.text == "My Title"
    if chart_type != "pie":
        assert figure.layout.xaxis.title.text == "Name Label"
        assert figure.layout.yaxis.title.text == "Value Label"


def test_bar_chart_is_capped():
    spec = ChartSpec("bar", "name", "value", "t", "x", "y")
    rows = [{"name": f"n{i}", "value": i} for i in range(100)]
    assert len(build_figure(spec, rows).data[0].x) == MAX_CATEGORIES


def test_pie_groups_small_slices():
    spec = ChartSpec("pie", "name", "value", "t", "x", "y")
    rows = [{"name": f"n{i}", "value": i + 1} for i in range(20)]
    labels = list(build_figure(spec, rows).data[0].labels)
    assert len(labels) == MAX_PIE_SLICES and "Other" in labels


def test_load_panel_passes_date_range(monkeypatch):
    seen = {}

    def fake_run_query(sql, params=None):
        seen.update(params)
        return [{"month": "2024-01-01", "revenue": 10}]

    monkeypatch.setattr(service, "run_query", fake_run_query)
    result = service.load_panel(PANELS[0], "2024-01-01", "2024-02-01", with_insight=False)
    assert seen == {"start": "2024-01-01", "end": "2024-02-01"} and result.rows


def test_load_panel_handles_query_failure(monkeypatch):
    def boom(sql, params=None):
        raise RuntimeError("db down")

    monkeypatch.setattr(service, "run_query", boom)
    result = service.load_panel(PANELS[0], "2024-01-01", "2024-02-01")
    assert result.error and not result.rows


def test_plain_escapes_dollar_signs():
    from nawaloka.dashboard.format import plain

    assert plain("Revenue ($1.5M) and ($2M)") == "Revenue (\\$1.5M) and (\\$2M)"
