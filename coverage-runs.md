# Coverage automation notes

## 2026-05-19 run (cursor/test-coverage-automation-30e8)
- Recent merges on `main`: workflow/Makefile/README only; no new production logic to test there.
- Open PRs #13/#15 already cover client sessions, status helpers, stream stripping — avoided overlap.
- Gap: `build_openai_messages` / `build_tools` in `models/llm.py` had zero tests; `render_message` used invalid `list.any()` (same fix as open PR #17).
- Added: `tests/test_llm.py` (15 tests) + one-line `any(...)` fix in `llm.py`.
- Validation: `237 passed, 25 skipped`.

## 2026-05-19 run (prior)
- Recent merge: f404999 — ToolType.MCP/HTTP enum rename after gotypegen fix; tools.py updated.
- Gap: test_tools.py had no MCP/HTTP/handler tests; test_imports had no enum acronym guards.
- Added: TestHTTPToolBuilder, TestMCPToolBuilder, TestClientToolHandler, test_enum_acronym_members.
- Branch: cursor/regression-test-coverage-62be
