from nawaloka.agents import contextualizer
from nawaloka.agents.contextualizer import Memory, rewrite


def test_memory_keeps_only_recent_turns():
    memory = Memory(max_turns=2)
    for i in range(4):
        memory.add(f"q{i}", "sql", "a")
    assert [t["question"] for t in memory.turns] == ["q2", "q3"]


def test_memory_clear():
    memory = Memory()
    memory.add("q", "sql", "a")
    memory.clear()
    assert memory.turns == []


def test_rewrite_without_history_skips_llm(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("LLM should not be called")

    monkeypatch.setattr(contextualizer, "get_llm", fail)
    assert rewrite("hello", []) == "hello"


def test_rewrite_falls_back_on_error(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("down")

    monkeypatch.setattr(contextualizer, "get_llm", fail)
    assert rewrite("and last year?", [{"question": "q", "sql": "s", "answer": "a"}]) == "and last year?"
