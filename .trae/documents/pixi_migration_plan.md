# Plan: Migrate Project Stack from Conda to Pixi

## Summary

Replace the project's dependency management and CI/CD stack from conda/pip to **pixi**.
This involves:
1. Fixing `pyproject.toml` pixi configuration issues.
2. Cleaning up `.gitignore` for pixi conventions.
3. Rewriting both GitHub Actions workflows to use `prefix-dev/setup-pixi`.
4. Updating `README.md` to reflect pixi installation, the finalized code standards (matching AGENTS.md), and removing stale references to `requirements.txt`.

## Current State Analysis

### `pyproject.toml`
- Already contains `[tool.pixi.*]` sections and a `pixi.lock` file exists, indicating a partial pixi adoption.
- **Issue 1**: Uses `[tool.pixi.workspace]` for a single project; `[tool.pixi.project]` is the idiomatic key.
- **Issue 2**: `pytest` is declared in **both** `[tool.pixi.dependencies]` (conda) and `[project.optional-dependencies]` test feature (PyPI). This is redundant and can cause resolution conflicts.
- **Issue 3**: `requires-python = ">=3.10"` but pixi pins `python = "3.12.*"`. While not a hard error, it is inconsistent.

### `.gitignore`
- Already contains pixi ignore rules at lines 120–125 (`.pixi`).
- **Issue**: Duplicated/fragmented pixi rules appear again at lines 228–230 (`.pixi/*`, `!.pixi/config.toml`). These should be consolidated into a single, clear block.

### GitHub Actions Workflows
- **`.github/workflows/test.yml`**: Uses `actions/setup-python@v5` + `pip install -e ".[test]"`. Needs to switch to `prefix-dev/setup-pixi@v2` + `pixi run --environment test pytest`.
- **`.github/workflows/arxiv-daily-paper-push.yml`**: Uses `actions/setup-python@v5` + `pip install -e .`. Needs to switch to `prefix-dev/setup-pixi@v2` + `pixi run python main.py`.

### `README.md`
- Still references `requirements.txt` (which no longer exists in the repo).
- Describes conda/pip installation steps.
- The "Code Contribution Guidelines" section uses **outdated** type annotation examples (`list[str]`, `dict[str, Any]`, `typing.Union`, `T | None`) that contradict the newly updated `AGENTS.md`.

## Proposed Changes

### Step 1: Fix `pyproject.toml`

**What**: Correct pixi configuration keys and remove duplicate dependency declarations.
**How**:
- Change `[tool.pixi.workspace]` → `[tool.pixi.project]`.
- Remove `pytest = ">=9.1.1,<10"` from `[tool.pixi.dependencies]` (it already lives in `[project.optional-dependencies]` and will be installed via PyPI in the test environment).
- Add `python = "3.12.*"` to `[tool.pixi.dependencies]` if not already present.
- Ensure `[tool.pixi.environments]` correctly maps `test` to the `test` feature.

**Resulting `[tool.pixi.*]` block should look like**:
```toml
[tool.pixi.project]
channels = ["conda-forge"]
platforms = ["linux-64"]

[tool.pixi.pypi-dependencies]
lark-arxivbot = { path = ".", editable = true }

[tool.pixi.environments]
default = { solve-group = "default" }
test = { features = ["test"], solve-group = "default" }

[tool.pixi.dependencies]
python = "3.12.*"
```

### Step 2: Clean `.gitignore`

**What**: Consolidate pixi-related ignore rules into one clear block.
**How**:
- Remove the scattered entries at lines 228–230.
- Keep (or move to a unified location) the standard pixi block:
  ```gitignore
  # pixi environments
  .pixi/
  ```
- Note: `pixi.lock` is **not** ignored (it is recommended to commit lock files for reproducibility).

### Step 3: Rewrite `.github/workflows/test.yml`

**What**: Use pixi for dependency installation and test execution.
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
      - uses: prefix-dev/setup-pixi@v2
        with:
          pixi-version: v0.39.0
          cache: true
      - name: Run tests
        run: pixi run --environment test pytest tests/ -v
```

### Step 4: Rewrite `.github/workflows/arxiv-daily-paper-push.yml`

**What**: Use pixi for dependency installation and bot execution.
**How**:
```yaml
name: arXiv Daily Paper Push

on:
  schedule:
    - cron: '30 1 * * *'
  workflow_dispatch:

jobs:
  push-papers:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: prefix-dev/setup-pixi@v2
        with:
          pixi-version: v0.39.0
          cache: true
      - name: Run arXiv bot
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          OPENAI_BASE_URL: ${{ secrets.OPENAI_BASE_URL }}
          OPENAI_MODEL: ${{ secrets.OPENAI_MODEL }}
          FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
          FEISHU_SECRET: ${{ secrets.FEISHU_SECRET }}
          MAX_PAPERS: ${{ secrets.MAX_PAPERS || '10' }}
        run: pixi run python main.py
```

### Step 5: Rewrite `README.md`

**What**: Update installation instructions, remove stale files, and align code contribution guidelines with `AGENTS.md`.
**How**:

#### A. Remove `requirements.txt` references
- In the "Quick Start" file tree example, replace `requirements.txt` with `pyproject.toml` and mention `pixi`.

#### B. Update Quick Start installation section
Replace the pip-based setup with pixi-based setup:
```markdown
#### 2. Install with Pixi

This project uses [pixi](https://pixi.sh) for reproducible
dependency management.

```bash
# Install pixi if you haven't already
curl -fsSL https://pixi.sh/install.sh | bash

# Install dependencies
pixi install

# Run tests
pixi run --environment test pytest tests/ -v

# Run the bot locally
pixi run python main.py
```
```

#### C. Update Code Contribution Guidelines
Replace the outdated type annotation section with examples that match `AGENTS.md`:
- Use `Dict`, `List`, `Optional` from `typing` in annotations.
- State: non-None unions use `T1 | T2`; nullable types use `Optional[T]`; never use `typing.Union`.
- Update the docstring example to use `Dict[str, str]` instead of `dict[str, str]`.

#### D. Update Deploy to Alibaba Cloud Function Compute section
Mention that the deployment package should be created via pixi (or note that `pyproject.toml` defines the dependencies).

## Assumptions & Decisions

1. **Pixi version**: We pin `setup-pixi` to `v0.39.0` (latest stable at time of writing) to avoid unexpected breaking changes from `latest`.
2. **Pixi lock file**: `pixi.lock` is already in the repo and should remain tracked (not ignored) for reproducible CI builds.
3. **Platform**: CI stays on `ubuntu-latest`, which matches the `linux-64` platform declared in `pyproject.toml`.
4. **Python version**: We align on Python 3.12 (the version already pinned in pixi config and the version used in tests).
5. **AGENTS.md is the source of truth**: README code examples must mirror the exact standards in `AGENTS.md`.

## Verification Steps

1. **pyproject.toml syntax check**:
   ```bash
   python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"
   ```
2. **Workflow YAML syntax check**:
   ```bash
   python -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml')); yaml.safe_load(open('.github/workflows/arxiv-daily-paper-push.yml'))"
   ```
3. **Import check** (after pixi install locally, or in CI):
   ```bash
   pixi run python -c "from lark_arxivbot.config import *; from lark_arxivbot.arxiv import *"
   ```
4. **Test suite** (in CI after the workflow rewrite):
   - Open a test PR and verify the `Tests` workflow passes with `prefix-dev/setup-pixi`.
5. **README consistency check**:
   - Confirm no mention of `requirements.txt`, `conda`, or `pip install` remains.
   - Confirm code examples use `List`, `Dict`, `Optional`.
