"""Tests for lark_arxivbot.logging_config module."""

from __future__ import annotations

import logging
from typing import List

import pytest

from lark_arxivbot.logging_config import setup_logging


def _clear_all_handlers() -> None:
    """Remove all handlers from root logger."""
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.setLevel(logging.WARNING)


def _count_our_stream_handlers() -> int:
    """Count StreamHandlers that use our expected formatter."""
    root = logging.getLogger()
    expected_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    return len([
        h
        for h in root.handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
        and isinstance(h.formatter, logging.Formatter)
        and h.formatter._fmt == expected_fmt
    ])


def test_setup_logging_sets_level() -> None:
    """Assert setup_logging configures the root logger level."""
    _clear_all_handlers()
    setup_logging("DEBUG")
    root = logging.getLogger()
    assert root.level == logging.DEBUG


def test_setup_logging_attaches_stream_handler() -> None:
    """Assert a StreamHandler is attached after setup."""
    _clear_all_handlers()
    setup_logging("INFO")
    assert _count_our_stream_handlers() == 1


def test_setup_logging_no_duplicate_handlers() -> None:
    """Assert calling setup_logging twice does not duplicate handlers."""
    _clear_all_handlers()
    setup_logging("INFO")
    setup_logging("INFO")
    assert _count_our_stream_handlers() == 1
