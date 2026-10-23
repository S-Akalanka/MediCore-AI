import os

from loguru import logger

from nawaloka.config import OBSERVABILITY_ENABLED, get_model, get_setting
from nawaloka.log import setup_logging

REQUIRED_ENV = ["GROQ_API_KEY", "DATABASE_URL"]
OPTIONAL_ENV = ["LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY"]


def main() -> None:
    """Print a startup check of configuration and environment."""
    setup_logging()
    logger.info("Provider: {}", get_setting("provider", "default"))
    for role in ["router", "sql_generator", "interpreter", "fallback"]:
        logger.info("Model {}: {}", role, get_model(role))
    logger.info("Observability enabled: {}", OBSERVABILITY_ENABLED)
    for name in REQUIRED_ENV:
        if os.getenv(name):
            logger.success("{} is set", name)
        else:
            logger.error("{} is missing", name)
    for name in OPTIONAL_ENV:
        if os.getenv(name):
            logger.success("{} is set", name)
        else:
            logger.warning("{} is not set", name)
