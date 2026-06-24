# CLI Entry Point and Availability Checks Refactor Plan

## Summary

Add a console script entry point `lark-arxivbot` with CLI arguments for arXiv search fields, keywords, and retrieval channel. Introduce pre-flight availability checks for LLM, arXiv, and network. Refactor `fetch_papers_from_arxiv` to respect the `channel` parameter (api / atom / all) with strict failure handling for single-channel mode.

## Current State Analysis

- `main.py` in repo root defines `run_daily_workflow()` and `handler()`. `run_daily_workflow` accepts no parameters; all configuration comes from environment variables or `config.py` defaults.
- `lark_arxivbot/arxiv.py` defines `fetch_papers_from_arxiv(categories, keywords, max_results, days_back)` which always tries the official `arxiv` library first and silently falls back to the Atom API on any exception.
- `lark_arxivbot/llm.py` already has a graceful fallback: when `OPENAI_API_KEY` is missing or the API call raises, it returns the original English title/abstract.
- `lark_arxivbot/feishu.py` already returns `False` on push failure with detailed logging.
- `pyproject.toml` has no `[project.scripts]` section.
- No availability-check module exists.

## Proposed Changes

### 1. Add `[project.scripts]` to `pyproject.toml`

**File**: `/home/huangyike/devel/arxiv-feishu-bot/pyproject.toml`

Insert after `[project.optional-dependencies]`:

```toml
[project.scripts]
lark-arxivbot = "lark_arxivbot.cli:main"
```

### 2. Refactor `fetch_papers_from_arxiv` to Accept `channel`

**File**: `/home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/arxiv.py`

- Add parameter `channel: str = "all"` to `fetch_papers_from_arxiv`.
- When `channel == "api"`: call `_fetch_via_arxiv_lib`. On **any** exception, log the full error at `ERROR` level and return `[]`.
- When `channel == "atom"`: call `_fetch_via_atom_api`. On **any** exception, log the full error at `ERROR` level and return `[]`.
- When `channel == "all"`: preserve existing behavior (try library, fall back to Atom API on exception).

Update the docstring to document the new parameter.

### 3. Create `lark_arxivbot/availability.py`

**New file**: `/home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/availability.py`

Three check functions and one orchestrator:

```python
def check_network_availability() -> bool
def check_arxiv_availability(channel: str) -> bool
def check_llm_availability() -> bool
def run_availability_checks(channel: str) -> Dict[str, bool]
```

Implementation details:
- `check_network_availability`: reuse `diagnose_network_connectivity` logic (DNS + HTTP probe to at least one endpoint). Return `True` if any endpoint responds with HTTP 200.
- `check_arxiv_availability`: attempt a lightweight query (1 result, 1 day back) via the requested channel. Return `True` if papers are returned (empty list is acceptable; only exceptions count as failure).
- `check_llm_availability`: verify `OPENAI_API_KEY` is set. If `OPENAI_BASE_URL` is also set, optionally probe it with a `GET` (not an expensive chat completion).
- `run_availability_checks`: call the three checks in order (network → arxiv → llm). Log each result. Return a dict like `{"network": True, "arxiv": True, "llm": False}`.

### 4. Create `lark_arxivbot/cli.py`

**New file**: `/home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/cli.py`

