# Refactor Plan: arXiv-Feishu Bot

## Summary

This plan refactors the monolithic `main.py` into a maintainable Python package (`lark_arxivbot`), introduces `pyproject.toml` for dependency management, integrates the official `arxiv` library as the primary fetching backend with Atom API fallback, exposes parameterized search interfaces, and improves logging infrastructure. All changes must strictly follow `AGENTS.md` coding standards.

## Current State Analysis

### File Structure
```
.
├── main.py                          # Monolithic: Feishu + Atom API + LLM + Card + Orchestration
├── with_arxiv_api.py                # Standalone alternative using official arxiv library
├── requirements.txt                 # Only requests, openai (missing arxiv, version loose)
├── .github/workflows/arxiv-daily-paper-push.yml  # Hard-coded pip install
├── AGENTS.md                        # Mandatory coding standards
└── README.md
```

### Identified Issues
1. **No `pyproject.toml`**: Dependencies are manually installed in CI; no installable package metadata.
2. **Monolithic `main.py`**: Feishu utilities, arXiv fetching, LLM summarization, card building, and orchestration all coexist in one file (~650 lines).
3. **Hard-coded search scope**: `fetch_papers_from_arxiv()` has no parameters; categories, keywords, and date range are baked into the function body.
4. **Basic logging**: Only a root `StreamHandler` with `INFO` level; no environment-level control, no structured formatting, no file rotation.
5. **Two separate arXiv implementations**: `main.py` uses Atom XML API with endpoint fallback; `with_arxiv_api.py` uses the official `arxiv` library. They are not unified.
6. **CI drift**: Workflow installs packages manually instead of using project metadata.

## Proposed Changes

### Step 1: Create `pyproject.toml`
**File**: `/home/huangyike/devel/arxiv-feishu-bot/pyproject.toml`

**What**: Define PEP 518/621 project metadata and dependencies.
**Why**: Enables `pip install -e .`, locks dependency declarations, and removes hard-coded `pip install` lines from CI.
**How**:
- `name = "arxiv-feishu-bot"`
- `version = "0.1.0"`
- `requires-python = ">=3.10"`
- Dependencies: `requests>=2.31.0`, `openai>=1.0.0`, `arxiv>=2.0.0`
- Optional: add `[project.scripts]` if desired (not strictly necessary since entry point remains `main.py`).

### Step 2: Restructure into `lark_arxivbot` Package
**Files to create**:
- `lark_arxivbot/__init__.py`
- `lark_arxivbot/config.py`
- `lark_arxivbot/logging_config.py`
- `lark_arxivbot/feishu.py`
- `lark_arxivbot/card.py`
- `lark_arxivbot/llm.py`
- `lark_arxivbot/arxiv.py`

**Files to modify**:
- `main.py` (shrink to thin orchestration entry point)
- `.gitignore` (add `*.log` if not present)

#### 2.1 `lark_arxivbot/config.py`
**What**: Centralize constants and environment-driven configuration defaults.
**Why**: Avoids duplication and makes customization discoverable.
**How**:
- Move `ARXIV_API_ENDPOINTS`, `_CUSTOM_ENDPOINT`, `_ATOM_NS` from `main.py`.
- Move `ARXIV_CATEGORIES`, `ARXIV_KEYWORDS` from `with_arxiv_api.py`.
- Add `DEFAULT_MAX_RESULTS: int = 50`, `DEFAULT_DAYS_BACK: int = 1`, `DEFAULT_MAX_PAPERS: int = 10`.
- Expose helper `load_env_or_default(key: str, default: str) -> str` if needed.

#### 2.2 `lark_arxivbot/logging_config.py`
**What**: Provide a reusable function `setup_logging()` that configures the `logging` system.
**Why**: Replaces ad-hoc `logging.basicConfig` in `main.py` and supports runtime tuning.
**How**:
- Function signature: `def setup_logging(level: str | None = None) -> None`.
- Read `LOG_LEVEL` env var (fallback to `INFO`).
- Create a `logging.Formatter` with `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`.
- Attach a `logging.StreamHandler` to the root logger.
- Optionally attach a `logging.handlers.RotatingFileHandler("lark_arxivbot.log", maxBytes=5*1024*1024, backupCount=3)` if the filesystem is writable; catch `OSError` silently to avoid crashing in read-only environments (e.g., Function Compute).
- Set root logger level and return.

#### 2.3 `lark_arxivbot/feishu.py`
**What**: Extract Feishu webhook utilities.
**Why**: Single responsibility; reusable and testable.
**How**:
- Move `generate_feishu_signature` and `push_card_to_feishu` from `main.py`.
- Keep exact logic, docstrings updated to NumPy style if needed.
- Import `logger` from `lark_arxivbot.logging_config` or use module-level `logging.getLogger(__name__)`.

#### 2.4 `lark_arxivbot/card.py`
**What**: Extract interactive card builder.
**Why**: UI payload construction is independent of networking or fetching.
**How**:
- Move `build_card_from_papers` from `main.py`.
- Use the same `dict[str, Any]` return type.

#### 2.5 `lark_arxivbot/llm.py`
**What**: Extract LLM summarization.
**Why**: Isolates OpenAI dependency and prompt engineering.
**How**:
- Move `summarize_paper_via_llm` from `main.py`.
- Keep prompt text identical to preserve behavior.

