# Plan: Standardize Type Hints to typing Generics and Add pytest Suite

## Summary

This plan addresses two distinct tasks:
1. **Normalize all type annotations** to use capitalized `typing` generics (e.g., `List`, `Dict`, `Optional`) for annotations while keeping lowercase builtins (`list`, `dict`) for instantiation. Update `AGENTS.md` to codify this rule.
2. **Add a comprehensive pytest test suite** with mocked external network calls (arxiv library, requests, OpenAI) to avoid hitting real APIs during CI. Add a GitHub Actions workflow that runs on every Pull Request.

## Current State Analysis

### Type Annotation Inventory (needs migration)
All source files currently use PEP 585 built-in generics (`list[str]`, `dict[str, Any]`) and PEP 604 union (`str | None`). The user mandates switching to `typing.List`, `typing.Dict`, `typing.Optional`, etc., for annotations. For nullable types, always use `Optional[T]` instead of `T | None`. For non-None unions, use `T1 | T2`. Never use `typing.Union`.

| File | Patterns to change |
|------|-------------------|
| `lark_arxivbot/config.py` | `list[str]` (4), `str \| None` (1), `dict[str, str]` (1) |
| `lark_arxivbot/logging_config.py` | `str \| None` (1) |
| `lark_arxivbot/feishu.py` | `dict[str, Any]` (3) |
| `lark_arxivbot/card.py` | `list[dict[str, str]]` (1), `dict[str, Any]` (many) |
| `lark_arxivbot/llm.py` | `dict[str, str]` (many), `dict[str, str]` annotations |
| `lark_arxivbot/arxiv.py` | `dict[str, str]` (many), `list[dict[str, str]]` (many), `list[str] \| None` (2), `Exception \| None`, `requests.Response \| None` |
| `main.py` | `dict[str, Any]` (1) |
| `AGENTS.md` | All code examples and section 2.2 / 2.3 / 2.4 / checklist |

### Testing State
- No test directory exists.
- No test dependencies in `pyproject.toml`.
- No CI workflow for PR validation.
- Running `main.py` directly hits real arXiv endpoints, which risks rate-limiting (HTTP 429) and IP blacklisting.

## Proposed Changes

### Part A: Type Hint Migration

#### Step A1: Update `lark_arxivbot/config.py`
**What**: Replace all built-in generics with `typing` equivalents.
**How**:
- Add imports: `from typing import Dict, List, Optional`
- `ARXIV_CATEGORIES: list[str]` → `ARXIV_CATEGORIES: List[str]`
- `ARXIV_KEYWORDS: list[str]` → `ARXIV_KEYWORDS: List[str]`
- `ARXIV_API_ENDPOINTS: list[str]` → `ARXIV_API_ENDPOINTS: List[str]`
- `_CUSTOM_ENDPOINT: str | None` → `_CUSTOM_ENDPOINT: Optional[str]`
- `_ATOM_NS: dict[str, str]` → `_ATOM_NS: Dict[str, str]`
- Keep instantiation lowercase (no `list()` / `dict()` changes needed here).

#### Step A2: Update `lark_arxivbot/logging_config.py`
**What**: Migrate the single nullable union type to `Optional`.
**How**:
- Add import: `from typing import Optional`
- `def setup_logging(level: str | None = None)` → `def setup_logging(level: Optional[str] = None)`
- Rationale: always use `Optional[T]` for `T | None`; never leave bare `| None` in annotations.

#### Step A3: Update `lark_arxivbot/feishu.py`
**What**: Migrate `dict[str, Any]` annotations.
**How**:
- Add import: `from typing import Any, Dict`
- Update parameter and return types in `push_card_to_feishu` and `generate_feishu_signature` docstrings.

#### Step A4: Update `lark_arxivbot/card.py`
**What**: Migrate all `list`/`dict` annotations.
**How**:
- Add imports: `from typing import Any, Dict, List`
- `papers: list[dict[str, str]]` → `papers: List[Dict[str, str]]`
- `elements: list[dict[str, Any]]` → `elements: List[Dict[str, Any]]`
- Return type `dict[str, Any]` → `Dict[str, Any]`
- Docstring types updated accordingly.

#### Step A5: Update `lark_arxivbot/llm.py`
**What**: Migrate `dict[str, str]` annotations.
**How**:
- Add imports: `from typing import Dict, List` (if needed)
- `-> dict[str, str]` → `-> Dict[str, str]`
- `client_kwargs: dict[str, str]` → `client_kwargs: Dict[str, str]`
- `lines = [ ... ]` stays lowercase instantiation.

#### Step A6: Update `lark_arxivbot/arxiv.py`
**What**: Heaviest migration — many nested generics and unions.
**How**:
- Add imports: `from typing import Any, Dict, List, Optional`
- `-> dict[str, str]` → `-> Dict[str, str]` (everywhere)
- `-> list[dict[str, str]]` → `-> List[Dict[str, str]]` (everywhere)
- `Exception | None` → `Optional[Exception]`
- `requests.Response | None` → `Optional[requests.Response]`
- `list[str] | None` in `fetch_papers_from_arxiv` params → `Optional[List[str]]`
- Docstrings updated to use `List[...]`, `Dict[...]`, `Optional[...]`.

#### Step A7: Update `main.py`
**What**: Migrate remaining annotations.
**How**:
- Add imports: `from typing import Any, Dict`
- `-> dict[str, Any]` → `-> Dict[str, Any]`

#### Step A8: Update `AGENTS.md`
**What**: Rewrite type-annotation sections to mandate `typing` generics.
**How**:
- **Section 2.2** (Union Types):
  - "Use `T1 | T2` for multi-type unions (non-None)."
  - "Use `Optional[T]` for `T | None` only."
  - "Never use `Union[T1, T2]` — it harms readability."
  - Update code examples.
