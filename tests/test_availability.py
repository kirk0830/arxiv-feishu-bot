"""Tests for lark_arxivbot.availability module."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from openai import APITimeoutError

from lark_arxivbot.availability import (
    check_arxiv_availability,
    check_llm_availability,
    check_network_availability,
    run_availability_checks,
)


@patch("lark_arxivbot.availability.diagnose_network_connectivity")
def test_check_network_availability_true(
    mock_diag: MagicMock,
) -> None:
    """Assert network check passes when at least one HTTP probe OK."""
    mock_diag.return_value = {
        "dns_example.com": "OK (1.2.3.4)",
        "http_https://example.com/api": "OK (200)",
    }
    assert check_network_availability() is True


@patch("lark_arxivbot.availability.diagnose_network_connectivity")
def test_check_network_availability_false(
    mock_diag: MagicMock,
) -> None:
    """Assert network check fails when all HTTP probes fail."""
    mock_diag.return_value = {
        "dns_example.com": "FAIL: timeout",
        "http_https://example.com/api": "FAIL: 500",
    }
    assert check_network_availability() is False


@patch("lark_arxivbot.availability.fetch_papers_from_arxiv")
def test_check_arxiv_availability_true(
    mock_fetch: MagicMock,
) -> None:
    """Assert arXiv check passes when fetch succeeds."""
    mock_fetch.return_value = []
    assert check_arxiv_availability("api") is True
    mock_fetch.assert_called_once_with(
        max_results=1, days_back=1, channel="api"
    )


@patch("lark_arxivbot.availability.fetch_papers_from_arxiv")
def test_check_arxiv_availability_false(
    mock_fetch: MagicMock,
) -> None:
    """Assert arXiv check fails when fetch raises."""
    mock_fetch.side_effect = RuntimeError("fetch error")
    assert check_arxiv_availability("atom") is False


@patch("lark_arxivbot.availability.OpenAI")
@patch("lark_arxivbot.availability.os.environ.get")
def test_check_llm_availability_with_key(
    mock_get: MagicMock,
    mock_openai_cls: MagicMock,
) -> None:
    """Assert LLM check passes when the model responds."""

    def _getenv(key: str, default: Any = None) -> Any:
        if key == "OPENAI_API_KEY":
            return "sk-test"
        return default

    mock_get.side_effect = _getenv

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "I am an AI assistant."
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_cls.return_value = mock_client

    assert check_llm_availability() is True
    mock_client.chat.completions.create.assert_called_once()


@patch("lark_arxivbot.availability.os.environ.get")
def test_check_llm_availability_without_key(
    mock_get: MagicMock,
) -> None:
    """Assert LLM check fails when OPENAI_API_KEY is missing."""
    mock_get.return_value = None
    assert check_llm_availability() is False


@patch("lark_arxivbot.availability.OpenAI")
@patch("lark_arxivbot.availability.os.environ.get")
def test_check_llm_availability_timeout(
    mock_get: MagicMock,
    mock_openai_cls: MagicMock,
) -> None:
    """Assert LLM check fails on API timeout."""

    def _getenv(key: str, default: Any = None) -> Any:
        if key == "OPENAI_API_KEY":
            return "sk-test"
        return default

    mock_get.side_effect = _getenv

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = APITimeoutError(
        "Request timed out"
    )
    mock_openai_cls.return_value = mock_client

    assert check_llm_availability() is False


@patch("lark_arxivbot.availability.OpenAI")
@patch("lark_arxivbot.availability.os.environ.get")
def test_check_llm_availability_api_error(
    mock_get: MagicMock,
    mock_openai_cls: MagicMock,
) -> None:
    """Assert LLM check fails on generic API error."""

    def _getenv(key: str, default: Any = None) -> Any:
        if key == "OPENAI_API_KEY":
            return "sk-test"
        return default

    mock_get.side_effect = _getenv

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError(
        "connection refused"
    )
    mock_openai_cls.return_value = mock_client

    assert check_llm_availability() is False


@patch("lark_arxivbot.availability.check_network_availability")
@patch("lark_arxivbot.availability.check_arxiv_availability")
@patch("lark_arxivbot.availability.check_llm_availability")
@patch("lark_arxivbot.availability.check_user_agent_email")
def test_run_availability_checks_all_pass(
    mock_email: MagicMock,
    mock_llm: MagicMock,
    mock_arxiv: MagicMock,
    mock_network: MagicMock,
) -> None:
    """Assert all checks return True when services are healthy."""
    mock_network.return_value = True
    mock_arxiv.return_value = True
    mock_llm.return_value = True
    mock_email.return_value = True

    results = run_availability_checks("all")
    assert results == {
        "network": True,
        "arxiv": True,
        "llm": True,
        "email": True,
    }


@patch("lark_arxivbot.availability.check_network_availability")
@patch("lark_arxivbot.availability.check_arxiv_availability")
@patch("lark_arxivbot.availability.check_llm_availability")
@patch("lark_arxivbot.availability.check_user_agent_email")
def test_run_availability_checks_one_fail(
    mock_email: MagicMock,
    mock_llm: MagicMock,
    mock_arxiv: MagicMock,
    mock_network: MagicMock,
) -> None:
    """Assert failed check is reflected in results."""
    mock_network.return_value = True
    mock_arxiv.return_value = False
    mock_llm.return_value = True
    mock_email.return_value = True

    results = run_availability_checks("all")
    assert results == {
        "network": True,
        "arxiv": False,
        "llm": True,
        "email": True,
    }
