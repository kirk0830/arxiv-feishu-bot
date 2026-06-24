"""Tests for lark_arxivbot.arxiv_fetcher module."""

from __future__ import annotations

import socket
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree as ET

import pytest
import requests

from lark_arxivbot.arxiv_fetcher import (
    _build_query,
    _fetch_via_arxiv_lib,
    _fetch_via_atom_api,
    diagnose_network_connectivity,
    fetch_papers_from_arxiv,
)


class FakeAuthor:
    """Fake author object with a string name attribute."""

    def __init__(self, name: str) -> None:
        self.name = name


class FakeArxivResult:
    """Fake arxiv.Result for testing."""

    def __init__(self, title: str, summary: str, published: datetime) -> None:
        self.title = title
        self.summary = summary
        self.published = published
        self.entry_id = "http://arxiv.org/abs/1234.56789"
        self.pdf_url = "https://arxiv.org/pdf/1234.56789.pdf"
        self.authors = [FakeAuthor("Alice")]


def test_build_query() -> None:
    """Assert query string construction from categories and keywords."""
    query = _build_query(
        ["physics.chem-ph", "cond-mat.mtrl-sci"],
        ["molecular dynamics", "machine learning"],
    )
    assert "cat:physics.chem-ph" in query
    assert "cat:cond-mat.mtrl-sci" in query
    assert 'all:"molecular dynamics"' in query
    assert 'all:"machine learning"' in query
    assert "AND" in query


@patch("lark_arxivbot.arxiv_fetcher.arxiv.Client")
def test_fetch_via_arxiv_lib(mock_client_cls: MagicMock) -> None:
    """Assert official library path returns correctly shaped papers."""
    mock_result = FakeArxivResult(
        title="Test Paper",
        summary="This is a test.",
        published=datetime(2024, 1, 15, 10, 0, 0),
    )
    mock_client = MagicMock()
    mock_client.results.return_value = [mock_result]
    mock_client_cls.return_value = mock_client

    papers = _fetch_via_arxiv_lib("query", 10, "2024-01-14")

    assert len(papers) == 1
    assert papers[0]["original_title"] == "Test Paper"
    assert papers[0]["abstract"] == "This is a test."
    assert papers[0]["published"] == "2024-01-15"
    assert "html" in papers[0]["html_url"]


@patch("lark_arxivbot.arxiv_fetcher.arxiv.Client")
def test_fetch_via_arxiv_lib_older_papers_skipped(
    mock_client_cls: MagicMock,
) -> None:
    """Assert papers older than target_date are skipped."""
    mock_result = FakeArxivResult(
        title="Old Paper",
        summary="Too old.",
        published=datetime(2024, 1, 10, 10, 0, 0),
    )
    mock_client = MagicMock()
    mock_client.results.return_value = [mock_result]
    mock_client_cls.return_value = mock_client

    papers = _fetch_via_arxiv_lib("query", 10, "2024-01-15")
    assert len(papers) == 0


@patch("lark_arxivbot.arxiv_fetcher.requests.get")
def test_fetch_via_atom_api(mock_get: MagicMock) -> None:
    """Assert Atom API path parses mocked XML correctly."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
  <opensearch:totalResults>1</opensearch:totalResults>
  <opensearch:itemsPerPage>1</opensearch:itemsPerPage>
  <entry>
    <id>http://arxiv.org/abs/1234.56789</id>
    <published>2024-01-15T10:00:00Z</published>
    <title> Atom Test Paper </title>
    <summary> Atom test summary. </summary>
    <author><name>Bob</name></author>
    <link rel="alternate" href="https://arxiv.org/abs/1234.56789"/>
    <link title="pdf" href="https://arxiv.org/pdf/1234.56789.pdf"/>
  </entry>
</feed>
"""
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    papers = _fetch_via_atom_api("query", 10, "[20240101+TO+20240131]", "2024-01-14")

    assert len(papers) == 1
    assert papers[0]["original_title"] == "Atom Test Paper"
    assert papers[0]["abstract"] == "Atom test summary."
    assert papers[0]["published"] == "2024-01-15"
    assert papers[0]["authors"] == "Bob"


@patch("lark_arxivbot.arxiv_fetcher.requests.get")
def test_fetch_via_atom_api_all_endpoints_fail(mock_get: MagicMock) -> None:
    """Assert empty list when all Atom endpoints fail."""
    mock_get.side_effect = requests.exceptions.RequestException("fail")

    papers = _fetch_via_atom_api("query", 10, "range", "2024-01-14")
    assert papers == []