Use `argparse` with the following arguments:

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--field` | `action="append"` | `None` | arXiv category; repeatable. Falls back to `config.ARXIV_CATEGORIES`. |
| `--keywords` | `action="append"` | `None` | Search keyword; repeatable. Falls back to `config.ARXIV_KEYWORDS`. |
| `--channel` | `choices=["api", "atom", "all"]` | `"all"` | Retrieval channel. |
| `--check-availability` | `action="store_true"` | `False` | Run pre-flight availability checks. |
| `--exit-on-failed-check` | `BooleanOptionalAction` | `True` | Exit immediately if any availability check fails. |
| `--max-results` | `int` | `DEFAULT_MAX_RESULTS` | Max results to request from arXiv. |
| `--days-back` | `int` | `DEFAULT_DAYS_BACK` | How many days back to search. |
| `--max-papers` | `int` | `DEFAULT_MAX_PAPERS` | How many papers to push. |

`main()` logic:
1. Parse args.
2. Call `setup_logging()`.
3. If `--check-availability`:
   - Run `run_availability_checks(args.channel)`.
   - If any check is `False` and `--exit-on-failed-check` is `True`, log critical error and call `sys.exit(1)`.
   - If `--exit-on-failed-check` is `False`, log warnings and continue.
4. Call `run_daily_workflow` with the parsed args.

### 5. Refactor `run_daily_workflow` in `main.py`

**File**: `/home/huangyike/devel/arxiv-feishu-bot/main.py`

Change signature to accept the same parameters as the CLI (all with defaults matching `config.py`). Pass them through to `fetch_papers_from_arxiv`.

```python
def run_daily_workflow(
    categories: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    channel: str = "all",
    max_results: int = DEFAULT_MAX_RESULTS,
    days_back: int = DEFAULT_DAYS_BACK,
    max_papers: int = DEFAULT_MAX_PAPERS,
) -> None:
```

Keep `handler()` unchanged in behavior: it calls `run_daily_workflow()` with no arguments (relying on defaults).

### 6. Update Tests

**File**: `/home/huangyike/devel/arxiv-feishu-bot/tests/test_arxiv.py`

Add tests for the new `channel` parameter:
- `test_fetch_papers_channel_api_success`
- `test_fetch_papers_channel_api_failure_returns_empty`
- `test_fetch_papers_channel_atom_success`
- `test_fetch_papers_channel_atom_failure_returns_empty`
- `test_fetch_papers_channel_all_fallback_still_works`

**New file**: `/home/huangyike/devel/arxiv-feishu-bot/tests/test_availability.py`

Add tests mocking `diagnose_network_connectivity`, `fetch_papers_from_arxiv`, and `os.environ`:
- `test_check_network_availability_true`
- `test_check_network_availability_false`
- `test_check_arxiv_availability_true`
- `test_check_arxiv_availability_false`
- `test_check_llm_availability_with_key`
- `test_check_llm_availability_without_key`
- `test_run_availability_checks_all_pass`
- `test_run_availability_checks_one_fail`

**New file**: `/home/huangyike/devel/arxiv-feishu-bot/tests/test_cli.py`

Add tests using `unittest.mock.patch` on `argparse.ArgumentParser.parse_args` and the workflow functions:
- `test_cli_defaults`
- `test_cli_check_availability_exits_on_failure`
- `test_cli_check_availability_continues_when_no_exit`
- `test_cli_passes_args_to_run_daily_workflow`

## Assumptions & Decisions

- **No `requirements.txt` reference**: The project uses `pixi` and `pyproject.toml`; no legacy pip requirements file will be created.
- **argparse over click/typer**: To avoid adding new dependencies, the CLI uses the standard library `argparse` module.
- **`--exit-on-failed-check` default is `True`**: Matches the user’s wording "报错退出 --exit-on-failed-check=true". Users who want downgrade behavior must explicitly pass `--no-exit-on-failed-check`.
- **Availability checks are lightweight**: `check_arxiv_availability` reuses `fetch_papers_from_arxiv` with `max_results=1` and `days_back=1`. `check_llm_availability` only checks the env var (and optionally the base URL), avoiding expensive LLM API calls during a health check.
- **`channel="all"` preserves current behavior**: This is the default both in the function signature and in the CLI, so existing GitHub Actions and Alibaba Cloud Function Compute deployments are unaffected.
- **Error-catching for LLM is already implemented**: No changes needed in `llm.py`; its existing fallback (return English content) satisfies the requirement.

## Verification Steps

1. Run `pixi run --environment test pytest tests/ -v` and confirm all old and new tests pass.
2. Verify `pyproject.toml` syntax with `python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"`.
3. Verify the script entry point resolves: `python3 -c "from lark_arxivbot.cli import main; print(main)"`.
4. Run `python3 -m lark_arxivbot.cli --help` (or after install, `lark-arxivbot --help`) and confirm all arguments appear.
5. Run `python3 -m lark_arxivbot.cli --check-availability` in an environment with valid secrets and confirm it either exits 0 or continues.
