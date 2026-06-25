# Plan: Update Delimiter Tests & Add Model Name to Card Footer

## Summary

1. Synchronize the LLM system prompt and tests with the new `^|` delimiter that the user already adopted in `lark_arxivbot/llm.py`.
2. Display the LLM model name (read from the `OPENAI_MODEL` environment variable) in the Feishu card footer.

## Current State Analysis

### Files involved
- **[`lark_arxivbot/llm.py`](file:///home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/llm.py)** — User already changed the user prompt and the `split` call to use `^|`, but line 71 (`system_prompt`) still tells the model to use `|` as the delimiter. This inconsistency can confuse the LLM.
- **[`tests/test_llm.py`](file:///home/huangyike/devel/arxiv-feishu-bot/tests/test_llm.py)** — `test_summarize_delimiter_parsing` mocks an LLM response with the old ` | ` delimiter (`"中文标题 | 中文摘要 | 亮点1; 亮点2"`). The test will now fail because the production code splits on `^|`.
- **[`lark_arxivbot/workflow.py`](file:///home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/workflow.py)** — Builds the card but does not pass the model name to the card builder.
- **[`lark_arxivbot/card.py`](file:///home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/card.py)** — The footer `note` currently shows `"数据来源：arXiv | 翻译总结：AI 辅助生成 | 仅供参考"`. No parameter exists for the model name.
- **[`tests/test_card.py`](file:///home/huangyike/devel/arxiv-feishu-bot/tests/test_card.py)** — No test currently asserts the footer text, so existing tests remain green after the signature change as long as defaults are provided.

## Proposed Changes

### 1. [`lark_arxivbot/llm.py`](file:///home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/llm.py)

**What & Why:** Align the system prompt with the user prompt so the LLM is consistently instructed to use `^|`.

**How:** Change line 71 from `"6. Output format must strictly use | as delimiter."` to `"6. Output format must strictly use ^| as delimiter."`.

### 2. [`tests/test_llm.py`](file:///home/huangyike/devel/arxiv-feishu-bot/tests/test_llm.py)

**What & Why:** Update the mock LLM response in `test_summarize_delimiter_parsing` to use the new `^|` delimiter.

**How:** Replace the mock `message.content` string with `"中文标题^|中文摘要^|亮点1; 亮点2"`. Keep the assertions unchanged (they already expect the three parts to be parsed correctly).

### 3. [`lark_arxivbot/workflow.py`](file:///home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/workflow.py)

**What & Why:** Read the model name from the environment and forward it to the card builder.

**How:** Before building the card, resolve:
```python
model_name = os.environ.get("OPENAI_MODEL", "gpt-4o")
```
Pass `model_name=model_name` to `build_card_from_papers(...)`.

### 4. [`lark_arxivbot/card.py`](file:///home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/card.py)

**What & Why:** Accept the model name and render it in the footer.

**How:**
- Add `model_name: str = ""` to the function signature.
- Append `" | 模型：{model_name}"` to the footer `note` content when `model_name` is non-empty. If empty, keep the original footer text unchanged.

### 5. [`tests/test_card.py`](file:///home/huangyike/devel/arxiv-feishu-bot/tests/test_card.py)

**What & Why:** Verify the model name appears in the footer when supplied.

**How:** Add `test_build_card_shows_model_name` — call `build_card_from_papers(..., model_name="gpt-4o")` and assert the last `note` element contains `"模型：gpt-4o"`.

## Assumptions & Decisions

- **Default model name**: If `OPENAI_MODEL` is unset, we display `gpt-4o`, which matches the fallback already used inside `summarize_paper_via_llm`.
- **Delimiter in tests**: The old ` | ` delimiter is no longer supported; the test must exactly match the new `^|` separator.
- **Empty model safe-guard**: If `model_name` is an empty string (unlikely but possible), the footer omits the model clause to avoid trailing punctuation.

## Verification Steps

1. Run `pixi run --environment test pytest tests/test_llm.py -v` — all 4 tests pass.
2. Run `pixi run --environment test pytest tests/test_card.py -v` — all 6 tests pass.
3. Run the full suite `pixi run --environment test pytest tests/ -v` — 51+ tests pass.
