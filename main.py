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
from typing import Any, Dict

from lark_arxivbot.logging_config import setup_logging
from lark_arxivbot.workflow import run_daily_workflow

logger = logging.getLogger(__name__)


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

    setup_logging()

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
