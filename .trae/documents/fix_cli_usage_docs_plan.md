# Fix CLI Usage Documentation and Explain pixi shell Behavior Plan

## Summary

The user reports that `pixi shell && lark-arxivbot` fails with "no such file or directory". Investigation shows the pyproject.toml configuration is correct and `lark-arxivbot` is properly installed in the pixi environment. The issue is a usage misunderstanding: `pixi shell` launches an interactive subshell, so `&&` cannot be used to chain commands. The README.md needs to clarify the correct usage patterns.

## Current State Analysis

- `pyproject.toml` correctly defines `[project.scripts] lark-arxivbot = "lark_arxivbot.cli:main"`.
- `[tool.pixi.pypi-dependencies]` declares `lark-arxivbot = { path = ".", editable = true }`.
- `pixi run which lark-arxivbot` resolves to `.pixi/envs/default/bin/lark-arxivbot`.
- `bash -c 'eval "$(pixi shell-hook)" && lark-arxivbot --help'` works perfectly.
- `pixi shell-hook` output shows `PATH` is correctly set to include `.pixi/envs/default/bin`.
- **Root cause**: `pixi shell` starts an interactive subshell; `&&` waits for it to exit before running the next command, which never happens interactively. Even if it did, the right-hand side would run outside the pixi environment.

## Proposed Changes

### File: `/home/huangyike/devel/arxiv-feishu-bot/README.md`

**1. Rewrite the "Local Usage via CLI" subsection**

Replace the current single example with two clearly labeled options:

```markdown
#### 3. Local Usage via CLI

After installing dependencies (`pixi install`), you can run the bot
locally in two ways.

**Option A: `pixi run` (recommended)**

No need to activate the environment manually. Pixi temporarily
activates it for the command:

```bash
pixi run lark-arxivbot
```

**Option B: `pixi shell` (interactive)**

Enter an interactive shell with the pixi environment activated, then
run commands directly:

```bash
pixi shell
# (inside the pixi shell)
lark-arxivbot
```

> **Important**: Do **not** use `pixi shell && lark-arxivbot`.
> `pixi shell` launches an interactive subshell, so `&&` will not
> work as expected.
```

**2. Update the customization examples**
Change all `pixi run lark-arxivbot ...` examples to show the `pixi run`
prefix consistently.

**3. Add a note about `pixi install`**
Ensure step 2 (Install Dependencies) already mentions `pixi install`.
If not, add it.

## Assumptions & Decisions

- **No code changes needed**: The pyproject.toml and pixi configuration are already correct. This is purely a documentation fix.
- **Two valid patterns**: `pixi run <cmd>` is the one-shot pattern; `pixi shell` is for interactive development. Both are valid pixi idioms.

## Verification Steps

1. Run `pixi run lark-arxivbot --help` and confirm it works.
2. Run `bash -c 'eval "$(pixi shell-hook)" && lark-arxivbot --help'` and confirm it works.
3. Review the updated README.md for clarity.
