# Add Boolean Expression Parser for --keyword and --category Plan

## Summary

Replace the list-based `--category` and `--keyword` CLI arguments with single string arguments that accept simple Boolean expressions using `&&` (AND), `||` (OR), and parentheses. A lightweight parser converts these expressions into valid arXiv query syntax via string substitution.

## Current State Analysis

- `lark_arxivbot/cli.py`: `--category` and `--keyword` use `action="append"`, yielding `List[str]`.
- `lark_arxivbot/arxiv_fetcher.py`: `_build_query(categories: List[str], keywords: List[str])` joins lists with `OR`.
- `lark_arxivbot/workflow.py`: `run_daily_workflow` accepts `Optional[List[str]]` for both.
- `tests/test_cli.py` and `tests/test_arxiv.py` assert list-based behavior.

## Proposed Changes

### File: `lark_arxivbot/arxiv_fetcher.py`

**1. Add `_parse_expression`**
```python
import re

def _parse_expression(expression: str, prefix: str) -> str:
    """Parse a simple Boolean expression into arXiv query syntax.

    Supports ``&&`` (AND), ``||`` (OR), and parentheses.
    Terms must be quoted with double quotes.

    Parameters
    ----------
    expression : str
        Input expression, e.g.
        ``"a"&&("b"||"c")``.
    prefix : str
        Field prefix, e.g. ``"cat:"`` or ``'all:"'``.

    Returns
    -------
    str
        arXiv query snippet, e.g.
        ``(cat:a) AND ((cat:b) OR (cat:c))``.
    """
    result = re.sub(
        r'"([^"]+)"',
        lambda m: f'({prefix}{m.group(1)})',
        expression,
    )
    result = result.replace("&&", " AND ")
    result = result.replace("||", " OR ")
    return result
```

**2. Modify `_build_query`**
Change signature to accept `str | List[str]` for both parameters:
```python
def _build_query(
    categories: str | List[str],
    keywords: str | List[str],
) -> str:
```
If a parameter is a `str`, pass it through `_parse_expression`; otherwise use the existing list logic.

**3. Modify `fetch_papers_from_arxiv` signature**
```python
def fetch_papers_from_arxiv(
    categories: Optional[str | List[str]] = None,
    keywords: Optional[str | List[str]] = None,
    ...
) -> List[Dict[str, str]]:
```
If `None`, fall back to the config defaults (which remain `List[str]`).

### File: `lark_arxivbot/cli.py`

**1. Change `--category` and `--keyword` argument definitions**
Remove `action="append"`. Set defaults to expression strings:
```python
_DEFAULT_CATEGORY_EXPR = (
    '"physics.chem-ph"||"cond-mat.mtrl-sci"||"physics.comp-ph"'
)
_DEFAULT_KEYWORD_EXPR = (
    '"molecular dynamics"&&'
    '("machine learning"||"deep learning"||"neural network")'
)

parser.add_argument(
    "--category",
    default=_DEFAULT_CATEGORY_EXPR,
    help=(
        "arXiv category expression. "
        'See https://arxiv.org/category_taxonomy for valid values. '
        'Use "term" for literals, && for AND, || for OR. '
        'Defaults to computational-physics categories.'
    ),
)
parser.add_argument(
    "--keyword",
    default=_DEFAULT_KEYWORD_EXPR,
    help=(
        "Search keyword expression. "
        'Use "term" for literals, && for AND, || for OR. '
        'Defaults to MD/ML/DL/NN keywords.'
    ),
)
```

**2. Update `main` to pass strings directly**
`args.category` and `args.keyword` are now strings, so pass them directly to `run_daily_workflow`.

### File: `lark_arxivbot/workflow.py`

**1. Update `run_daily_workflow` signature**
```python
def run_daily_workflow(
    categories: Optional[str | List[str]] = None,
    keywords: Optional[str | List[str]] = None,
    ...
) -> None:
```
Update docstrings accordingly.

### File: `tests/test_arxiv.py`

**1. Add tests for `_parse_expression`**
- `test_parse_expression_category_or`
- `test_parse_expression_keyword_and_or`
- `test_parse_expression_single_term`

**2. Update `fetch_papers_from_arxiv` channel tests**
If any test directly calls `fetch_papers_from_arxiv(categories=..., keywords=...)` with lists, no changes needed (lists still work).

### File: `tests/test_cli.py`

**1. Update `test_cli_defaults`**
Assert that `run_daily_workflow` is called with the new default expression strings instead of `None`.

**2. Update `test_cli_passes_args_to_run_daily_workflow`**
Change the CLI invocation to pass single expression strings instead of repeated flags, and assert the strings are forwarded.

### File: `README.md`

**1. Update "Local Usage via CLI" examples**
Replace repeated `--category`/`--keyword` flags with expression examples:
```bash
pixi run lark-arxivbot --category '"physics.bio-ph"||"cond-mat.stat-mech"'
pixi run lark-arxivbot --keyword '"force field"&&"coarse-grained"'
```

**2. Update "Customizing Search Queries" section**
Replace list-based examples with expression-based examples. Keep the arXiv query syntax reference table.

## Assumptions & Decisions

- **String-only parser**: The parser relies purely on regex substitution and string replacement. It does not build an AST or validate parentheses nesting. Invalid expressions will be passed to arXiv, which will return an error.
- **Terms must be double-quoted**: This is required so the regex can unambiguously identify literal strings. Parentheses and operators are unquoted.
- **Backward compatibility**: `fetch_papers_from_arxiv` still accepts `List[str]` for existing callers (e.g., tests, Alibaba Cloud Function Compute).
- **Defaults are expressions**: When the user runs `lark-arxivbot` with no arguments, the defaults produce the same query as before, just expressed as `||`/`&&` strings.

## Verification Steps

1. Run `pixi run --environment test pytest tests/test_arxiv.py -v` and confirm all tests pass.
2. Run `pixi run --environment test pytest tests/test_cli.py -v` and confirm all tests pass.
3. Run `pixi run --environment test pytest tests/ -v` for full regression.
4. Run `pixi run python lark_arxivbot/cli.py --help` and verify the new defaults and help text.
5. Run `pixi run python lark_arxivbot/cli.py --check-availability` and confirm the bot still works end-to-end.
