# Code Contribution Standards for arXiv-Feishu Bot

> This document defines mandatory coding standards for all contributors,
> including automated coding agents. Violations will be rejected during
> code review.

---

## 1. Naming Conventions

### 1.1 Variables and Functions

- **Format**: lowercase snake_case exclusively.
- **Prohibition**: No camelCase, no PascalCase, no UPPER_SNAKE for
  non-constants.

```python
# Good
paper_count = 10
fetch_papers_from_arxiv()

# Bad
PaperCount = 10          # PascalCase for variable
fetchPapersFromArxiv()   # camelCase
FETCH_PAPERS()           # screaming snake for function
```

### 1.2 Function Naming Pattern

All functions MUST follow the `verb_owner_noun` pattern:

```
verb      + _ + owner/scope + _ + noun/object
  |              |                  |
action    + _ + context/thing  + _ + target
```

**Valid examples**:

| Function | verb | owner | noun |
|----------|------|-------|------|
| `fetch_papers_from_arxiv` | fetch | papers | from_arxiv |
| `build_card_from_papers` | build | card | from_papers |
| `summarize_paper_via_llm` | summarize | paper | via_llm |
| `generate_feishu_signature` | generate | feishu | signature |
| `push_card_to_feishu` | push | card | to_feishu |
| `diagnose_network_connectivity` | diagnose | network | connectivity |
| `run_daily_workflow` | run | daily | workflow |

**Invalid examples** (will be rejected):

```python
# Missing verb
def paper_fetcher(): ...

# Missing owner/scope
def fetch(): ...

# Missing noun
def do_something(): ...

# Wrong order
def arxiv_fetch_papers(): ...  # noun before verb
```

**Exceptions** (fixed by convention):

| Name | Reason |
|------|--------|
| `handler` | Cloud provider entry point convention |
| `__main__` | Python module entry point |

### 1.3 Variable Naming: No Meaningless Suffixes

**Prohibited suffixes**: `_info`, `_list`, `_dict`, `_data`, `_arr`,
`_obj`, `_val`, `_var`, `_tmp`, `_buf`.

The semantic context MUST imply the collection type. Use plural forms
for collections.

```python
# Good
papers = []           # plural implies list
endpoints = {}        # plural implies collection
config = {}           # context implies dict
metadata = {}         # context implies dict

# Bad
paper_list = []       # redundant suffix
endpoint_dict = {}    # redundant suffix
config_data = {}      # redundant suffix
result_info = {}      # meaningless suffix
tmp_val = 0           # meaningless prefix+suffix
```

### 1.4 Classes and Factory Functions

- **Classes**: PascalCase (e.g., `PaperFetcher`, `CardBuilder`).
- **Factory functions**: PascalCase (treat as class constructors).

```python
# Good
class PaperTranslator:
    ...

def CardBuilder(papers: List[Dict[str, str]]) -> Dict[str, Any]:
    ...

# Bad
class paper_translator:   # snake_case for class
class paperTranslator:    # camelCase for class
```

### 1.5 Constants

- **Module-level constants**: UPPER_SNAKE_CASE.
- **Type hints required** for all constants.

```python
# Good
ARXIV_API_ENDPOINTS: List[str] = [
    "https://export.arxiv.org/api/query",
]
MAX_RETRY_COUNT: int = 5
DEFAULT_TIMEOUT: float = 30.0

# Bad
arxiv_api_endpoints = [...]   # lowercase
MAXRETRYCOUNT = 5             # no underscores
```

---

## 2. Type Annotations

### 2.1 Mandatory Annotations

**Every function** MUST annotate all parameters and return types.
No exceptions.

```python
from typing import Dict, List

# Good
def fetch_papers_from_arxiv(
    categories: List[str],
    keywords: List[str],
    max_results: int = 50,
) -> List[Dict[str, str]]:
    ...

# Bad - missing any annotation
def fetch_papers_from_arxiv(categories, keywords, max_results=50):
    ...
```

### 2.2 Union Types: Use `T1 | T2`

For non-None unions, use PEP 604 `|`. **Never** use `typing.Union`.

```python
from typing import Union  # PROHIBITED - do not import

# Good (non-None union)
def process_result(
    data: Dict[str, str] | int,
) -> List[str] | int:
    ...

# Bad
def process_result(
    data: Union[Dict[str, str], int],
) -> Union[List[str], int]:
    ...
```

### 2.3 Optional Types

Always use `Optional[T]` for nullable types. Never use `T | None`.

```python
from typing import Dict, Optional

# Good
def find_paper_by_id(
    paper_id: Optional[str],
) -> Optional[Dict[str, str]]:
    ...

# Bad - uses | None
def find_paper_by_id(
    paper_id: str | None,
) -> Dict[str, str] | None:
    ...

# Bad - no annotation
def find_paper_by_id(paper_id):
    ...
```

### 2.4 Generics from typing

Use `typing` generics (`Dict`, `List`, etc.) in all annotations.
Keep lowercase builtins for instantiation only.

