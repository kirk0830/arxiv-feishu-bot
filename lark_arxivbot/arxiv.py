"""arXiv paper retrieval with official library primary path and Atom API fallback."""

from __future__ import annotations

import logging
import os
import socket
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

import arxiv
import requests

from lark_arxivbot.config import (
    ARXIV_API_ENDPOINTS,
    ARXIV_CATEGORIES,
    ARXIV_KEYWORDS,
    DEFAULT_DAYS_BACK,
    DEFAULT_MAX_RESULTS,
    _ATOM_NS,
)

logger = logging.getLogger(__name__)


def diagnose_network_connectivity() -> Dict[str, str]:
    """Diagnose network connectivity to all configured arXiv endpoints.

    Performs DNS resolution and HTTP connectivity tests against each
    configured arXiv API endpoint.

    Returns
    -------
    Dict[str, str]
        Mapping of test names to their results (e.g., "OK (200)" or
        "FAIL: <error_message>").
    """
    results: Dict[str, str] = {}

    for endpoint in ARXIV_API_ENDPOINTS:
        hostname = endpoint.split("/")[2]
        try:
            ip = socket.gethostbyname(hostname)
            results[f"dns_{hostname}"] = f"OK ({ip})"
        except OSError as e:
            results[f"dns_{hostname}"] = f"FAIL: {e}"

    for endpoint in ARXIV_API_ENDPOINTS:
        try:
            resp = requests.get(
                endpoint,
                params={"search_query": "all:electron", "max_results": 1},
                timeout=10,
            )
            results[f"http_{endpoint}"] = f"OK ({resp.status_code})"
        except requests.exceptions.RequestException as e:
            results[f"http_{endpoint}"] = f"FAIL: {e}"

    return results


def _build_query(
    categories: List[str],
    keywords: List[str],
) -> str:
    """Build an arXiv search query string from categories and keywords.

    Parameters
    ----------
    categories : List[str]
        List of arXiv category strings.
    keywords : List[str]
        List of keywords to search in title and abstract.

    Returns
    -------
    str
        Combined query string suitable for arXiv API.
    """
    cat_clause = " OR ".join(f"cat:{c}" for c in categories)
    kw_clause = " OR ".join(f'all:"{kw}"' for kw in keywords)
    return f"({cat_clause}) AND ({kw_clause})"


def _fetch_via_arxiv_lib(
    query: str,
    max_results: int,
    target_date: str,
) -> List[Dict[str, str]]:
    """Fetch papers using the official arxiv Python library.

    Parameters
    ----------
    query : str
        arXiv search query string.
    max_results : int
        Maximum number of results to request.
    target_date : str
        Earliest submission date to include (``YYYY-MM-DD``).

    Returns
    -------
    List[Dict[str, str]]
        List of paper dictionaries.
    """
    client = arxiv.Client(
        page_size=max_results,
        delay_seconds=3,
        num_retries=5,
    )

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers: List[Dict[str, str]] = []
    for result in client.results(search):
        published_date = result.published.strftime("%Y-%m-%d")

        if published_date < target_date:
            break

        papers.append({
            "original_title": result.title,
            "abstract": result.summary,
            "html_url": result.entry_id.replace("abs", "html"),
            "pdf_url": result.pdf_url,
            "authors": ", ".join(a.name for a in result.authors),
            "published": published_date,
            "arxiv_id": result.entry_id.split("/")[-1],
        })
        logger.info(
            f"Found paper: [{published_date}] {result.title[:60]}..."
        )

    logger.info(f"Retrieved {len(papers)} papers via arxiv library")
    return papers


