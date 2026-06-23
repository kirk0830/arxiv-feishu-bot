"""
arXiv Daily Paper Bot for Feishu (Lark).

Automatically fetches new papers from arXiv in computational physics,
molecular dynamics, and machine learning, translates and summarizes
them via LLM, and pushes formatted cards to Feishu group via webhook.

Environment Variables:
    OPENAI_API_KEY: API key for LLM service.
    OPENAI_BASE_URL: Base URL for LLM API (optional).
    OPENAI_MODEL: Model name for LLM (optional, defaults to gpt-4o).
    FEISHU_WEBHOOK_URL: Feishu bot webhook URL.
    FEISHU_SECRET: Secret for Feishu signature verification (optional).
    MAX_PAPERS: Maximum papers to push per day (optional, defaults to 10).
    ENABLE_NETWORK_DIAG: Set to "true" to enable network diagnostics.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import socket
import time
from datetime import datetime, timedelta
from typing import Any
from xml.etree import ElementTree as ET

import requests
from openai import OpenAI

# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

ARXIV_API_ENDPOINTS: list[str] = [
    "https://cn.arxiv.org/api/query",
    "https://xxx.itp.ac.cn/api/query",
    "https://export.arxiv.org/api/query",
    "https://arxiv.org/api/query",
]

_CUSTOM_ENDPOINT: str | None = os.environ.get("ARXIV_API_URL")
if _CUSTOM_ENDPOINT:
    ARXIV_API_ENDPOINTS.insert(0, _CUSTOM_ENDPOINT)

_ATOM_NS: dict[str, str] = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}


# =============================================================================
# Network Diagnostics
# =============================================================================

def diagnose_network_connectivity() -> dict[str, str]:
    """Diagnose network connectivity to all configured arXiv endpoints.

    Performs DNS resolution and HTTP connectivity tests against each
    configured arXiv API endpoint.

    Returns
    -------
    dict[str, str]
        Mapping of test names to their results (e.g., "OK (200)" or
        "FAIL: <error_message>").
    """
    results: dict[str, str] = {}

    for endpoint in ARXIV_API_ENDPOINTS:
        hostname = endpoint.split("/")[2]
        try:
            ip = socket.gethostbyname(hostname)
            results[f"dns_{hostname}"] = f"OK ({ip})"
        except Exception as e:
            results[f"dns_{hostname}"] = f"FAIL: {e}"

    for endpoint in ARXIV_API_ENDPOINTS:
        try:
            resp = requests.get(
                endpoint,
                params={"search_query": "all:electron", "max_results": 1},
                timeout=10,
            )
            results[f"http_{endpoint}"] = f"OK ({resp.status_code})"
        except Exception as e:
            results[f"http_{endpoint}"] = f"FAIL: {e}"

    return results


# =============================================================================
# Feishu Webhook Utilities
# =============================================================================

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


def push_card_to_feishu(card_content: dict[str, Any]) -> bool:
    """Push an interactive card message to Feishu via webhook.

    Parameters
    ----------
    card_content : dict[str, Any]
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

    payload: dict[str, Any] = {
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
    except Exception as e:
        logger.error(f"Exception while sending Feishu message: {e}")
        return False


# =============================================================================
# Card Builder
# =============================================================================

def build_card_from_papers(
    papers: list[dict[str, str]],
    date_label: str,
) -> dict[str, Any]:
    """Build a Feishu interactive card from a list of paper dictionaries.

    Parameters
    ----------
    papers : list[dict[str, str]]
        List of paper dictionaries containing chinese_title,
        original_title, chinese_abstract, highlights, and html_url.
    date_label : str
        Human-readable date string for the card header.

    Returns
    -------
    dict[str, Any]
        Feishu interactive card payload.
    """
    header = {
        "template": "blue",
        "title": {
            "content": f"📚 计算物理日报 | {date_label}",
            "tag": "plain_text",
        },
    }

    intro = (
        f"**今日共检索到 {len(papers)} 篇相关论文**\n\n"
        f"🔬 领域：计算物理 | 分子动力学模拟 | 机器学习\n"
        f"📅 日期：{date_label}"
    )

    elements: list[dict[str, Any]] = [
        {"tag": "div", "text": {"tag": "lark_md", "content": intro}},
        {"tag": "hr"},
    ]

    for idx, paper in enumerate(papers, 1):
        elements.extend([
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{idx}. {paper['chinese_title']}**",
                },
            },
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": f"原文：{paper['original_title']}",
                    },
                ],
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📝 **摘要**：{paper['chinese_abstract']}",
                },
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"💡 **亮点**：{paper['highlights']}",
                },
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "📄 查看论文详情",
                        },
                        "type": "primary",
                        "url": paper["html_url"],
                    },
                ],
            },
        ])
        if idx < len(papers):
            elements.append({"tag": "hr"})

    elements.extend([
        {"tag": "hr"},
        {
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": (
                        "数据来源：arXiv | 翻译总结：AI 辅助生成 | 仅供参考"
                    ),
                },
            ],
        },
    ])

    return {
        "config": {"wide_screen_mode": True},
        "header": header,
        "elements": elements,
    }


