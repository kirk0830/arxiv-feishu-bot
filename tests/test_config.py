"""Tests for lark_arxivbot.config module."""

from __future__ import annotations

import importlib
import os
from typing import List

import lark_arxivbot.config as config_module


def test_arxiv_categories_is_list_of_str() -> None:
    """Assert ARXIV_CATEGORIES is a non-empty List[str]."""
    assert isinstance(config_module.ARXIV_CATEGORIES, list)
    assert len(config_module.ARXIV_CATEGORIES) > 0
    for cat in config_module.ARXIV_CATEGORIES:
        assert isinstance(cat, str)


def test_arxiv_keywords_is_list_of_str() -> None:
    """Assert ARXIV_KEYWORDS is a non-empty List[str]."""
    assert isinstance(config_module.ARXIV_KEYWORDS, list)
    assert len(config_module.ARXIV_KEYWORDS) > 0
    for kw in config_module.ARXIV_KEYWORDS:
        assert isinstance(kw, str)


def test_default_values() -> None:
    """Assert default constants have expected values."""
    assert config_module.DEFAULT_MAX_RESULTS == 50
    assert config_module.DEFAULT_DAYS_BACK == 1
    assert config_module.DEFAULT_MAX_PAPERS == 10


def test_custom_endpoint_injection(monkeypatch) -> None:
    """Assert ARXIV_API_URL env var injects a custom endpoint."""
    custom_url = "https://custom.arxiv.org/api/query"
    monkeypatch.setenv("ARXIV_API_URL", custom_url)

    # Force re-import to pick up the new env var
    reloaded = importlib.reload(config_module)

    assert reloaded.ARXIV_API_ENDPOINTS[0] == custom_url
