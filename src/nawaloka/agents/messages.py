from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RouterMessage:
    intent: str
    message: str = ""


@dataclass
class ChartSpec:
    chart_type: str
    x: str
    y: str
    title: str
    x_label: str
    y_label: str


@dataclass
class Interpretation:
    summary: str
    chart: ChartSpec | None = None


@dataclass
class StepTrace:
    agent: str
    status: str
    duration_ms: float
    detail: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class PipelineResult:
    question: str
    status: str
    answer: str = ""
    intent: str = ""
    sql: str = ""
    rows: list[dict[str, Any]] = field(default_factory=list)
    interpretation: Interpretation | None = None
    steps: list[StepTrace] = field(default_factory=list)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