- **Section 2.3** (Optional Types): Consolidate into `Optional[T]` style only.
- **Section 2.4** (Generics): Replace `list[dict[str, str]]` examples with `List[Dict[str, str]]`.
- **Section 2.5** (Variable Type Hints): Same migration.
- **Section 1.5** / **Section 3.1** / **Section 9** (Example function): Update all annotations in the example.
- **Checklist (Section 8)**: Change to: "Non-None unions use `T1 | T2` (never `Union[...]`); nullable types use `Optional[T]` (never `T | None`); built-in generics are not used in annotations."

### Part B: Test Suite & CI

#### Step B1: Add pytest to `pyproject.toml`
**What**: Declare test dependencies.
**How**:
- Add `[project.optional-dependencies]` block:
  ```toml
  [project.optional-dependencies]
  test = [
      "pytest>=7.0.0",
      "pytest-mock>=3.10.0",
  ]
  ```

#### Step B2: Create `tests/__init__.py`
**What**: Make `tests` a package.
**How**: Empty file.

#### Step B3: Create `tests/test_config.py`
**What**: Verify constants and env-var logic.
**How**:
- Test `ARXIV_CATEGORIES` is a non-empty `List[str]`.
- Test `DEFAULT_MAX_RESULTS` / `DEFAULT_DAYS_BACK` values.
- Test `_CUSTOM_ENDPOINT` is injected when `ARXIV_API_URL` env var is set.

#### Step B4: Create `tests/test_logging_config.py`
**What**: Verify `setup_logging` behavior.
**How**:
- Call `setup_logging("DEBUG")` and assert root logger level is `logging.DEBUG`.
- Assert a `StreamHandler` is attached.
- Call again and assert no duplicate handlers.

#### Step B5: Create `tests/test_feishu.py`
**What**: Verify signature generation and webhook payload.
**How**:
- Test `generate_feishu_signature` with known secret/timestamp produces expected Base64 HMAC.
- Monkeypatch `FEISHU_WEBHOOK_URL` and mock `requests.post` to verify payload structure in `push_card_to_feishu`.
- Test missing webhook URL returns `False`.

#### Step B6: Create `tests/test_card.py`
**What**: Verify card payload structure.
**How**:
- Build a card with 2 fake papers and assert:
  - `header["title"]["content"]` contains the date label.
  - `elements` list contains the expected tags (`div`, `hr`, `action`, `note`).
  - Paper count appears in intro text.

#### Step B7: Create `tests/test_llm.py`
**What**: Verify LLM summarization logic without calling OpenAI.
**How**:
- Mock `os.environ.get` so `OPENAI_API_KEY` is missing → assert fallback dict is returned.
- Mock `os.environ.get` with a dummy key, patch `openai.OpenAI.chat.completions.create` to return a deterministic response, then assert parsed output.
- Test delimiter parsing (` | `) and newline fallback parsing.

#### Step B8: Create `tests/test_arxiv.py`
**What**: Verify arXiv fetching without real network calls.
**How**:
- **Mock official library path**: Patch `arxiv.Client` and `arxiv.Search`. Create a mock `Result` object with `.title`, `.summary`, `.published`, `.entry_id`, `.pdf_url`, `.authors`. Assert `_fetch_via_arxiv_lib` returns correctly shaped `List[Dict[str, str]]`.
- **Mock Atom API path**: Patch `requests.get` to return a mocked `Response` with realistic Atom XML. Assert `_fetch_via_atom_api` parses papers correctly.
- **Test fallback**: Patch `arxiv.Client.results` to raise `Exception`, assert `fetch_papers_from_arxiv` falls back to Atom API.
- **Test empty results**: Both paths return `[]` when no entries match.
- **Test network diagnostics**: Patch `socket.gethostbyname` and `requests.get` to assert `diagnose_network_connectivity` returns the expected `Dict[str, str]` shape.

#### Step B9: Create `.github/workflows/test.yml`
**What**: PR-gated CI that runs the pytest suite.
**How**:
```yaml
name: Tests

on:
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: |
          python -m pip install --upgrade pip
          pip install -e ".[test]"
      - run: pytest tests/ -v
```

#### Step B10: Update `.gitignore`
**What**: Ignore pytest cache.
**How**: Append `.pytest_cache/` (if not already present).

## Assumptions & Decisions

1. **`typing.Any` stays as-is** — user explicitly said they do not object to `Any`.
2. **Instantiation stays lowercase** — `list()`, `dict()`, `set()` remain unchanged; only annotations change.
3. **Nullable types must use `Optional[T]`** — never use `T | None`. Non-None unions use `T1 | T2`. `typing.Union` is prohibited entirely for readability.
4. **pytest + pytest-mock** chosen over unittest — more concise, better mock patching ergonomics.
5. **Branch protection enforcement** (blocking merge on failing tests) is a GitHub repository setting outside the scope of file changes; the workflow itself only runs tests and reports status.
6. **All tests mock external I/O** — no real HTTP requests to arXiv, OpenAI, or Feishu during CI.

## Verification Steps

1. **Type-check compilation**:
   ```bash
   python -m py_compile lark_arxivbot/*.py main.py
   ```
2. **Import check**:
   ```bash
   python -c "from lark_arxivbot.config import *; from lark_arxivbot.arxiv import *; ..."
   ```
3. **Run test suite**:
   ```bash
   pip install -e ".[test]"
   pytest tests/ -v
   ```
   Expected: all tests pass, no real network traffic.
4. **AGENTS.md review**: Confirm all code examples use `List`, `Dict`, `Optional`; non-None unions use `T1 | T2`; `Union[...]` and `| None` are absent.