@patch("lark_arxivbot.arxiv_fetcher.arxiv.Client")
def test_fetch_papers_from_arxiv_fallback(mock_client_cls: MagicMock) -> None:
    """Assert fallback to Atom API when official library raises."""
    mock_client = MagicMock()
    mock_client.results.side_effect = RuntimeError("library error")
    mock_client_cls.return_value = mock_client

    with patch(
        "lark_arxivbot.arxiv_fetcher._fetch_via_atom_api"
    ) as mock_atom:
        mock_atom.return_value = [
            {
                "original_title": "Fallback",
                "abstract": "abs",
                "html_url": "https://x",
                "pdf_url": "https://y",
                "authors": "A",
                "published": "2024-01-15",
                "arxiv_id": "1234",
            }
        ]
        papers = fetch_papers_from_arxiv(
            categories=["physics.chem-ph"],
            keywords=["md"],
            days_back=1,
        )

    assert len(papers) == 1
    assert papers[0]["original_title"] == "Fallback"


@patch("lark_arxivbot.arxiv_fetcher.socket.gethostbyname")
@patch("lark_arxivbot.arxiv_fetcher.requests.get")
def test_diagnose_network_connectivity(
    mock_get: MagicMock, mock_dns: MagicMock
) -> None:
    """Assert diagnose returns expected shape without real network calls."""
    mock_dns.return_value = "1.2.3.4"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    results = diagnose_network_connectivity()

    assert isinstance(results, dict)
    assert any("OK" in v for v in results.values())


@patch("lark_arxivbot.arxiv_fetcher.arxiv.Client")
def test_fetch_papers_channel_api_success(
    mock_client_cls: MagicMock,
) -> None:
    """Assert channel='api' returns papers when library succeeds."""
    mock_result = FakeArxivResult(
        title="API Paper",
        summary="Summary.",
        published=datetime(2024, 1, 15, 10, 0, 0),
    )
    mock_client = MagicMock()
    mock_client.results.return_value = [mock_result]
    mock_client_cls.return_value = mock_client

    papers = fetch_papers_from_arxiv(
        categories=["physics.chem-ph"],
        keywords=["md"],
        channel="api",
        days_back=1000,
    )

    assert len(papers) == 1
    assert papers[0]["original_title"] == "API Paper"


@patch("lark_arxivbot.arxiv_fetcher.arxiv.Client")
def test_fetch_papers_channel_api_failure_returns_empty(
    mock_client_cls: MagicMock,
) -> None:
    """Assert channel='api' returns empty list on library failure."""
    mock_client = MagicMock()
    mock_client.results.side_effect = RuntimeError("library error")
    mock_client_cls.return_value = mock_client

    papers = fetch_papers_from_arxiv(
        categories=["physics.chem-ph"],
        keywords=["md"],
        channel="api",
    )

    assert papers == []


@patch("lark_arxivbot.arxiv_fetcher.requests.get")
def test_fetch_papers_channel_atom_success(
    mock_get: MagicMock,
) -> None:
    """Assert channel='atom' returns papers when Atom API succeeds."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
  <opensearch:totalResults>1</opensearch:totalResults>
  <opensearch:itemsPerPage>1</opensearch:itemsPerPage>
  <entry>
    <id>http://arxiv.org/abs/1234.56789</id>
    <published>2024-01-15T10:00:00Z</published>
    <title> Atom Paper </title>
    <summary> Atom summary. </summary>
    <author><name>Charlie</name></author>
    <link rel="alternate" href="https://arxiv.org/abs/1234.56789"/>
    <link title="pdf" href="https://arxiv.org/pdf/1234.56789.pdf"/>
  </entry>
</feed>
"""
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    papers = fetch_papers_from_arxiv(
        categories=["physics.chem-ph"],
        keywords=["md"],
        channel="atom",
        days_back=1000,
    )

    assert len(papers) == 1
    assert papers[0]["original_title"] == "Atom Paper"


@patch("lark_arxivbot.arxiv_fetcher.requests.get")
def test_fetch_papers_channel_atom_failure_returns_empty(
    mock_get: MagicMock,
) -> None:
    """Assert channel='atom' returns empty list on Atom API failure."""
    mock_get.side_effect = requests.exceptions.RequestException("fail")

    papers = fetch_papers_from_arxiv(
        categories=["physics.chem-ph"],
        keywords=["md"],
        channel="atom",
    )

    assert papers == []


@patch("lark_arxivbot.arxiv_fetcher.arxiv.Client")
def test_fetch_papers_channel_all_fallback_still_works(
    mock_client_cls: MagicMock,
) -> None:
    """Assert channel='all' still falls back to Atom on library failure."""
    mock_client = MagicMock()
    mock_client.results.side_effect = RuntimeError("library error")
    mock_client_cls.return_value = mock_client

    with patch(
        "lark_arxivbot.arxiv_fetcher._fetch_via_atom_api"
    ) as mock_atom:
        mock_atom.return_value = [
            {
                "original_title": "All Fallback",
                "abstract": "abs",
                "html_url": "https://x",
                "pdf_url": "https://y",
                "authors": "A",
                "published": "2024-01-15",
                "arxiv_id": "1234",
            }
        ]
        papers = fetch_papers_from_arxiv(
            categories=["physics.chem-ph"],
            keywords=["md"],
            channel="all",
        )

    assert len(papers) == 1
    assert papers[0]["original_title"] == "All Fallback"
