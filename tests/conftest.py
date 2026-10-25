import pytest

from nawaloka import config


@pytest.fixture(autouse=True)
def no_trace_files(monkeypatch):
    monkeypatch.setattr(config, "SAVE_TRACES", False)
