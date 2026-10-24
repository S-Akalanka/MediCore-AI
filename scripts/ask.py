import sys

from loguru import logger

from nawaloka.engine.engine import ask
from nawaloka.log import setup_logging

DEFAULT_QUESTIONS = [
    "Show the 5 most recent patients",
    "What are the top 5 revenue-generating departments?",
    "DELETE all patients",
    "asdf qwerty zxcv",
]


def main() -> None:
    """Run questions through the NL2SQL engine and print the outcome."""
    setup_logging()
    questions = sys.argv[1:] or DEFAULT_QUESTIONS
    for question in questions:
        result = ask(question)
        logger.info("Question: {}", question)
        logger.info("Status: {} (attempts: {})", result.status, result.attempts)
        if result.sql:
            logger.info("SQL: {}", result.sql)
        if result.message:
            logger.info("Message: {}", result.message)
        for row in result.rows[:5]:
            logger.info("Row: {}", row)
        logger.info("Rows returned: {}", len(result.rows))


if __name__ == "__main__":
    main()
