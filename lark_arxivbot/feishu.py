"""Feishu (Lark) webhook utilities for pushing interactive cards."""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import time
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


def generate_feishu_signature(secret: str, timestamp: int) -> str:
    """Generate HMAC-SHA256 signature for Feishu webhook verification.

    Algorithm: Base64(HMAC-SHA256(timestamp + "\\n" + secret))

    Parameters
    ----------
    secret : str
        The secret key provided by Feishu custom bot settings.
    timestamp : int
        Current Unix timestamp in seconds.

    Returns
    -------
    str
        Base64-encoded signature string.
    """
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(hmac_code).decode("utf-8")


def push_card_to_feishu(card_content: Dict[str, Any]) -> bool:
    """Push an interactive card message to Feishu via webhook.

    Parameters
    ----------
    card_content : Dict[str, Any]
        The interactive card content following Feishu message card schema.

    Returns
    -------
    bool
        True if the message was sent successfully, False otherwise.
    """
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    secret = os.environ.get("FEISHU_SECRET", "")

    if not webhook_url:
        logger.error("FEISHU_WEBHOOK_URL environment variable is not set")
        return False

    payload: Dict[str, Any] = {
        "msg_type": "interactive",
        "card": card_content,
    }

    if secret:
        timestamp = int(time.time())
        payload["timestamp"] = str(timestamp)
        payload["sign"] = generate_feishu_signature(secret, timestamp)

    try:
        resp = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        result = resp.json()
        if result.get("code") == 0:
            logger.info("Feishu message sent successfully")
            return True
        logger.error(f"Feishu message failed: {result}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception while sending Feishu message: {e}")
        return False
