import json
from datetime import datetime

from loguru import logger

from nawaloka import config
from nawaloka.agents.messages import PipelineResult

SAMPLE_ROWS = 5


def save_trace(result: PipelineResult) -> None:
    """Write a JSON trace of one pipeline run to the traces folder."""
    if not config.SAVE_TRACES:
        return
    data = result.to_dict()
    data["total_rows"] = len(result.rows)
    data["rows"] = result.rows[:SAMPLE_ROWS]
    data["input_tokens"] = sum(s.input_tokens for s in result.steps)
    data["output_tokens"] = sum(s.output_tokens for s in result.steps)
    data["timestamp"] = datetime.now().isoformat(timespec="seconds")
    try:
        config.TRACES_DIR.mkdir(parents=True, exist_ok=True)
        name = f"{datetime.now():%Y%m%d_%H%M%S_%f}_{result.status}.json"
        (config.TRACES_DIR / name).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    except OSError as exc:
        logger.warning("Could not save trace: {}", exc)
