import json
from types import SimpleNamespace

from nawaloka import config, traces
from nawaloka.agents.messages import PipelineResult, StepTrace
from nawaloka.observability import UsageCallback, start_usage, stop_usage


def _response(input_tokens, output_tokens):
    message = SimpleNamespace(usage_metadata={"input_tokens": input_tokens, "output_tokens": output_tokens})
    return SimpleNamespace(generations=[[SimpleNamespace(message=message)]])


def test_usage_callback_accumulates_tokens():
    token = start_usage()
    callback = UsageCallback()
    callback.on_llm_end(_response(10, 4))
    callback.on_llm_end(_response(5, 1))
    usage = stop_usage(token)
    assert usage == {"input": 15, "output": 5}


def test_usage_is_ignored_without_active_counter():
    UsageCallback().on_llm_end(_response(10, 4))


def test_save_trace_writes_json(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "TRACES_DIR", tmp_path)
    monkeypatch.setattr(config, "SAVE_TRACES", True)
    result = PipelineResult(
        "q",
        "ok",
        answer="a",
        rows=[{"n": i} for i in range(20)],
        steps=[StepTrace("router", "ok", 12.5, "", 10, 2), StepTrace("interpreter", "ok", 30.0, "", 20, 8)],
    )
    traces.save_trace(result)
    files = list(tmp_path.glob("*_ok.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data["total_rows"] == 20 and len(data["rows"]) == 5
    assert data["input_tokens"] == 30 and data["output_tokens"] == 10


def test_save_trace_respects_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "TRACES_DIR", tmp_path)
    monkeypatch.setattr(config, "SAVE_TRACES", False)
    traces.save_trace(PipelineResult("q", "ok"))
    assert list(tmp_path.iterdir()) == []
