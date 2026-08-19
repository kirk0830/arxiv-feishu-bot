"""Tests for lark_arxivbot.llm module."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock, patch

from lark_arxivbot.llm import summarize_paper_via_llm


def test_summarize_without_api_key(monkeypatch) -> None:
    """Assert fallback dict is returned when OPENAI_API_KEY is missing."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = summarize_paper_via_llm("Title", "Abstract")

    assert result["chinese_title"] == "Title"
    assert result["chinese_abstract"] == "Abstract"
    assert "未启用" in result["highlights"]


@patch("lark_arxivbot.llm.OpenAI")
def test_summarize_delimiter_parsing(
    mock_openai: MagicMock, monkeypatch
) -> None:
    """Assert correct parsing when LLM returns pipe-delimited output."""
    monkeypatch.setenv("OPENAI_API_KEY", "fake_key")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="中文标题|中文摘要|亮点1; 亮点2"))
    ]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    result = summarize_paper_via_llm("Title", "Abstract")

    assert result["chinese_title"] == "中文标题"
    assert result["chinese_abstract"] == "中文摘要"
    assert result["highlights"] == "亮点1; 亮点2"


@patch("lark_arxivbot.llm.OpenAI")
def test_summarize_json_parsing(
    mock_openai: MagicMock, monkeypatch
) -> None:
    """Assert JSON output is parsed and highlights list is joined."""
    monkeypatch.setenv("OPENAI_API_KEY", "fake_key")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content=(
                    '{"chinese_title": "中文标题", '
                    '"chinese_abstract": "中文摘要", '
                    '"highlights": ["亮点1", "亮点2", "亮点3"]}'
                )
            )
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    result = summarize_paper_via_llm("Title", "Abstract")

    assert result["chinese_title"] == "中文标题"
    assert result["chinese_abstract"] == "中文摘要"
    assert result["highlights"] == "亮点1; 亮点2; 亮点3"
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["response_format"] == {"type": "json_object"}


@patch("lark_arxivbot.llm.OpenAI")
def test_summarize_json_with_markdown_fence(
    mock_openai: MagicMock, monkeypatch
) -> None:
    """Assert JSON wrapped in a markdown code fence is still parsed."""
    monkeypatch.setenv("OPENAI_API_KEY", "fake_key")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content=(
                    "```json\n"
                    '{"chinese_title": "标题", '
                    '"chinese_abstract": "摘要", '
                    '"highlights": "单行亮点"}\n'
                    "```"
                )
            )
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    result = summarize_paper_via_llm("Title", "Abstract")

    assert result["chinese_title"] == "标题"
    assert result["chinese_abstract"] == "摘要"
    assert result["highlights"] == "单行亮点"


@patch("lark_arxivbot.llm.OpenAI")
def test_summarize_json_with_surrounding_prose(
    mock_openai: MagicMock, monkeypatch
) -> None:
    """Assert JSON embedded in prose is extracted from the response."""
    monkeypatch.setenv("OPENAI_API_KEY", "fake_key")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content=(
                    "Here is the summary:\n"
                    '{"chinese_title": "标题", '
                    '"chinese_abstract": "摘要", '
                    '"highlights": ["亮点"]}\n'
                    "Hope this helps."
                )
            )
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    result = summarize_paper_via_llm("Title", "Abstract")

    assert result["chinese_title"] == "标题"
    assert result["chinese_abstract"] == "摘要"
    assert result["highlights"] == "亮点"


@patch("lark_arxivbot.llm.OpenAI")
def test_summarize_retry_without_json_mode(
    mock_openai: MagicMock, monkeypatch
) -> None:
    """Assert a failed JSON-mode call retries without response_format."""
    monkeypatch.setenv("OPENAI_API_KEY", "fake_key")

    mock_client = MagicMock()
    fallback_response = MagicMock()
    fallback_response.choices = [
        MagicMock(message=MagicMock(content="中文标题|中文摘要|亮点"))
    ]
    mock_client.chat.completions.create.side_effect = [
        RuntimeError("response_format unsupported"),
        fallback_response,
    ]
    mock_openai.return_value = mock_client

    result = summarize_paper_via_llm("Title", "Abstract")

    assert result["chinese_title"] == "中文标题"
    assert result["chinese_abstract"] == "中文摘要"
    assert result["highlights"] == "亮点"
    assert mock_client.chat.completions.create.call_count == 2
    calls = mock_client.chat.completions.create.call_args_list
    assert calls[0].kwargs["response_format"] == {"type": "json_object"}
    assert "response_format" not in calls[1].kwargs


@patch("lark_arxivbot.llm.OpenAI")
def test_summarize_newline_fallback(
    mock_openai: MagicMock, monkeypatch
) -> None:
    """Assert fallback parsing works for newline-separated output."""
    monkeypatch.setenv("OPENAI_API_KEY", "fake_key")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="Line1\nLine2\nLine3\nLine4"
            )
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    result = summarize_paper_via_llm("Title", "Abstract")

    assert result["chinese_title"] == "Line1"
    assert result["chinese_abstract"] == "Line2\nLine3"
    assert result["highlights"] == "Line4"


@patch("lark_arxivbot.llm.OpenAI")
def test_summarize_exception_fallback(
    mock_openai: MagicMock, monkeypatch
) -> None:
    """Assert fallback dict on LLM exception includes error snippet."""
    monkeypatch.setenv("OPENAI_API_KEY", "fake_key")

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError(
        "connection refused"
    )
    mock_openai.return_value = mock_client

    result = summarize_paper_via_llm("Title", "Abstract")

    assert result["chinese_title"] == "Title"
    assert result["chinese_abstract"] == "Abstract"
    assert "翻译失败" in result["highlights"]
