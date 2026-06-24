# Rename arxiv.py to Resolve Package Name Collision Plan

## Summary

The file `lark_arxivbot/arxiv.py` shadows the installed `arxiv` Python package. When the code executes `import arxiv`, Python resolves it to the local module instead of the third-party library, causing `AttributeError: module 'arxiv' has no attribute 'Client'` at runtime.

## Current State Analysis

- `lark_arxivbot/arxiv.py` contains our paper-retrieval logic and also imports the official `arxiv` library with `import arxiv` (line 12).
- Because the module name (`arxiv`) is identical to the package name, Python's import system loads our module first.
- This breaks `_fetch_via_arxiv_lib`, which tries to instantiate `arxiv.Client`.
- 22 references to `lark_arxivbot.arxiv` exist across source files, test files, and documentation.

## Proposed Changes

### Step 1: Rename the module file
- `lark_arxivbot/arxiv.py` → `lark_arxivbot/arxiv_fetcher.py`

### Step 2: Update imports in source files
- `lark_arxivbot/cli.py`: `from lark_arxivbot.arxiv import ...` → `from lark_arxivbot.arxiv_fetcher import ...`
- `lark_arxivbot/availability.py`: same change
- `lark_arxivbot/workflow.py`: same change
- `lark_arxivbot/main.py`: same change

### Step 3: Update tests
- `tests/test_arxiv.py`:
  - Module docstring and all `from lark_arxivbot.arxiv import ...` → `from lark_arxivbot.arxiv_fetcher import ...`
  - All `@patch("lark_arxivbot.arxiv...")` → `@patch("lark_arxivbot.arxiv_fetcher...")`
- `tests/test_availability.py`: patch paths already target `lark_arxivbot.availability.*`, so no changes needed.
- `tests/test_cli.py`: patch paths already target `lark_arxivbot.cli.*` or `lark_arxivbot.availability.*`, so no changes needed.

### Step 4: Delete the old file
- Remove `lark_arxivbot/arxiv.py` after the rename.

## Assumptions & Decisions

- **New name `arxiv_fetcher.py`**: Chosen because it clearly describes the module's purpose and cannot collide with the `arxiv` package.
- **No test file rename**: `tests/test_arxiv.py` can stay as-is; only its imports and patches need updating.

## Verification Steps

1. Run `pixi run python lark_arxivbot/cli.py` and confirm the run completes without the `module 'arxiv' has no attribute 'Client'` warning.
2. Run `pixi run --environment test pytest tests/ -v` and confirm all tests pass.