```python
from typing import Any, Dict, List

# Good
def build_card(
    papers: List[Dict[str, str]],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    ...

# Bad (built-in generics in annotations)
def build_card(
    papers: list[dict[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    ...
```

### 2.5 Variable Type Hints

Type hints REQUIRED for:
- Empty collections initialized at module level.
- Variables whose type cannot be inferred from the RHS.
- Complex nested types.

```python
from typing import Any, Dict, List

# Good
papers: List[Dict[str, str]] = []
config: Dict[str, Any] = {}

# Acceptable (type inferable)
papers = fetch_papers_from_arxiv()  # type inferred
```

---

## 3. Docstring Style

### 3.1 Format: NumPy/SciPy Style

All public functions MUST have docstrings in NumPy/SciPy format.

```python
from typing import Dict

def summarize_paper_via_llm(
    title: str,
    abstract: str,
) -> Dict[str, str]:
    """Translate and summarize a paper abstract using an LLM.

    Uses standard terminology from computational chemistry and
    theoretical chemistry. Returns Chinese title, abstract, and
    highlight bullet points.

    Parameters
    ----------
    title : str
        Original English paper title.
    abstract : str
        Original English paper abstract.

    Returns
    -------
    Dict[str, str]
        Dictionary with keys: chinese_title, chinese_abstract,
        highlights.
    """
```

### 3.2 Language: English Only

All docstrings, comments, and commit messages MUST be in English.

```python
# Good
# Fetches papers from arXiv using the official API.

# Bad
# 从arXiv获取论文
```

### 3.3 Required Sections

Every public function docstring MUST include:

1. **One-line summary** (first line, imperative mood).
2. **Blank line**.
3. **Extended description** (if behavior is non-obvious).
4. **Parameters** section (if any parameters).
5. **Returns** section (if return value is not None).
6. **Raises** section (if exceptions are raised intentionally).

Private functions (prefixed with `_`) MAY omit docstrings but
SHOULD include a brief comment.

---

## 4. Line Length and Formatting

### 4.1 Maximum Line Length

**79 characters** per line. Hard limit. No exceptions.

```python
# Good (79 chars or less)
logger.info(
    f"Found paper: [{published_date}] {result.title[:60]}..."
)

# Bad (exceeds 79 chars)
logger.info(f"Found paper: [{published_date}] {result.title[:60]}...")
```

### 4.2 Line Continuation

Use parentheses for implicit line continuation. Prefer this over
backslash `\`.

```python
# Good (parentheses)
query = (
    f'(cat:physics.chem-ph OR cat:cond-mat.mtrl-sci '
    f'OR cat:physics.comp-ph) '
    f'AND (all:"molecular dynamics")'
)

# Acceptable (backslash, avoid if possible)
query = f'(cat:physics.chem-ph) AND ' \
        f'(all:"molecular dynamics")'
```

### 4.3 String Concatenation Across Lines

Use f-string concatenation with parentheses.

```python
# Good
system_prompt = (
    "You are a senior researcher in computational chemistry, "
    "theoretical chemistry, and molecular simulation.\n"
    "Translate and summarize the following paper professionally."
)

# Bad (implicit concatenation without parentheses)
system_prompt = "You are a senior researcher in computational " \
                "chemistry, theoretical chemistry..."
```

### 4.4 Indentation

- **4 spaces** per indentation level.
- **No tabs**. Configure editor to insert spaces.
- Hanging indents align with opening delimiter.

```python
from typing import Any, Dict

# Good
def long_function_name(
    var_one: str,
    var_two: int,
    var_three: float,
) -> Dict[str, Any]:
    ...

# Bad (2 spaces)
def long_function_name(
  var_one: str,
  var_two: int,
) -> Dict[str, Any]:
    ...
```

---

## 5. Pythonic Patterns

### 5.1 Comprehensions Over Loops

Use list/dict comprehensions and generator expressions for
constructing collections. Avoid explicit `for` loops for simple
collection building.

```python
# Good (comprehension)
authors = [
    name_elem.text
    for author in entry.findall("atom:author", _ATOM_NS)
    if (name_elem := author.find("atom:name", _ATOM_NS))
    is not None
]

# Bad (explicit loop)
authors = []
for author in entry.findall("atom:author", _ATOM_NS):
    name_elem = author.find("atom:name", _ATOM_NS)
    if name_elem is not None:
        authors.append(name_elem.text)
```

### 5.2 Walrus Operator (`:=`)

Use walrus operator for assignment expressions within comprehensions
and conditions where it improves readability.

```python
# Good (walrus in comprehension)
authors = [
    name_elem.text
    for author in entry.findall("atom:author", _ATOM_NS)
    if (name_elem := author.find("atom:name", _ATOM_NS))
    is not None
]

# Good (walrus in condition)
if (count := len(papers)) > 0:
    logger.info(f"Found {count} papers")

# Bad (repeated expression)
if len(papers) > 0:
    logger.info(f"Found {len(papers)} papers")
