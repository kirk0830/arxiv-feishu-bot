"""Tests for lark_arxivbot.card module."""

from __future__ import annotations

from typing import Any, Dict, List

from lark_arxivbot.card import build_card_from_papers


def test_build_card_structure() -> None:
    """Assert card payload contains expected top-level keys."""
    papers: List[Dict[str, str]] = [
        {
            "chinese_title": "测试标题",
            "original_title": "Test Title",
            "chinese_abstract": "测试摘要",
            "highlights": "亮点1; 亮点2",
            "html_url": "https://arxiv.org/html/1234.56789",
        }
    ]
    card = build_card_from_papers(papers, "2024-01-01")

    assert "config" in card
    assert "header" in card
    assert "elements" in card
    assert card["header"]["template"] == "blue"


def test_build_card_header_title() -> None:
    """Assert header title contains the date label."""
    papers: List[Dict[str, str]] = []
    card = build_card_from_papers(papers, "2024-01-01")
    title_content = card["header"]["title"]["content"]
    assert "2024-01-01" in title_content


def test_build_card_paper_count() -> None:
    """Assert intro text reflects the number of papers."""
    papers: List[Dict[str, str]] = [
        {
            "chinese_title": "A",
            "original_title": "A_en",
            "chinese_abstract": "摘要A",
            "highlights": "h1",
            "html_url": "https://a",
        },
        {
            "chinese_title": "B",
            "original_title": "B_en",
            "chinese_abstract": "摘要B",
            "highlights": "h2",
            "html_url": "https://b",
        },
    ]
    card = build_card_from_papers(papers, "2024-01-01")

    elements: List[Dict[str, Any]] = card["elements"]
    intro_elem = elements[0]
    assert intro_elem["tag"] == "div"
    assert "2 篇相关论文" in intro_elem["text"]["content"]


def test_build_card_elements_tags() -> None:
    """Assert elements contain expected tags for a single paper."""
    papers: List[Dict[str, str]] = [
        {
            "chinese_title": "标题",
            "original_title": "Title",
            "chinese_abstract": "摘要",
            "highlights": "亮点",
            "html_url": "https://arxiv.org/html/1234",
        }
    ]
    card = build_card_from_papers(papers, "2024-01-01")
    tags = [e["tag"] for e in card["elements"]]

    assert "div" in tags
    assert "hr" in tags
    assert "note" in tags
    assert "action" in tags
