# Test coverage automation runs

## 2026-05-22 (push main @ 76f33e6, v0.7.9)

**Skipped (open PR #66):** billing/knowledge/oauth/notification enum tests from `0c6e23a` — draft PR `cursor/test-coverage-automation-4901` already covers those.

**Gaps filled this run:**

- `ChatInput` / `ModelSettings` — nested sampling schema, validation bounds, `build_openai_messages` compatibility (commit `3eda863`)
- RFC 9457 problem+json error parsing — `detail` / `title` fallback in sync client (commit `bedb60e`)
- `X-API-Version: 2` header on requests
- `SuggestRequest` / `SuggestResponse` / `SuggestResult` import smoke (commit `0637e77`)

**Files:** `tests/test_llm.py`, `tests/test_client.py`, `tests/test_imports.py`