# =============================================================================
# LLM Summarization
# =============================================================================

def summarize_paper_via_llm(
    title: str,
    abstract: str,
) -> dict[str, str]:
    """Translate and summarize a paper abstract using an LLM.

    Uses standard terminology from computational chemistry and
    theoretical chemistry. Returns Chinese title, abstract, and
    highlight bullet points.

    Parameters
    ----------
    title : str
        Original English paper title.
    abstract : str
        Original English paper abstract.

    Returns
    -------
    dict[str, str]
        Dictionary with keys: chinese_title, chinese_abstract, highlights.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "")
    model = os.environ.get("OPENAI_MODEL", "")

    if not api_key:
        logger.warning("OPENAI_API_KEY not set, skipping LLM translation")
        return {
            "chinese_title": title,
            "chinese_abstract": abstract,
            "highlights": "（LLM 翻译未启用）",
        }

    client_kwargs: dict[str, str] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    client = OpenAI(**client_kwargs)

    system_prompt = (
        "You are a senior researcher in computational chemistry, "
        "theoretical chemistry, and molecular simulation.\n"
        "Translate and summarize the following paper professionally. "
        "Requirements:\n"
        "1. Use standard terminology from chemical physics, theoretical "
        "chemistry, and computational chemistry.\n"
        "2. Chinese title must accurately reflect the core content.\n"
        "3. Chinese abstract must preserve scientific meaning with "
        "standard terminology.\n"
        "4. Highlight summary (3-5 points) should emphasize: "
        "methodological innovation, key findings, and application value.\n"
        "5. Key terms include: molecular dynamics (MD), density functional "
        "theory (DFT), potential energy surface (PES), free energy "
        "calculation, coarse-grained model, force field parameterization, "
        "neural network potential (NNP), reaction path, ensemble average, "
        "etc."
    )

    user_prompt = (
        f"Paper Title: {title}\n\n"
        f"Paper Abstract: {abstract}\n\n"
        f"Output format (strictly use | as delimiter):\n"
        f"Chinese Title | Chinese Abstract | Highlight1; Highlight2; "
        f"Highlight3"
    )

    try:
        model_name = model if model else "gpt-4o"
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        content = response.choices[0].message.content.strip()
        parts = content.split(" | ")

        if len(parts) >= 3:
            return {
                "chinese_title": parts[0].strip(),
                "chinese_abstract": parts[1].strip(),
                "highlights": parts[2].strip(),
            }

        lines = [line.strip() for line in content.split("\n") if line.strip()]
        return {
            "chinese_title": lines[0] if lines else title,
            "chinese_abstract": (
                "\n".join(lines[1:-1]) if len(lines) > 2 else abstract
            ),
            "highlights": lines[-1] if len(lines) > 1 else "总结生成中...",
        }

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return {
            "chinese_title": title,
            "chinese_abstract": abstract,
            "highlights": f"（LLM 翻译失败: {str(e)[:50]}）",
        }


# =============================================================================
# arXiv Fetching
# =============================================================================

def fetch_papers_from_arxiv() -> list[dict[str, str]]:
    """Fetch yesterday's new papers from arXiv matching MD + ML keywords.

    Uses submittedDate range query to retrieve only papers submitted
    within the target date window. Tries multiple endpoints in order
    until one succeeds.

    Returns
    -------
    list[dict[str, str]]
        List of paper dictionaries with keys: original_title, abstract,
        html_url, pdf_url, authors, published, arxiv_id.
    """
    yesterday = datetime.utcnow() - timedelta(days=1)
    date_start = yesterday.strftime("%Y%m%d") + "0000"
    date_end = yesterday.strftime("%Y%m%d") + "2359"
    date_str = yesterday.strftime("%Y-%m-%d")
    date_range = f"[{date_start}+TO+{date_end}]"

    search_query = (
        f'(cat:physics.chem-ph OR cat:cond-mat.mtrl-sci '
        f'OR cat:physics.comp-ph) '
        f'AND (all:"molecular dynamics" OR all:"machine learning" '
        f'OR all:"deep learning" OR all:"neural network") '
        f'AND submittedDate:{date_range}'
    )

    logger.info("Starting arXiv paper retrieval")
    logger.info(f"Target date: {date_str} (GMT)")
    logger.info(f"Date range: {date_range}")
    logger.info(f"Search query: {search_query}")

    proxies: dict[str, str] = {}
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get(
        "https_proxy"
    )
    if http_proxy:
        proxies["http"] = http_proxy
    if https_proxy:
        proxies["https"] = https_proxy

    last_error: Exception | None = None
    resp: requests.Response | None = None
    successful_endpoint: str | None = None

    for endpoint in ARXIV_API_ENDPOINTS:
        try:
            logger.info(f"Trying endpoint: {endpoint}")
            resp = requests.get(
                endpoint,
                params={
                    "search_query": search_query,
                    "max_results": 50,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                },
                proxies=proxies if proxies else None,
                timeout=30,
                headers={
                    "User-Agent": "arxiv-bot/1.0 (academic-research-bot)",
                },
            )
            resp.raise_for_status()
            logger.info(
                f"Endpoint {endpoint} succeeded (HTTP {resp.status_code})"
            )
            successful_endpoint = endpoint
            break
        except Exception as e:
            logger.warning(f"Endpoint {endpoint} failed: {e}")
            last_error = e

    if resp is None or successful_endpoint is None:
        logger.error(
            f"All arXiv endpoints unreachable. Last error: {last_error}"
        )
        return []

    try:
        root = ET.fromstring(resp.text)

        total_elem = root.find("opensearch:totalResults", _ATOM_NS)
        total_results = (
            total_elem.text if total_elem is not None else "unknown"
        )
        logger.info(f"arXiv API total results: {total_results}")

        items_elem = root.find("opensearch:itemsPerPage", _ATOM_NS)
        items_per_page = (
            items_elem.text if items_elem is not None else "unknown"
        )
        logger.info(f"Results returned: {items_per_page}")

        papers: list[dict[str, str]] = []
        for entry in root.findall("atom:entry", _ATOM_NS):
            published_elem = entry.find("atom:published", _ATOM_NS)
            if published_elem is None:
                continue
            published_date = published_elem.text[:10]

            id_elem = entry.find("atom:id", _ATOM_NS)
            arxiv_id = (
                id_elem.text.split("/")[-1] if id_elem is not None else ""
            )

            title_elem = entry.find("atom:title", _ATOM_NS)
            title = title_elem.text.strip() if title_elem is not None else ""

            summary_elem = entry.find("atom:summary", _ATOM_NS)
            summary = (
                summary_elem.text.strip()
                if summary_elem is not None
                else ""
            )

            authors = [
                name_elem.text
                for author in entry.findall("atom:author", _ATOM_NS)
                if (name_elem := author.find("atom:name", _ATOM_NS))
                is not None
            ]

            html_url = f"https://arxiv.org/html/{arxiv_id}"
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            for link in entry.findall("atom:link", _ATOM_NS):
                rel = link.get("rel", "")
                title_attr = link.get("title", "")
                href = link.get("href", "")
                if rel == "alternate" and not title_attr:
                    html_url = href
                elif title_attr == "pdf":
                    pdf_url = href

            papers.append({
                "original_title": title,
                "abstract": summary,
                "html_url": html_url,
                "pdf_url": pdf_url,
                "authors": ", ".join(authors),
                "published": published_date,
                "arxiv_id": arxiv_id,
            })
            logger.info(f"Found paper: [{published_date}] {title[:60]}...")

        logger.info(
            f"Parsed {len(papers)} papers via {successful_endpoint}"
        )
        return papers

    except Exception as e:
        logger.error(f"Failed to parse arXiv response: {e}")
        logger.debug(f"Response preview: {resp.text[:500]}")
        return []


# =============================================================================
# Main Orchestration
# =============================================================================

def run_daily_workflow() -> None:
    """Execute the complete daily paper retrieval and push workflow.

    Steps:
    1. Optional network diagnostics.
    2. Fetch papers from arXiv.
    3. Limit to MAX_PAPERS.
    4. Summarize each paper via LLM.
    5. Build and push Feishu interactive card.
    """
    if os.environ.get("ENABLE_NETWORK_DIAG", "").lower() == "true":
        diag = diagnose_network_connectivity()
        logger.info(f"Network diagnostics: {json.dumps(diag)}")

    papers = fetch_papers_from_arxiv()
    if not papers:
        logger.info("No new papers today, skipping push")
        return

    max_papers = int(os.environ.get("MAX_PAPERS", "10"))
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


# =============================================================================
# Entry Points
# =============================================================================

def handler(event: Any, context: Any) -> dict[str, Any]:
    """Alibaba Cloud Function Compute entry point.

    Parameters
    ----------
    event : Any
        Trigger event payload (e.g., timer trigger metadata).
    context : Any
        Function runtime context.

    Returns
    -------
    dict[str, Any]
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