# Update README.md for CLI and New Features Plan

## Summary

The previous refactor added a `lark-arxivbot` CLI entry point, availability checks, and the `--channel` parameter, but the `README.md` was not updated to reflect these changes. This plan updates the documentation to keep it accurate and useful.

## Current State Analysis

- `README.md` does not mention the `lark-arxivbot` console script at all.
- The "Customizing Search Queries" section still tells users to "modify the `search_query` string in the `fetch_papers_from_arxiv()` function within `main.py`" — this is outdated because users can now pass `--field` and `--keywords` via CLI.
- The "Features" section does not mention the CLI, channel selection, or availability checks.
- The docstring example under "Docstring Style" returns `dict[str, str]` in the Returns section (line 316), which should be `Dict[str, str]` per AGENTS.md.

## Proposed Changes

### File: `/home/huangyike/devel/arxiv-feishu-bot/README.md`

**1. Update Features section**
- Add bullet points for:
  - **CLI Interface**: Run locally with `lark-arxivbot` and customize search via command-line arguments.
  - **Channel Selection**: Choose between the official arXiv library, the Atom API, or automatic fallback.
  - **Availability Checks**: Pre-flight checks for network, arXiv, and LLM health.

**2. Add a new "Local Usage via CLI" subsection under Usage**
Place it after "Install Dependencies with Pixi" and before "Configure Secrets". Include:
- How to run the default daily workflow: `pixi run lark-arxivbot`
- How to customize categories and keywords:
  ```bash
  pixi run lark-arxivbot \
    --field physics.chem-ph \
    --field cond-mat.mtrl-sci \
    --keywords "molecular dynamics" \
    --keywords "machine learning"
  ```
- How to choose a channel:
  ```bash
  pixi run lark-arxivbot --channel api
  pixi run lark-arxivbot --channel atom
  ```
- How to run availability checks:
  ```bash
  pixi run lark-arxivbot --check-availability
  pixi run lark-arxivbot --check-availability --no-exit-on-failed-check
  ```

**3. Update "Customizing Search Queries" section**
- Replace the outdated instruction ("modify the `search_query` string in `main.py`") with instructions to use the CLI `--field` and `--keywords` arguments.
- Keep the arXiv query syntax reference table as-is (it is still useful).
- Keep the example query modifications, but reframe them as CLI examples where appropriate.

**4. Fix the docstring example under "Docstring Style"**
- Line 316: Change `dict[str, str]` to `Dict[str, str]`.

## Verification Steps

1. Run `python3 -c "import tomllib; ..."` on `pyproject.toml` to ensure it remains valid (unaffected).
2. Confirm no broken markdown links or headings by reviewing the rendered preview if possible.
3. Ensure all new CLI examples fit within 79 characters where feasible, or use shell line continuations.
