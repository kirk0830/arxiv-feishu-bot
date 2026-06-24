"""Feishu interactive card builder for paper digests."""

from __future__ import annotations

from typing import Any, Dict, List


def build_card_from_papers(
    papers: List[Dict[str, str]],
    date_label: str,
) -> Dict[str, Any]:
    """Build a Feishu interactive card from a list of paper dictionaries.

    Parameters
    ----------
    papers : List[Dict[str, str]]
        List of paper dictionaries containing chinese_title,
        original_title, chinese_abstract, highlights, and html_url.
    date_label : str
        Human-readable date string for the card header.

    Returns
    -------
    Dict[str, Any]
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

    elements: List[Dict[str, Any]] = [
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