#### 2.6 `lark_arxivbot/arxiv.py`
**What**: Unified arXiv paper fetcher with official-library-first + Atom-API-fallback.
**Why**: Addresses the dual-implementation problem; official library provides automatic retries and rate limiting, while Atom API fallback preserves multi-endpoint resilience.
**How**:
- Define public function:
  ```python
  def fetch_papers_from_arxiv(
      categories: list[str] | None = None,
      keywords: list[str] | None = None,
      max_results: int = 50,
      days_back: int = 1,
  ) -> list[dict[str, str]]:
  ```
  - Defaults come from `config.ARXIV_CATEGORIES` and `config.ARXIV_KEYWORDS` when `None`.
- **Primary path**: Use official `arxiv` library (`arxiv.Client`, `arxiv.Search`) exactly as demonstrated in `with_arxiv_api.py`.
  - Build query string from `categories` and `keywords`.
  - Filter results to `published_date >= target_date`.
- **Fallback path**: If the official library path raises an exception (e.g., network, parsing), log a warning and fall back to the Atom API logic extracted from `main.py`.
  - Try endpoints in `config.ARXIV_API_ENDPOINTS` order.
  - Use `requests` + `xml.etree.ElementTree`.
- Both paths return the same `list[dict[str, str]]` shape with keys:
  `original_title`, `abstract`, `html_url`, `pdf_url`, `authors`, `published`, `arxiv_id`.
- Move `diagnose_network_connectivity` into this module as a private or public utility, since it tests arXiv endpoints.

#### 2.7 `main.py` (Refactored Entry Point)
**What**: Thin orchestration layer.
**Why**: Entry point should only wire modules together.
**How**:
- Imports:
  ```python
  from lark_arxivbot.logging_config import setup_logging
  from lark_arxivbot.config import DEFAULT_MAX_PAPERS
  from lark_arxivbot.arxiv import fetch_papers_from_arxiv
  from lark_arxivbot.llm import summarize_paper_via_llm
  from lark_arxivbot.card import build_card_from_papers
  from lark_arxivbot.feishu import push_card_to_feishu
  ```
- `run_daily_workflow()`:
  1. Call `setup_logging()`.
  2. Optional network diagnostics (read `ENABLE_NETWORK_DIAG`).
  3. Call `fetch_papers_from_arxiv()` with no args (uses defaults).
  4. Slice with `MAX_PAPERS`.
  5. Summarize via list comprehension + `|` merge.
  6. Build card and push.
- Keep `handler(event, context)` for Alibaba Cloud Function Compute compatibility.

### Step 3: Update GitHub Actions Workflow
**File**: `.github/workflows/arxiv-daily-paper-push.yml`

**What**: Replace manual `pip install requests openai` with project-based install.
**Why**: Centralizes dependency declarations in `pyproject.toml`.
**How**:
```yaml
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
```

### Step 4: Update `.gitignore`
**File**: `.gitignore`

**What**: Ensure build artifacts and local logs are ignored.
**Why**: Clean working tree after package builds.
**How**: Append `*.log` and `lark_arxivbot.egg-info/` if not already covered.

### Step 5: Delete `with_arxiv_api.py`
**File**: `with_arxiv_api.py`

**What**: Remove the standalone alternative file after its logic is merged into `lark_arxivbot/arxiv.py`.
**Why**: Avoids duplication and confusion.
**How**: Delete after confirming `lark_arxivbot/arxiv.py` contains the equivalent primary path.

### Step 6: Update `requirements.txt` (Optional but Recommended)
**File**: `requirements.txt`

**What**: Keep it in sync with `pyproject.toml` or replace with a note.
**Why**: Some users may still expect `requirements.txt`.
**How**: Add `arxiv>=2.0.0` to the existing list. Alternatively, leave a comment pointing to `pyproject.toml`.

## Assumptions & Decisions

1. **Python 3.10+**: The workflow and README already target 3.10; we keep this minimum.
2. **Official arxiv library as primary**: Chosen because it handles rate limiting and retries. Atom API remains as fallback for environments where the library might fail or for endpoint diversity.
3. **No behavior change for end users**: Default categories/keywords remain the same; default card template remains the same.
4. **Alibaba Cloud Function Compute compatibility**: `handler` signature and response shape are preserved.
5. **No test suite added**: Out of scope for this refactor; focus is on packaging and modularity.
6. **Environment isolation**: Since `conda` is unavailable, local verification should use `python -m venv .venv`.

## Verification Steps

1. **Structure check**:
   ```bash
   python -c "from lark_arxivbot.arxiv import fetch_papers_from_arxiv; print('OK')"
   ```
2. **Install check**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   python -c "import lark_arxivbot; print(lark_arxivbot)"
   ```
3. **Entry point dry-run** (without secrets, should gracefully handle missing env vars):
   ```bash
   LOG_LEVEL=DEBUG python main.py
   ```
   Expect: logs show initialization, arXIV fetch attempt, no unhandled exceptions.
4. **Lint/format alignment with AGENTS.md**:
   - No line exceeds 79 characters.
   - All functions follow `verb_owner_noun`.
   - All public functions have NumPy-style docstrings in English.
   - No bare `except`.
