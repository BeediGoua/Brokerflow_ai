"""
Simple logging configuration for BrokerFlow AI.

This module exposes a helper to get a configured logger.  It avoids adding
duplicate handlers if called multiple times.
"""

import logging
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger instance.

    If the logger already has handlers attached, this function does not add
    duplicate handlers.  By default the logger writes to standard output
    and uses a simple format.

    Args:
        name: Optional name of the logger.  If ``None`` a root logger is used.

    Returns:
        A configured :class:`logging.Logger` object.
    """

    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # Default to INFO level unless specified otherwise
        logger.setLevel(logging.INFO)
    return logger