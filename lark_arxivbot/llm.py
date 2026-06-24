"""LLM-powered translation and summarization for paper abstracts."""

from __future__ import annotations

import logging
import os
from typing import Dict

from openai import OpenAI

logger = logging.getLogger(__name__)


def summarize_paper_via_llm(
    title: str,
    abstract: str,
) -> Dict[str, str]:
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

        lines = [
            line.strip() for line in content.split("\n") if line.strip()
        ]
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
