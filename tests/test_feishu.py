"""Tests for lark_arxivbot.feishu module."""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from lark_arxivbot.feishu import (
    generate_feishu_signature,
    push_card_to_feishu,
)


def test_generate_feishu_signature_known_value() -> None:
    """Assert signature matches manual HMAC-SHA256 computation."""
    secret = "test_secret"
    timestamp = 1234567890
    expected = base64.b64encode(
        hmac.new(
            f"{timestamp}\n{secret}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
    ).decode("utf-8")
    assert generate_feishu_signature(secret, timestamp) == expected


@patch("lark_arxivbot.feishu.requests.post")
def test_push_card_to_feishu_success(mock_post: MagicMock, monkeypatch) -> None:
    """Assert successful push returns True and payload is well-formed."""
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://hook.feishu.cn")
    mock_post.return_value.json.return_value = {"code": 0, "msg": "ok"}

    card: Dict[str, Any] = {"header": {"title": "Test"}, "elements": []}
    result = push_card_to_feishu(card)

    assert result is True
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[1]["json"]["msg_type"] == "interactive"
    assert call_args[1]["json"]["card"] == card


@patch("lark_arxivbot.feishu.requests.post")
def test_push_card_to_feishu_with_secret(mock_post: MagicMock, monkeypatch) -> None:
    """Assert signature is included when FEISHU_SECRET is set."""
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://hook.feishu.cn")
    monkeypatch.setenv("FEISHU_SECRET", "my_secret")
    mock_post.return_value.json.return_value = {"code": 0}

    card: Dict[str, Any] = {"header": {"title": "Test"}, "elements": []}
    result = push_card_to_feishu(card)

    assert result is True
    payload = mock_post.call_args[1]["json"]
    assert "sign" in payload
    assert "timestamp" in payload


def test_push_card_to_feishu_missing_webhook() -> None:
    """Assert missing webhook URL returns False."""
    card: Dict[str, Any] = {"header": {"title": "Test"}, "elements": []}
    result = push_card_to_feishu(card)
    assert result is False


@patch("lark_arxivbot.feishu.requests.post")
def test_push_card_to_feishu_request_exception(
    mock_post: MagicMock, monkeypatch
) -> None:
    """Assert request exception returns False."""
    import requests

    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://hook.feishu.cn")
    mock_post.side_effect = requests.exceptions.RequestException("timeout")

    card: Dict[str, Any] = {"header": {"title": "Test"}, "elements": []}
    result = push_card_to_feishu(card)
    assert result is False
