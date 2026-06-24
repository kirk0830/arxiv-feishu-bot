"""arXiv Daily Paper Bot for Feishu (Lark).

Entry point that orchestrates paper retrieval, LLM summarization,
and Feishu card pushing.

Environment Variables:
    OPENAI_API_KEY: API key for LLM service.
    OPENAI_BASE_URL: Base URL for LLM API (optional).
    OPENAI_MODEL: Model name for LLM (optional, defaults to gpt-4o).
    FEISHU_WEBHOOK_URL: Feishu bot webhook URL.
    FEISHU_SECRET: Secret for Feishu signature verification (optional).
    MAX_PAPERS: Maximum papers to push per day (optional, defaults to 10).
    ENABLE_NETWORK_DIAG: Set to "true" to enable network diagnostics.
    LOG_LEVEL: Logging level (optional, defaults to INFO).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

from lark_arxivbot.arxiv import (
    diagnose_network_connectivity,
    fetch_papers_from_arxiv,
)
from lark_arxivbot.card import build_card_from_papers
from lark_arxivbot.config import DEFAULT_MAX_PAPERS
from lark_arxivbot.feishu import push_card_to_feishu
from lark_arxivbot.llm import summarize_paper_via_llm
from lark_arxivbot.logging_config import setup_logging

logger = logging.getLogger(__name__)


def run_daily_workflow() -> None:
    """Execute the complete daily paper retrieval and push workflow.

    Steps:
    1. Configure logging.
    2. Optional network diagnostics.
    3. Fetch papers from arXiv.
    4. Limit to MAX_PAPERS.
    5. Summarize each paper via LLM.
    6. Build and push Feishu interactive card.
    """
    setup_logging()

    if os.environ.get("ENABLE_NETWORK_DIAG", "").lower() == "true":
        diag = diagnose_network_connectivity()
        logger.info(f"Network diagnostics: {json.dumps(diag)}")

    papers = fetch_papers_from_arxiv()
    if not papers:
        logger.info("No new papers today, skipping push")
        return

    max_papers = int(os.environ.get("MAX_PAPERS", str(DEFAULT_MAX_PAPERS)))
    papers = papers[:max_papers]

    processed = [
        paper | summarize_paper_via_llm(
            paper["original_title"], paper["abstract"]
        )
        for paper in papers
    ]

    today_label = datetime.now().strftime("%Y年%m月%d日")
    card = build_card_from_papers(processed, today_label)

    if push_card_to_feishu(card):
        logger.info(f"Successfully pushed {len(processed)} papers to Feishu")
    else:
        logger.error("Failed to push to Feishu")


def handler(event: Any, context: Any) -> Dict[str, Any]:
    """Alibaba Cloud Function Compute entry point.

    Parameters
    ----------
    event : Any
        Trigger event payload (e.g., timer trigger metadata).
    context : Any
        Function runtime context.

    Returns
    -------
    Dict[str, Any]
        HTTP-style response with statusCode and body.
    """
    logger.info(f"Function invoked, event: {event}")

    try:
        run_daily_workflow()
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Success"}),
        }
    except Exception as e:
        logger.error(f"Function execution failed: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Failed: {str(e)}"}),
        }


if __name__ == "__main__":
    handler(None, None)
