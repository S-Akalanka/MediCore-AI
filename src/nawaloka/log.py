import sys

from loguru import logger

_FORMAT = (
    "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
)


def setup_logging(level: str = "INFO") -> None:
    """Configure loguru for the current process."""
    logger.remove()
    logger.add(sys.stderr, format=_FORMAT, level=level.upper())
