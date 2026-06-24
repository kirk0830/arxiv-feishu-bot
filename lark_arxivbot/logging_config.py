"""Logging configuration for lark_arxivbot."""

from __future__ import annotations

import logging
import logging.handlers
import os
from typing import Optional


def setup_logging(level: Optional[str] = None) -> None:
    """Configure the logging system for the application.

    Reads ``LOG_LEVEL`` from the environment (fallback to ``INFO``).
    Attaches a ``StreamHandler`` to the root logger and optionally
    a ``RotatingFileHandler`` if the filesystem is writable.

    Parameters
    ----------
    level : Optional[str], optional
        Logging level name (e.g., ``DEBUG``, ``INFO``). If ``None``,
        the value of the ``LOG_LEVEL`` environment variable is used.
    """
    resolved = (level or os.environ.get("LOG_LEVEL", "INFO")).upper()
    log_level = getattr(logging, resolved, logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    root = logging.getLogger()
    root.setLevel(log_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not any(
        isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
        for h in root.handlers
    ):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    # Attempt to add a rotating file handler; silently skip if read-only
    has_file_handler = any(
        isinstance(h, logging.handlers.RotatingFileHandler)
        for h in root.handlers
    )
    if not has_file_handler:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                "lark_arxivbot.log",
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError:
            pass
