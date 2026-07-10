
<div align="right">

**English** | [中文](README.zh-CN.md)

</div>

# arXiv Daily Paper Bot for Feishu (Lark)

<img src="assets/arxivbot-logo.png" alt="arXiv Bot Logo" width="200">

Automatically fetch the latest arXiv papers every day, translate and
summarize them with AI, and push formatted interactive cards to your
Feishu (Lark) group chat.

**Who is this for**: Researchers and students who know nothing about AI
or programming and just want to receive daily paper digests.

**Three things you need**:
1. A GitHub account
2. An LLM API Key (DeepSeek recommended, detailed tutorial below)
3. A Feishu group with a custom bot

---

## Table of Contents

- [Features](#features)
- [5-Minute Quick Start (Recommended)](#5-minute-quick-start-recommended)
  - [Step 1: Prerequisites](#step-1-prerequisites)
  - [Step 2: Configure GitHub Secrets](#step-2-configure-github-secrets)
  - [Step 3: Run a Test](#step-3-run-a-test)
- [How to Get an LLM API Key (DeepSeek Example)](#how-to-get-an-llm-api-key-deepseek-example)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Customizing Search Queries](#customizing-search-queries)
- [Code Contribution Guidelines](#code-contribution-guidelines)
- [License](#license)

---

## Features

- **Daily Auto-Push**: Automatically fetches new papers every morning
- **Smart Filtering**: Filters papers by category and keyword
- **AI-Powered Translation**: Translates titles and abstracts into
  Chinese with proper terminology, and extracts key highlights
- **Rich Feishu Cards**: Beautiful interactive cards with direct links
  to paper pages
- **Zero Server Cost**: Runs entirely on GitHub Actions — free for
  public repositories

---

## 5-Minute Quick Start (Recommended)

> **No coding required, no programming knowledge needed.** Just follow
> the steps below and click through.

### Step 1: Prerequisites

Before you start, prepare the following:

1. **A GitHub account** (sign up at https://github.com if you don't
   have one — it's free)
2. **An LLM API Key** (DeepSeek recommended — cheap, easy to sign up,
   new users get free credits. Tutorial below.)
3. **A Feishu group + Feishu bot webhook URL**
   - In your Feishu group, go to **Group Settings** → **Group Bots**
     → **Add Bot** → **Custom Bot**
   - Give it a name (e.g., "arXiv Paper Assistant") and copy the
     Webhook URL

Once ready, fork this repository to your own GitHub account (click the
**Fork** button in the top-right corner).

### Step 2: Configure GitHub Secrets

This step tells the bot your "passwords." Don't worry — GitHub encrypts
them and no one else can see them.

1. Go to your forked repository page
2. Click **Settings** at the top
3. In the left sidebar, find **Secrets and variables** → click
   **Actions**
4. Click **New repository secret** in the top-right
5. Add each item from the table below one by one:

| Secret Name | Required? | Description | Example |
|-------------|-----------|-------------|---------|
| `OPENAI_API_KEY` | ✅ Yes | API key from your LLM provider | `sk-xxxxxxxxxxxx` |
| `OPENAI_BASE_URL` | ✅ Yes | LLM API base URL (required for DeepSeek) | `https://api.deepseek.com/v1` |
| `OPENAI_MODEL` | ❌ No | Model name, defaults to `gpt-4o` | `deepseek-chat` |
| `FEISHU_WEBHOOK_URL` | ✅ Yes | Feishu bot webhook URL | `https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx` |
| `FEISHU_SECRET` | ❌ No | Feishu signature secret (only if enabled) | optional |
| `MAX_PAPERS` | ❌ No | Max papers per day, defaults to 10 | `5` |
| `ARXIV_CATEGORIES` | ❌ No | arXiv subject categories, defaults to computational physics | see below |
| `ARXIV_KEYWORDS` | ❌ No | Search keywords, defaults to MD + machine learning | see below |
| `USER_AGENT_EMAIL` | ❌ No | Your email for User-Agent, helps avoid blocking | `your@email.com` |

> 💡 **Tip**: After adding each one, click **Add secret** to save it,
> then move on to the next.

### Step 3: Run a Test

Once configured, let's run it manually to see if it works:

1. Click **Actions** at the top of the repository
2. Select **arXiv Daily Paper Push** on the left
3. Click **Run workflow** on the right → then click the green
   **Run workflow** button
4. Wait a minute or two. When the status shows ✅, it succeeded!
5. Check your Feishu group — did you receive the paper digest card?

If it works, the bot will automatically run **every day at 09:37 Beijing
Time** without any further action from you.

---

## How to Get an LLM API Key (DeepSeek Example)

LLM stands for "Large Language Model" — it's what powers the paper
translation and summarization. We'll use DeepSeek as an example because
it's affordable, easy to sign up for, and new users get free credits.

### 1. Sign Up for DeepSeek

Go to https://platform.deepseek.com and sign up with your phone number.

### 2. Top Up (Optional — New Users Get Free Credits)

- New users usually receive free credits after signing up, which is
  enough for a long trial period
- If you run out, you can top up on the "Top Up" page. It's very cheap
  — just a few dollars a month for 10 papers per day

### 3. Get Your API Key

1. After logging in, click **API Keys** in the left menu
2. Click the **Create new API Key** button
3. Give it a name, like "arxiv-bot", then click create
4. **Important**: The key only shows once! Copy it right away and save
   it somewhere safe — you won't see it again after closing the page
5. This key is what you'll use for `OPENAI_API_KEY` above

### 4. What Else Do I Need to Fill In?

If you're using DeepSeek, you need to set these three GitHub Secrets:

| Secret Name | Value |
|-------------|-------|
| `OPENAI_API_KEY` | The `sk-...` key you just copied |
| `OPENAI_BASE_URL` | Exactly: `https://api.deepseek.com/v1` |
| `OPENAI_MODEL` | Exactly: `deepseek-chat` |

> 💡 **What about other LLM providers?**
> Any OpenAI-compatible API works — Zhipu AI, Moonshot, Qwen, etc.
> The process is similar, just use different values for
> `OPENAI_BASE_URL` and `OPENAI_MODEL`.

---

## Configuration

### Environment Variables

All configuration is done via environment variables (GitHub Secrets).
No code changes needed.

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | LLM API key, **required** |
| `OPENAI_BASE_URL` | — | Custom LLM API base URL (required for DeepSeek and others) |
| `OPENAI_MODEL` | `gpt-4o` | Model name |
| `FEISHU_WEBHOOK_URL` | — | Feishu bot webhook URL, **required** |
| `FEISHU_SECRET` | — | Feishu signature secret (optional) |
| `MAX_PAPERS` | `10` | Maximum papers to push per day |
| `ARXIV_CATEGORIES` | computational physics | arXiv category expression |
| `ARXIV_KEYWORDS` | molecular dynamics + ML | Keyword search expression |
| `ARXIV_API_URL` | — | Custom arXiv API endpoint (optional) |
| `HTTP_PROXY` | — | HTTP proxy (optional) |
| `HTTPS_PROXY` | — | HTTPS proxy (optional) |
| `ENABLE_NETWORK_DIAG` | `false` | Enable network diagnostics logs |

### Customizing Search Queries

By default, the bot searches for papers about **molecular dynamics and
machine learning** within **computational physics, materials science,
and computational physics** categories.

To customize for your own research area, add `ARXIV_CATEGORIES` and
`ARXIV_KEYWORDS` as GitHub Secrets.

#### Categories (ARXIV_CATEGORIES)

Separate multiple categories with `||` (meaning "OR"). Wrap each
category in double quotes.

Example — adding biophysics and statistical mechanics:

```
"physics.chem-ph"||"cond-mat.mtrl-sci"||"physics.comp-ph"||"physics.bio-ph"||"cond-mat.stat-mech"
```

Find all category codes here: https://arxiv.org/category_taxonomy

#### Keywords (ARXIV_KEYWORDS)

- `&&` means "AND"
- `||` means "OR"
- Parentheses `()` can be used for grouping

Example — "molecular dynamics" AND ("machine learning" OR "force field"
OR "coarse-grained"):

```
"molecular dynamics"&&("machine learning"||"deep learning"||"neural network"||"force field"||"coarse-grained")
```

> 💡 **Not sure how to write it?**
> No worries — just use the defaults for now. You can tweak it later
> once you're more familiar.

---

## Code Contribution Guidelines

We welcome contributions! Please follow these standards to maintain
code quality and consistency.

### Naming Conventions

- **Variables and functions**: Use lowercase snake_case exclusively.
- **Function naming**: Follow the `verb_owner_noun` pattern (e.g.,
  `fetch_papers_from_arxiv`, `build_card_from_papers`,
  `summarize_paper_via_llm`).
- **Avoid meaningless suffixes**: Don't use `_info`, `_list`, `_dict`,
  `_data` as suffixes. Let the semantic context imply the collection
  type (e.g., `papers` instead of `paper_list`, `endpoints` instead of
  `endpoint_list`).
- **Classes and factory functions**: Use PascalCase (e.g.,
  `PaperFetcher`, `CardBuilder`).

### Type Annotations

- Annotate **all** function parameters and return types.
- Use the `|` union operator instead of `typing.Union` (PEP 604).
- Prefer `typing.Optional` for nullable types.
- Use `typing` generics where applicable (e.g., `List[str]`,
  `Dict[str, Any]`).

```python
# Good
def fetch_papers_from_arxiv() -> List[Dict[str, str]]:
    ...

# Bad
def fetch_papers_from_arxiv():
    ...
```

### Docstring Style

- Use **NumPy/SciPy style** docstrings for all public functions.
- Write docstrings in **English**.
- Clearly describe each parameter's type and meaning, and document the
  return value structure.

```python
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

### Line Length and Formatting

- **Maximum line length**: 79 characters (PEP 8).
- Use parentheses for implicit line continuation. Prefer this over
  backslash `\`.
- Use 4 spaces for indentation. No tabs.

### Pythonic Patterns

- **Comprehensions**: Prefer list/dict comprehensions and generator
  expressions over explicit `for` loops for collection construction.
- **Walrus operator**: Use `:=` for assignment expressions within
  comprehensions and conditions where it improves readability.
- **Dictionary merging**: Use the `|` operator (PEP 604) for merging
  dictionaries instead of `.update()`.

```python
# Good: comprehension + walrus
authors = [
    name_elem.text
    for author in entry.findall("atom:author", _ATOM_NS)
    if (name_elem := author.find("atom:name", _ATOM_NS))
    is not None
]

# Good: dictionary merge
processed = [
    paper | summarize_paper_via_llm(
        paper["original_title"], paper["abstract"]
    )
    for paper in papers
]
```

---

## License

This project is licensed under the MIT License. See the LICENSE file
in the repository for full details.
