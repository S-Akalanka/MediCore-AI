import sys

from loguru import logger

from nawaloka.agents.orchestrator import run_pipeline
from nawaloka.log import setup_logging
from nawaloka.observability import flush

DEFAULT_QUESTIONS = [
    "How many patients are registered?",
    "What are the top 5 revenue-generating departments?",
    "Which doctors have the highest no-show rates?",
    "Show monthly admissions for the last 6 months",
    "What are the most common diagnoses?",
    "Break down payments by payment method",
    "How many appointments does each doctor have this year?",
    "DELETE all patients",
    "What is the capital of France?",
    "asdf qwerty zxcv",
]


def main() -> None:
    """Run questions through the multi-agent pipeline and print each step."""
    setup_logging()
    for question in sys.argv[1:] or DEFAULT_QUESTIONS:
        result = run_pipeline(question)
        logger.info("Question: {}", question)
        logger.info("Status: {} | Intent: {}", result.status, result.intent)
        if result.sql:
            logger.info("SQL: {}", result.sql)
        logger.info("Answer: {}", result.answer)
        if result.interpretation and result.interpretation.chart:
            logger.info("Chart: {}", result.interpretation.chart)
        for step in result.steps:
            logger.info(
                "  step {} {} {}ms tokens in={} out={}",
                step.agent,
                step.status,
                step.duration_ms,
                step.input_tokens,
                step.output_tokens,
            )
        logger.info("Total latency: {}ms", result.duration_ms)
        logger.info("Rows returned: {}", len(result.rows))
    flush()


if __name__ == "__main__":
    main()