def _fetch_via_atom_api(
    query: str,
    max_results: int,
    date_range: str,
    target_date: str,
) -> List[Dict[str, str]]:
    """Fetch papers using the arXiv Atom API with endpoint fallback.

    Parameters
    ----------
    query : str
        arXiv search query string.
    max_results : int
        Maximum number of results to request.
    date_range : str
        Date range string for ``submittedDate`` filter.
    target_date : str
        Earliest submission date to include (``YYYY-MM-DD``).

    Returns
    -------
    List[Dict[str, str]]
        List of paper dictionaries.
    """
    full_query = f"{query} AND submittedDate:{date_range}"

    proxies: Dict[str, str] = {}
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get(
        "https_proxy"
    )
    if http_proxy:
        proxies["http"] = http_proxy
    if https_proxy:
        proxies["https"] = https_proxy

    last_error: Optional[Exception] = None
    resp: Optional[requests.Response] = None
    successful_endpoint: Optional[str] = None

    for endpoint in ARXIV_API_ENDPOINTS:
        try:
            logger.info(f"Trying Atom endpoint: {endpoint}")
            resp = requests.get(
                endpoint,
                params={
                    "search_query": full_query,
                    "max_results": max_results,
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
                f"Endpoint {endpoint} succeeded "
                f"(HTTP {resp.status_code})"
            )
            successful_endpoint = endpoint
            break
        except requests.exceptions.RequestException as e:
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

        papers: List[Dict[str, str]] = []
        for entry in root.findall("atom:entry", _ATOM_NS):
            published_elem = entry.find("atom:published", _ATOM_NS)
            if published_elem is None:
                continue
            published_date = published_elem.text[:10]

            if published_date < target_date:
                break

            id_elem = entry.find("atom:id", _ATOM_NS)
            arxiv_id = (
                id_elem.text.split("/")[-1]
                if id_elem is not None
                else ""
            )

            title_elem = entry.find("atom:title", _ATOM_NS)
            title = (
                title_elem.text.strip()
                if title_elem is not None
                else ""
            )

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
            logger.info(
                f"Found paper: [{published_date}] {title[:60]}..."
            )

        logger.info(
            f"Parsed {len(papers)} papers via Atom API "
            f"({successful_endpoint})"
        )
        return papers

    except ET.ParseError as e:
        logger.error(f"Failed to parse arXiv Atom response: {e}")
        return []


def fetch_papers_from_arxiv(
    categories: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    max_results: int = DEFAULT_MAX_RESULTS,
    days_back: int = DEFAULT_DAYS_BACK,
) -> List[Dict[str, str]]:
    """Fetch yesterday's new papers from arXiv matching given criteria.

    Uses the official ``arxiv`` Python library as the primary path.
    Falls back to the Atom XML API if the primary path fails.

    Parameters
    ----------
    categories : Optional[List[str]], optional
        List of arXiv category strings. Defaults to
        ``config.ARXIV_CATEGORIES`` when ``None``.
    keywords : Optional[List[str]], optional
        List of keywords to search in title and abstract. Defaults to
        ``config.ARXIV_KEYWORDS`` when ``None``.
    max_results : int, optional
        Maximum number of results to return. Defaults to 50.
    days_back : int, optional
        Number of days back from today to filter. Defaults to 1.

    Returns
    -------
    List[Dict[str, str]]
        List of paper dictionaries with keys: original_title,
        abstract, html_url, pdf_url, authors, published, arxiv_id.
    """
    resolved_categories = (
        categories if categories is not None else ARXIV_CATEGORIES
    )
    resolved_keywords = (
        keywords if keywords is not None else ARXIV_KEYWORDS
    )

    target = datetime.utcnow() - timedelta(days=days_back)
    target_date = target.strftime("%Y-%m-%d")
    date_start = target.strftime("%Y%m%d") + "0000"
    date_end = target.strftime("%Y%m%d") + "2359"
    date_range = f"[{date_start}+TO+{date_end}]"

    query = _build_query(resolved_categories, resolved_keywords)

    logger.info("Starting arXiv paper retrieval")
    logger.info(f"Target date: {target_date} (GMT)")
    logger.info(f"Query: {query}")

    try:
        return _fetch_via_arxiv_lib(query, max_results, target_date)
    except Exception as e:
        logger.warning(
            f"Primary arxiv library path failed: {e}. "
            f"Falling back to Atom API."
        )
        return _fetch_via_atom_api(
            query, max_results, date_range, target_date
        )
