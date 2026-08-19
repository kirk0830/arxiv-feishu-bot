"""LLM-powered translation and summarization for paper abstracts."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

_DEFAULT_MODEL: str = "gpt-4o"
_JSON_FORMAT: Dict[str, str] = {"type": "json_object"}
_FALLBACK_HIGHLIGHT: str = "总结生成中..."


def _call_chat_completion(
    client: OpenAI,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    use_json_mode: bool,
) -> str:
    """Call the chat completion API and return the response text."""
    kwargs: Dict[str, Any] = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }
    if use_json_mode:
        kwargs["response_format"] = _JSON_FORMAT

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()


def extract_json_dict_from_content(
    content: str,
) -> Optional[Dict[str, Any]]:
    """Extract a JSON object dictionary from raw LLM response text.

    Handles markdown code fences and prose surrounding the JSON object
    so partially non-conforming model output can still be recovered.

    Parameters
    ----------
    content : str
        Raw text returned by the LLM.

    Returns
    -------
    Optional[Dict[str, Any]]
        Parsed JSON object, or None if no valid object is found.
    """
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()

    try:
        parsed = json.loads(stripped, strict=False)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return parsed

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        candidate = stripped[start : end + 1]
        try:
            parsed = json.loads(candidate, strict=False)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def _render_highlights_text(highlights: Any) -> str:
    """Convert a highlights value from JSON into a display string."""
    if isinstance(highlights, list):
        items = [
            str(item).strip()
            for item in highlights
            if str(item).strip()
        ]
        if items:
            return "; ".join(items)
        return _FALLBACK_HIGHLIGHT
    if isinstance(highlights, str) and highlights.strip():
        return highlights.strip()
    return _FALLBACK_HIGHLIGHT


def parse_summary_from_content(
    content: str,
    fallback_title: str,
    fallback_abstract: str,
) -> Dict[str, str]:
    """Parse a structured summary from raw LLM response text.

    Tries JSON object extraction first, then pipe-delimited parsing,
    then newline-based parsing as a last resort.

    Parameters
    ----------
    content : str
        Raw text returned by the LLM.
    fallback_title : str
        Original title used when parsing cannot find a title.
    fallback_abstract : str
        Original abstract used when parsing cannot find an abstract.

    Returns
    -------
    Dict[str, str]
        Dictionary with keys: chinese_title, chinese_abstract, highlights.
    """
    parsed = extract_json_dict_from_content(content)
    if parsed:
        return {
            "chinese_title": str(
                parsed.get("chinese_title") or fallback_title
            ).strip(),
            "chinese_abstract": str(
                parsed.get("chinese_abstract") or fallback_abstract
            ).strip(),
            "highlights": _render_highlights_text(
                parsed.get("highlights")
            ),
        }

    parts = [part.strip() for part in content.split("|")]
    if len(parts) >= 3:
        return {
            "chinese_title": parts[0],
            "chinese_abstract": parts[1],
            "highlights": parts[2],
        }

    lines = [
        line.strip() for line in content.split("\n") if line.strip()
    ]
    return {
        "chinese_title": lines[0] if lines else fallback_title,
        "chinese_abstract": (
            "\n".join(lines[1:-1]) if len(lines) > 2 else fallback_abstract
        ),
        "highlights": (
            lines[-1] if len(lines) > 1 else _FALLBACK_HIGHLIGHT
        ),
    }


def summarize_paper_via_llm(
    title: str,
    abstract: str,
) -> Dict[str, str]:
    """Translate and summarize a paper abstract using an LLM.

    Uses standard terminology from computational chemistry and
    theoretical chemistry. Requests a strict JSON object so the
    three fields can be parsed reliably, and falls back to
    pipe-delimited or newline parsing when JSON is not available.

    Parameters
    ----------
    title : str
        Original English paper title.
    abstract : str
        Original English paper abstract.

    Returns
    -------
    Dict[str, str]
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

    client_kwargs: Dict[str, str] = {"api_key": api_key}
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
        "etc.\n"
        "6. Return only a single valid JSON object with exactly these "
        "keys: chinese_title (string), chinese_abstract (string), "
        "highlights (array of 3-5 strings). Do not add any text outside "
        "the JSON object."
    )

    user_prompt = (
        f"Paper Title: {title}\n\n"
        f"Paper Abstract: {abstract}\n\n"
        "Return the JSON object in this shape:\n"
        '{"chinese_title": "...", "chinese_abstract": "...", '
        '"highlights": ["...", "...", "..."]}'
    )

    model_name = model if model else _DEFAULT_MODEL
    try:
        content = _call_chat_completion(
            client, model_name, system_prompt, user_prompt, True
        )
    except Exception as first_error:
        logger.warning(
            f"JSON-mode LLM call failed, retrying without it: "
            f"{first_error}"
        )
        try:
            content = _call_chat_completion(
                client, model_name, system_prompt, user_prompt, False
            )
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return {
                "chinese_title": title,
                "chinese_abstract": abstract,
                "highlights": f"（LLM 翻译失败: {str(e)[:50]}）",
            }

    return parse_summary_from_content(content, title, abstract)
