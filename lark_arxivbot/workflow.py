"""Daily paper retrieval and push workflow."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from lark_arxivbot.arxiv_fetcher import (
    diagnose_network_connectivity,
    fetch_papers_from_arxiv,
)
from lark_arxivbot.card import build_card_from_papers
from lark_arxivbot.config import (
    DEFAULT_DAYS_BACK,
    DEFAULT_MAX_PAPERS,
    DEFAULT_MAX_RESULTS,
)
from lark_arxivbot.feishu import push_card_to_feishu
from lark_arxivbot.llm import summarize_paper_via_llm
from lark_arxivbot.logging_config import setup_logging

logger = logging.getLogger(__name__)


def run_daily_workflow(
    categories: Optional[str | List[str]] = None,
    keywords: Optional[str | List[str]] = None,
    channel: str = "all",
    max_results: int = DEFAULT_MAX_RESULTS,
    days_back: int = DEFAULT_DAYS_BACK,
    max_papers: int = DEFAULT_MAX_PAPERS,
) -> None:
    """Execute the complete daily paper retrieval and push workflow.

    Steps:
    1. Configure logging.
    2. Optional network diagnostics.
    3. Fetch papers from arXiv.
    4. Limit to MAX_PAPERS.
    5. Summarize each paper via LLM.
    6. Build and push Feishu interactive card.

    Parameters
    ----------
    categories : Optional[str | List[str]], optional
        Category expression or list of arXiv category strings.
        Defaults to config values.
    keywords : Optional[str | List[str]], optional
        Keyword expression or list of search keywords.
        Defaults to config values.
    channel : str, optional
        Retrieval channel (``"api"``, ``"atom"``, ``"all"``).
        Defaults to ``"all"``.
    max_results : int, optional
        Maximum results to fetch from arXiv. Defaults to 50.
    days_back : int, optional
        Days back to search. Defaults to 1.
    max_papers : int, optional
        Maximum papers to push. Defaults to 10.
    """
    setup_logging()

    if os.environ.get("ENABLE_NETWORK_DIAG", "").lower() == "true":
        diag = diagnose_network_connectivity()
        logger.info(f"Network diagnostics: {json.dumps(diag)}")

    papers = fetch_papers_from_arxiv(
        categories=categories,
        keywords=keywords,
        max_results=max_results,
        days_back=days_back,
        channel=channel,
    )
    if not papers:
        logger.info("No new papers today, skipping push")
        return

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
        logger.info(
            f"Successfully pushed {len(processed)} papers to Feishu"
        )
    else:
        logger.error("Failed to push to Feishu")
