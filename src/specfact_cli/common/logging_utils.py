"""Logging helpers with graceful fallback when SpecFact CLI common module is unavailable."""

from __future__ import annotations

import logging

from beartype import beartype
from icontract import ensure, require


@beartype
@require(lambda name: isinstance(name, str) and len(name) > 0, "Name must be non-empty string")
@require(lambda level: isinstance(level, str) and len(level) > 0, "Level must be non-empty string")
@ensure(lambda result: isinstance(result, logging.Logger), "Must return Logger instance")
def get_bridge_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Retrieve a configured logger.

    If the SpecFact CLI `common.logger_setup` module is available we reuse it, otherwise
    we create a standard library logger to keep the bridge self-contained.
    """
    logger = _try_common_logger(name, level)
    if logger is not None:
        return logger

    fallback_logger = logging.getLogger(name)
    if not fallback_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        handler.setFormatter(formatter)
        fallback_logger.addHandler(handler)
    fallback_logger.setLevel(level.upper())
    return fallback_logger


def _try_common_logger(name: str, level: str) -> logging.Logger | None:
    try:
        from specfact_cli.common.logger_setup import LoggerSetup  # type: ignore[import]
    except ImportError:
        return None
    return LoggerSetup.create_logger(name, log_level=level)