```

### 5.3 Dictionary Merging

Use the `|` operator (PEP 604) for merging dictionaries. Avoid
`.update()` for creating new dicts.

```python
# Good (| operator)
processed = [
    paper | summarize_paper_via_llm(
        paper["original_title"], paper["abstract"]
    )
    for paper in papers
]

# Bad (.update() for new dict)
processed = []
for paper in papers:
    summary = summarize_paper_via_llm(
        paper["original_title"], paper["abstract"]
    )
    merged = paper.copy()
    merged.update(summary)
    processed.append(merged)
```

### 5.4 Single If-Else for Same Variable

Use conditional expressions (ternary) for single if-else assigning
to the same variable.

```python
# Good (conditional expression)
model_name = model if model else "gpt-4o"

# Bad (if-else block)
if model:
    model_name = model
else:
    model_name = "gpt-4o"
```

### 5.5 Truthiness Checks

Use implicit truthiness for empty collections and None checks.

```python
# Good
if papers:
    ...

if not api_key:
    ...

# Bad (explicit comparison)
if len(papers) > 0:
    ...

if api_key is None or api_key == "":
    ...
```

---

## 6. Module Structure

### 6.1 Import Order

1. `__future__` annotations (if needed).
2. Standard library imports.
3. Third-party imports.
4. Local imports.

Separate each group with a blank line.

```python
from __future__ import annotations

import base64
import hashlib
from datetime import datetime
from typing import Any

import arxiv
import requests
from openai import OpenAI
```

### 6.2 Module-Level Constants

Group related constants. Add type hints. Use docstrings for the
module if it is the main module.

### 6.3 Function Order

Organize functions logically:

1. Utility functions (no external dependencies).
2. Core business logic functions.
3. Orchestration functions.
4. Entry point functions.

---

## 7. Error Handling

### 7.1 Specific Exceptions

Catch specific exceptions, not bare `except`.

```python
# Good
try:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
except requests.exceptions.RequestException as e:
    logger.error(f"Request failed: {e}")

# Bad
try:
    resp = requests.get(url, timeout=30)
except:
    logger.error("Request failed")
```

### 7.2 Logging Over Print

Use the `logging` module. Never use `print()` for diagnostics.

```python
# Good
logger.info("Fetching papers from arXiv")
logger.error(f"Failed to fetch: {e}")

# Bad
print("Fetching papers from arXiv")
```

---

## 8. Quick Reference Checklist

Before submitting code, verify:

- [ ] All functions follow `verb_owner_noun` naming.
- [ ] No meaningless suffixes (`_list`, `_dict`, `_info`, etc.).
- [ ] All functions have full type annotations.
- [ ] Non-None unions use `T1 | T2` (never `Union[...]`); nullable types use `Optional[T]` (never `T | None`).
- [ ] All public functions have NumPy-style docstrings in English.
- [ ] No line exceeds 79 characters.
- [ ] 4 spaces for indentation, no tabs.
- [ ] Comprehensions used where appropriate.
- [ ] Walrus operator used for repeated expressions.
- [ ] Dictionary merge uses `|` operator.
- [ ] Specific exceptions caught, never bare `except`.
- [ ] `logging` used instead of `print`.
- [ ] Constants use UPPER_SNAKE_CASE with type hints.

---

## 9. Example: Complete Function

```python
from typing import Dict, List

def fetch_papers_from_arxiv(
    categories: List[str],
    keywords: List[str],
    max_results: int = 50,
) -> List[Dict[str, str]]:
    """Fetch papers from arXiv matching given categories and keywords.

    Uses the official arxiv Python library for robust API access
    with automatic rate limiting and retries.

    Parameters
    ----------
    categories : List[str]
        List of arXiv category strings (e.g., ["physics.chem-ph"]).
    keywords : List[str]
        List of keywords to search in title and abstract.
    max_results : int, optional
        Maximum number of results to return. Defaults to 50.

    Returns
    -------
    List[Dict[str, str]]
        List of paper dictionaries with keys: original_title,
        abstract, html_url, pdf_url, authors, published, arxiv_id.
    """
    yesterday = datetime.utcnow() - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")

    cat_clause = " OR ".join(f"cat:{c}" for c in categories)
    kw_clause = " OR ".join(f'all:"{kw}"' for kw in keywords)
    query = f"({cat_clause}) AND ({kw_clause})"

    logger.info(f"Query: {query}")

    client = arxiv.Client(
        page_size=max_results,
        delay_seconds=3,
        num_retries=5,
    )

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers: List[Dict[str, str]] = []
    for result in client.results(search):
        published_date = result.published.strftime("%Y-%m-%d")
        if published_date < date_str:
            break

        papers.append({
            "original_title": result.title,
            "abstract": result.summary,
            "html_url": result.entry_id.replace("abs", "html"),
            "pdf_url": result.pdf_url,
            "authors": ", ".join(a.name for a in result.authors),
            "published": published_date,
            "arxiv_id": result.entry_id.split("/")[-1],
        })

    logger.info(f"Retrieved {len(papers)} papers")
    return papers
```
