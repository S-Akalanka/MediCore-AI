from decimal import Decimal

from nawaloka.agents import fallback, interpreter, orchestrator, router
from nawaloka.agents.messages import Interpretation, RouterMessage
from nawaloka.engine.engine import EngineResult

ROWS = [{"department": "Cardiology", "revenue": Decimal("1200.50")}, {"department": "Oncology", "revenue": Decimal("900")}]


def test_validate_chart_accepts_valid_spec():
    chart = {"type": "bar", "x": "department", "y": "revenue", "title": "Revenue"}
    spec = interpreter.validate_chart(chart, ROWS)
    assert spec is not None and spec.chart_type == "bar" and spec.x_label == "department"


def test_validate_chart_rejects_unknown_column():
    assert interpreter.validate_chart({"type": "bar", "x": "nope", "y": "revenue"}, ROWS) is None


def test_validate_chart_rejects_non_numeric_y():
    assert interpreter.validate_chart({"type": "bar", "x": "department", "y": "department"}, ROWS) is None


def test_validate_chart_rejects_unknown_type():
    assert interpreter.validate_chart({"type": "radar", "x": "department", "y": "revenue"}, ROWS) is None


def _patch(monkeypatch, intent="data_query", sql_result=None, sql_error=None):
    monkeypatch.setattr(router, "classify", lambda q: RouterMessage(intent, "reply"))

    def fake_ask(question):
        if sql_error:
            raise sql_error
        return sql_result

    monkeypatch.setattr(orchestrator, "ask", fake_ask)
    monkeypatch.setattr(interpreter, "interpret", lambda q, s, r: Interpretation("Cardiology leads."))
    monkeypatch.setattr(fallback, "respond", lambda q: "fallback reply")
    orchestrator._graph = None


def test_successful_query_reaches_interpreter(monkeypatch):
    _patch(monkeypatch, sql_result=EngineResult("ok", "q", sql="SELECT 1", rows=ROWS))
    result = orchestrator.run_pipeline("q")
    assert result.status == "ok" and result.answer == "Cardiology leads."
    assert [s.agent for s in result.steps] == ["router", "sql_generator", "interpreter"]


def test_destructive_intent_is_blocked_before_sql(monkeypatch):
    _patch(monkeypatch, intent="destructive")
    result = orchestrator.run_pipeline("delete everything")
    assert result.status == "blocked"
    assert "sql_generator" not in [s.agent for s in result.steps]


def test_failed_sql_goes_to_fallback(monkeypatch):
    _patch(monkeypatch, sql_result=EngineResult("failed", "q", message="bad"))
    result = orchestrator.run_pipeline("q")
    assert result.status == "fallback" and result.answer == "fallback reply"


def test_agent_crash_goes_to_fallback(monkeypatch):
    _patch(monkeypatch, sql_error=RuntimeError("boom"))
    result = orchestrator.run_pipeline("q")
    assert result.status == "fallback"
    assert any(s.status == "error" for s in result.steps)


def test_destructive_answer_uses_standard_message(monkeypatch):
    from nawaloka.engine.engine import BLOCKED_MESSAGE

    _patch(monkeypatch, intent="destructive")
    assert orchestrator.run_pipeline("delete everything").answer == BLOCKED_MESSAGE


def test_history_adds_contextualizer_step(monkeypatch):
    from nawaloka.agents import contextualizer

    _patch(monkeypatch, sql_result=EngineResult("ok", "q", sql="SELECT 1", rows=ROWS))
    seen = {}

    def fake_rewrite(question, history):
        seen["history"] = history
        return "standalone question"

    monkeypatch.setattr(contextualizer, "rewrite", fake_rewrite)
    history = [{"question": "earlier", "sql": "SELECT 1", "answer": "a"}]
    result = orchestrator.run_pipeline("and last year?", history)
    assert [s.agent for s in result.steps][0] == "contextualizer"
    assert seen["history"] == history
    assert result.question == "and last year?"
