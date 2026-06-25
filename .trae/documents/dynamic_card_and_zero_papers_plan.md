# Plan: Dynamic Card Header & Zero-Paper Push

## Summary

Eliminate hard-coded text in Feishu cards and ensure the bot informs users even when zero papers are retrieved. Specifically:

1. Replace the hard-coded card title "计算物理日报" with "arXiv预印本日报" and display the actual `--category` / `--keyword` expressions in a grey, small-font note.
2. Remove the early-return logic that skips pushing when zero papers are found, so users see an explicit "0 papers" message instead of silence.

## Current State Analysis

### Files involved
- **[`lark_arxivbot/card.py`](file:///home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/card.py)** — Builds the Feishu interactive card payload. Currently hard-codes the header title (`📚 计算物理日报 | {date_label}`) and the scope line (`🔬 领域：计算物理 | ...`) inside the intro markdown.
- **[`lark_arxivbot/workflow.py`](file:///home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/workflow.py)** — Orchestrates fetch → summarise → build → push. Lines 77–79 skip the push entirely when `not papers`.
- **[`lark_arxivbot/cli.py`](file:///home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/cli.py)** — Already passes `args.category` and `args.keyword` (string expressions) into `run_daily_workflow`.
- **[`lark_arxivbot/config.py`](file:///home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/config.py)** — Contains the default string expressions `ARXIV_CATEGORIES` and `ARXIV_KEYWORDS`.
- **[`tests/test_card.py`](file:///home/huangyike/devel/arxiv-feishu-bot/tests/test_card.py)** — Tests card structure. Uses positional args only; adding defaults keeps existing tests green.

### Key observations
- Feishu `note` elements render with a grey background and smaller font by default, which satisfies the "grey, small font" requirement without needing custom colour attributes.
- `build_card_from_papers` already handles an empty `papers` list safely (the `for` loop simply adds no paper blocks), so no extra null-handling is needed there.
- `run_daily_workflow` may receive `None` for `categories`/`keywords` (e.g. from [`main.py`](file:///home/huangyike/devel/arxiv-feishu-bot/main.py)), so the actual display strings must fall back to `config.ARXIV_CATEGORIES` / `config.ARXIV_KEYWORDS`.

## Proposed Changes

### 1. [`lark_arxivbot/card.py`](file:///home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/card.py)

**What & Why:** Update `build_card_from_papers` signature to accept the raw query expressions, replace the hard-coded header and intro, and insert a `note` element for the query info.

**How:**
- Add `category: str = ""` and `keyword: str = ""` parameters.
- Change header `content` to `"📚 arXiv预印本日报 | {date_label}"`.
- Remove the hard-coded `🔬 领域：...` line from `intro`.
- After the first `hr`, insert a `note` element whose `plain_text` content is `"检索关键词：{category} | {keyword}"`.
- Keep the existing empty-list behaviour (loop body is skipped, only header + intro + note + footer remain).

### 2. [`lark_arxivbot/workflow.py`](file:///home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/workflow.py)

**What & Why:** Resolve display defaults, remove the zero-paper early return, and forward the query strings to the card builder.

**How:**
- Import `ARXIV_CATEGORIES` and `ARXIV_KEYWORDS` from `config`.
- At the top of `run_daily_workflow`, resolve:
  ```python
  display_category = categories if categories is not None else ARXIV_CATEGORIES
  display_keyword = keywords if keywords is not None else ARXIV_KEYWORDS
  ```
  If either is a `List`, join with `" | "` for display.
- Delete the `if not papers: logger.info(...); return` block (lines 77–79).
- Pass `category=str(display_category)` and `keyword=str(display_keyword)` to `build_card_from_papers`.

### 3. [`tests/test_card.py`](file:///home/huangyike/devel/arxiv-feishu-bot/tests/test_card.py)

**What & Why:** Cover the new parameters and the empty-papers scenario.

**How:**
- Add `test_build_card_with_query_info` — call with `category="...", keyword="..."` and assert the `note` element contains those expressions.
- Add `test_build_card_empty_papers` — call with `papers=[]` and assert the intro still says `"0 篇相关论文"` and the payload is valid.
- Existing tests remain unchanged because the new parameters have default values.

## Assumptions & Decisions

- **Grey/small font**: We use a Feishu `note` element. It is the standard, stable way to show auxiliary info in Feishu cards and renders in a subdued style.
- **No translation of expressions**: The raw Boolean expressions (e.g. `"physics.chem-ph"||"cond-mat.mtrl-sci"`) are displayed as-is, which is exactly what the user asked for.
- **List fallback formatting**: If `categories`/`keywords` is a list, join with `" | "`. This only affects legacy callers; the CLI always passes strings.
- **0-paper message**: When `papers` is empty, the card still contains the header, the intro stating `"今日共检索到 0 篇相关论文"`, the query `note`, and the footer, then it is pushed normally.

## Verification Steps

1. Run `pixi run pytest tests/test_card.py -v` — all old tests pass, new tests pass.
2. Run `pixi run lark-arxivbot --max-results 1 --days-back 0 --category '"nonexistent.category"' --keyword '"xyzabc123"'` (a query guaranteed to return 0 results) and verify the Feishu card is pushed showing "0 篇相关论文" and the query expressions.
