"""Availability checks for LLM, arXiv, and network."""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Dict

from openai import OpenAI, APITimeoutError

from lark_arxivbot.arxiv_fetcher import (
    diagnose_network_connectivity,
    fetch_papers_from_arxiv,
)

logger = logging.getLogger(__name__)

_TIMEOUT_NETWORK: float = 30.0
_TIMEOUT_ARXIV: float = 30.0
_TIMEOUT_LLM: float = 15.0


def check_network_availability() -> bool:
    """Check whether at least one arXiv endpoint is reachable.

    Performs DNS resolution and HTTP connectivity tests with a
    hard timeout of 30 seconds.

    Returns
    -------
    bool
        True if any HTTP endpoint responds with status 200,
        False otherwise.
    """
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(diagnose_network_connectivity)
            results = future.result(timeout=_TIMEOUT_NETWORK)
    except TimeoutError:
        logger.error("Network availability check timed out")
        return False

    ok = any(
        k.startswith("http_") and v.startswith("OK")
        for k, v in results.items()
    )
    if ok:
        logger.info("Network availability check passed")
    else:
        logger.error("Network availability check failed")
    return ok


def _check_arxiv(channel: str) -> bool:
    """Internal arXiv check without timeout wrapper."""
    try:
        papers = fetch_papers_from_arxiv(
            max_results=1,
            days_back=1,
            channel=channel,
        )
        logger.info(
            f"arXiv availability check passed "
            f"(channel={channel}, papers={len(papers)})"
        )
        return True
    except Exception as e:
        logger.error(f"arXiv availability check failed: {e}")
        return False


def check_arxiv_availability(channel: str) -> bool:
    """Check whether the requested arXiv channel is functional.

    Performs a lightweight query (1 result, 1 day back) via the
    requested channel with a hard timeout of 30 seconds.

    Parameters
    ----------
    channel : str
        Retrieval channel (``"api"``, ``"atom"``, or ``"all"``).

    Returns
    -------
    bool
        True if the query succeeds without exception, False otherwise.
    """
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_check_arxiv, channel)
            return future.result(timeout=_TIMEOUT_ARXIV)
    except TimeoutError:
        logger.error("arXiv availability check timed out")
        return False


def check_llm_availability() -> bool:
    """Check whether the LLM service responds to a chat request.

    Sends a minimal chat-completion message to verify end-to-end
    connectivity. Uses a 15-second HTTP timeout on the OpenAI client.

    Returns
    -------
    bool
        True if the LLM returns a response, False otherwise.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error(
            "LLM availability check failed: OPENAI_API_KEY not set"
        )
        return False

    base_url = os.environ.get("OPENAI_BASE_URL", "")
    model = os.environ.get("OPENAI_MODEL", "")

    client_kwargs: Dict[str, str] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    try:
        client = OpenAI(timeout=_TIMEOUT_LLM, **client_kwargs)
        model_name = model if model else "gpt-4o"
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Who are you?"}],
            max_tokens=20,
        )
        content = response.choices[0].message.content.strip()
        logger.info(
            f"LLM availability check passed "
            f"(model={model_name}, response={content[:40]!r})"
        )
        return True
    except APITimeoutError:
        logger.error("LLM availability check timed out")
        return False
    except Exception as e:
        logger.error(f"LLM availability check failed: {e}")
        return False


def check_user_agent_email() -> bool:
    """Check whether the User-Agent email is set.

    Returns
    -------
    bool
        True if the email is set, False otherwise.
    """
    email = os.environ.get("USER_AGENT_EMAIL")
    if not email:
        logger.warning(
            "User-Agent email check failed: USER_AGENT_EMAIL not set"
        )
        return False
    logger.info("User-Agent email check passed")
    return True


def run_availability_checks(channel: str) -> Dict[str, bool]:
    """Run all availability checks in order.

    Checks are executed in the order: network, arXiv, LLM.

    Parameters
    ----------
    channel : str
        Retrieval channel to test for arXiv availability.

    Returns
    -------
    Dict[str, bool]
        Mapping of check names to their results.
    """
    logger.info("Starting availability checks")
    results: Dict[str, bool] = {
        "network": check_network_availability(),
        "arxiv": check_arxiv_availability(channel),
        "llm": check_llm_availability(),
        "email": check_user_agent_email(),
    }
    logger.info(f"Availability checks complete: {results}")
    return results
