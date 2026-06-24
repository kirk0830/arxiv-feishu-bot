# Unify main.py and CLI Default Query Logic Plan

## Summary

`main.py` (Alibaba Cloud FC entry) and `cli.py` currently use different
default query logic. `cli.py` defaults to Boolean expressions
(`"molecular dynamics"&&("machine learning"||...)`) while `main.py`
falls back to `config.py` list defaults which become simple `OR`
queries. This inconsistency means the GitHub Actions / Alibaba Cloud
runs behave differently from local CLI runs.

## Current State Analysis

- `lark_arxivbot/config.py`:
  - `ARXIV_CATEGORIES: List[str] = ["physics.chem-ph", ...]`
  - `ARXIV_KEYWORDS: List[str] = ["molecular dynamics", ...]`
- `lark_arxivbot/cli.py`:
  - `--category` default: `'"physics.chem-ph"||"cond-mat.mtrl-sci"||"physics.comp-ph"'`
  - `--keyword` default: `'"molecular dynamics"&&("machine learning"||"deep learning"||"neural network")'`
- `lark_arxivbot/arxiv_fetcher.py`:
  - `fetch_papers_from_arxiv(..., categories=None, keywords=None, ...)`
  - When `None`, falls back to `ARXIV_CATEGORIES` / `ARXIV_KEYWORDS`
  - `_build_query` treats `List[str]` as `OR`, `str` as expression
- `main.py`:
  - Calls `run_daily_workflow()` with no arguments → falls back to config lists
- `tests/test_config.py`:
  - Asserts `ARXIV_CATEGORIES` and `ARXIV_KEYWORDS` are `List[str]`

## Proposed Changes

### File: `lark_arxivbot/config.py`

Convert the list constants to expression strings so that all callers
(main.py, cli.py, tests) use the same Boolean logic by default.

```python
ARXIV_CATEGORIES: str = (
    '"physics.chem-ph"||"cond-mat.mtrl-sci"||"physics.comp-ph"'
)

ARXIV_KEYWORDS: str = (
    '"molecular dynamics"&&'
    '("machine learning"||"deep learning"||"neural network")'
)
```

### File: `lark_arxivbot/cli.py`

Remove the local `_DEFAULT_CATEGORY_EXPR` / `_DEFAULT_KEYWORD_EXPR`
constants and import from `config.py` instead:

```python
from lark_arxivbot.config import (
    ARXIV_CATEGORIES,
    ARXIV_KEYWORDS,
)

parser.add_argument(
    "--category",
    default=ARXIV_CATEGORIES,
    ...
)
parser.add_argument(
    "--keyword",
    default=ARXIV_KEYWORDS,
    ...
)
```

### File: `lark_arxivbot/arxiv_fetcher.py`

Update the docstring of `fetch_papers_from_arxiv` to reflect that the
config defaults are now expression strings rather than lists.

### File: `tests/test_config.py`

Update the tests to assert the new type and content:

```python
def test_arxiv_categories_is_expression() -> None:
    """Assert ARXIV_CATEGORIES is a non-empty expression string."""
    assert isinstance(config_module.ARXIV_CATEGORIES, str)
    assert len(config_module.ARXIV_CATEGORIES) > 0
    assert "physics.chem-ph" in config_module.ARXIV_CATEGORIES


def test_arxiv_keywords_is_expression() -> None:
    """Assert ARXIV_KEYWORDS is a non-empty expression string."""
    assert isinstance(config_module.ARXIV_KEYWORDS, str)
    assert len(config_module.ARXIV_KEYWORDS) > 0
    assert "molecular dynamics" in config_module.ARXIV_KEYWORDS
```

## Assumptions & Decisions

- **Single source of truth**: Defaults live in `config.py` only. `cli.py` imports them, eliminating duplication.
- **Backward compatibility**: `fetch_papers_from_arxiv` still accepts `List[str]` for explicit callers; only the config defaults change to `str`.
- **Expression format**: Uses the same `"term"&&("term"||"term")` syntax already implemented in `_parse_expression`.

## Verification Steps

1. Run `pixi run --environment test pytest tests/test_config.py -v`.
2. Run `pixi run --environment test pytest tests/test_arxiv.py -v`.
3. Run `pixi run --environment test pytest tests/test_cli.py -v`.
4. Run `pixi run --environment test pytest tests/ -v` for full regression.
5. Run `pixi run python lark_arxivbot/cli.py --check-availability` to confirm the default query still works end-to-end.
