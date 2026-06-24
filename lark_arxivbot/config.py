"""Centralized configuration and constants for lark_arxivbot."""

from __future__ import annotations

import os
from typing import Dict, List, Optional

# =============================================================================
# arXiv Categories
# =============================================================================

ARXIV_CATEGORIES: List[str] = [
    "physics.chem-ph",
    "cond-mat.mtrl-sci",
    "physics.comp-ph",
]

ARXIV_KEYWORDS: List[str] = [
    "molecular dynamics",
    "machine learning",
    "deep learning",
    "neural network",
]

# =============================================================================
# arXiv API Endpoints
# =============================================================================

ARXIV_API_ENDPOINTS: List[str] = [
    "https://cn.arxiv.org/api/query",
    "https://xxx.itp.ac.cn/api/query",
    "https://export.arxiv.org/api/query",
    "https://arxiv.org/api/query",
]

_CUSTOM_ENDPOINT: Optional[str] = os.environ.get("ARXIV_API_URL")
if _CUSTOM_ENDPOINT:
    ARXIV_API_ENDPOINTS.insert(0, _CUSTOM_ENDPOINT)

_ATOM_NS: Dict[str, str] = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}

# =============================================================================
# Defaults
# =============================================================================

DEFAULT_MAX_RESULTS: int = 50
DEFAULT_DAYS_BACK: int = 1
DEFAULT_MAX_PAPERS: int = 10
