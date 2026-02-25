"""
Loguru logging configuration for binance-futures-bot.

Configures two sinks:
  - Rotating file sink at logs/trading_bot.log (DEBUG level, 10 MB rotation, 5 retained files)
  - Console sink to stderr (INFO level, colourised rich-compatible format)
"""

import sys

from loguru import logger


def setup_logging() -> None:
    """Configure Loguru sinks for file and console output.

    Call this once at application startup (e.g., at the top of cli.py).
    Subsequent calls are idempotent because the default handler is removed first.
    """
    # Remove the default Loguru handler so we control all output.
    logger.remove()

    # ------------------------------------------------------------------
    # File sink: DEBUG level, 10 MB rotation, 5 retained files.
    # ------------------------------------------------------------------
    logger.add(
        "logs/trading_bot.log",
        level="DEBUG",
        rotation="10 MB",
        retention=5,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | "
            "{name}:{function}:{line} - {message}"
        ),
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # ------------------------------------------------------------------
    # Console sink: INFO level, colourised output via Loguru markup.
    # ------------------------------------------------------------------
    logger.add(
        sys.stderr,
        level="INFO",
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level:<8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )
