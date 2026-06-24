# Improve Availability Checks with Real LLM Probe and Timeouts Plan

## Summary

The current `check_llm_availability()` only verifies that `OPENAI_API_KEY` is set and optionally probes the base URL with an HTTP GET. This is insufficient — a real availability check must send a chat-completion request to the LLM and verify it responds without error. Additionally, all three availability checks (network, arXiv, LLM) must enforce explicit timeout policies and log timeout errors distinctly.

## Current State Analysis

- `lark_arxivbot/availability.py` contains:
  - `check_network_availability()`: calls `diagnose_network_connectivity()`, which already uses `requests.get(..., timeout=10)` but leaves DNS resolution (`socket.gethostbyname`) without an explicit timeout.
  - `check_arxiv_availability(channel)`: calls `fetch_papers_from_arxiv()`, which has no timeout parameter and may hang indefinitely if the arXiv library or Atom API stalls.
  - `check_llm_availability()`: only checks env vars and performs a lightweight HTTP GET to `OPENAI_BASE_URL`. It never actually invokes the LLM chat-completion endpoint.
- `lark_arxivbot/llm.py` already constructs an `OpenAI` client and calls `chat.completions.create`. We can reuse this pattern.

## Proposed Changes

### File: `/home/huangyike/devel/arxiv-feishu-bot/lark_arxivbot/availability.py`

**1. Add imports**
- `from concurrent.futures import ThreadPoolExecutor, TimeoutError`
- `from openai import OpenAI, APITimeoutError`

**2. Refactor `check_llm_availability()`**
- Replace the env-var / HTTP-GET logic with a real chat-completion probe.
- Build an `OpenAI` client using `api_key` and optional `base_url`, passing `timeout=15.0` to the constructor.
- Send a minimal message (e.g., `"Who are you?"`) with `max_tokens=20`.
- On success: log the model name (e.g., `logger.info(f"LLM availability check passed (model={model_name})")`) and return `True`.
- On `APITimeoutError`: log `logger.error("LLM availability check timed out")` and return `False`.
- On any other exception: log `logger.error(f"LLM availability check failed: {e}")` and return `False`.

**3. Add timeout wrapper for `check_network_availability()`**
- Use `ThreadPoolExecutor(max_workers=1)` to wrap the call to `diagnose_network_connectivity()`.
- Apply `future.result(timeout=30.0)`.
- If `TimeoutError` occurs: log `logger.error("Network availability check timed out")` and return `False`.
- Otherwise evaluate results as before.

**4. Add timeout wrapper for `check_arxiv_availability()`**
- Define a private helper `_check_arxiv(channel: str) -> bool` containing the existing `try/except` + `fetch_papers_from_arxiv()` logic.
- In `check_arxiv_availability`, submit `_check_arxiv` to a `ThreadPoolExecutor(max_workers=1)` and call `future.result(timeout=30.0)`.
- If `TimeoutError` occurs: log `logger.error("arXiv availability check timed out")` and return `False`.
- On any other exception: log `logger.error(f"arXiv availability check failed: {e}")` and return `False`.

**5. Update docstrings**
- Document the new timeout behaviors and the real LLM probe in each function's docstring.

### File: `/home/huangyike/devel/arxiv-feishu-bot/tests/test_availability.py`

**1. Update `test_check_llm_availability_with_key`**
- Mock `openai.OpenAI` and its `chat.completions.create` method to return a fake response.
- Assert the function returns `True`.

**2. Add `test_check_llm_availability_timeout`**
- Mock `openai.OpenAI` so that `chat.completions.create` raises `APITimeoutError`.
- Assert the function returns `False` and that the log contains "timed out".

**3. Add `test_check_llm_availability_api_error`**
- Mock `openai.OpenAI` so that `chat.completions.create` raises a generic `RuntimeError`.
- Assert the function returns `False`.

**4. Update existing network / arXiv tests if needed**
- The existing mocks for `diagnose_network_connectivity` and `fetch_papers_from_arxiv` should still work because `ThreadPoolExecutor` reads the patched module attributes. No test changes are expected unless assertions fail.

## Assumptions & Decisions

- **ThreadPoolExecutor for network and arXiv**: Both `diagnose_network_connectivity` and `fetch_papers_from_arxiv` lack direct timeout parameters. Wrapping them in `ThreadPoolExecutor` + `future.result(timeout=...)` is the least-invasive way to enforce a hard deadline without modifying `arxiv.py`.
- **OpenAI client timeout for LLM**: The `openai` Python client accepts a `timeout` constructor argument. This is cleaner than a thread wrapper for LLM because it yields a distinct `APITimeoutError`.
- **Timeout values**: 30 seconds for network and arXiv, 15 seconds for LLM. These are generous enough for slow networks but prevent indefinite hangs.
- **Keep `check_user_agent_email` unchanged**: It is not mentioned in the user's request and is harmless.

## Verification Steps

1. Run `pixi run --environment test pytest tests/test_availability.py -v` and confirm all tests pass.
2. Run `pixi run --environment test pytest tests/ -v` to ensure no regressions in other modules.
3. Verify the CLI still works: `pixi run lark-arxivbot --check-availability` (with valid env vars) should log the model name on success.
