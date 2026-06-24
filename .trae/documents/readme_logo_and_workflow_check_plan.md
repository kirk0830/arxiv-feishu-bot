# Plan: Check README.md, Logo, and Workflow Consistency

## Summary

Verify that README.md is properly updated with the project logo, and that the GitHub Actions workflow invocation matches the CLI usage documented in README.md. Fix any inconsistencies found.

## Current State Analysis

### Already Correct
1. **Logo in README.md**: Line 3 contains `<img src="docs/assets/arxivbot-logo.png" alt="arXiv Bot Logo" width="200">`.
2. **CLI documentation**: README.md documents `pixi run lark-arxivbot` as the recommended invocation.
3. **Workflow run command**: `.github/workflows/arxiv-daily-paper-push.yml` line 26 uses `run: pixi run lark-arxivbot`, matching README.
4. **pyproject.toml script entry**: Line 25 correctly declares `lark-arxivbot = "lark_arxivbot.cli:main"`.

### Issues Found
1. **Duplicate section numbering in README.md**:
   - Line 143: `#### 4. Configure Secrets`
   - Line 158: `#### 4. Trigger the Workflow` (should be `#### 5.`)
   - Line 164: `#### 5. Verify in Feishu` (should be `#### 6.`)

2. **Incorrect schedule time in README.md**:
   - Line 162 says: "09:30 Beijing Time (01:30 UTC)"
   - `.github/workflows/arxiv-daily-paper-push.yml` line 6 uses `37 1 * * *` (01:37 UTC = 09:37 Beijing Time)
   - The README text does not match the actual workflow cron expression.

## Proposed Changes

1. **README.md** — Fix duplicate numbering in Usage section:
   - Change `#### 4. Trigger the Workflow` to `#### 5. Trigger the Workflow`
   - Change `#### 5. Verify in Feishu` to `#### 6. Verify in Feishu`

2. **README.md** — Correct the scheduled time description:
   - Change "09:30 Beijing Time (01:30 UTC)" to "09:37 Beijing Time (01:37 UTC)" to match the workflow cron expression.

## Verification Steps

- Read README.md after edits to confirm numbering is sequential (4 → 5 → 6).
- Confirm the time string matches `37 1 * * *` in the workflow file.
- Ensure no other broken references or inconsistent invocation examples remain.
