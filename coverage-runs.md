# Coverage automation runs

## 2026-05-19

**Recent changes reviewed:** `f404999` (ToolType.MCP + gotypegen acronym enums), `bf4cd7d` (call_tool/mcp_tool builders).

**Gaps filled:**
- `tests/test_tools.py`: HTTP/call/MCP tool builders (auth, method, schema) — would have caught `ToolType.M_C_P` AttributeError.
- `tests/test_types.py`: enum acronym regression (HTTP, MCP, CLOUD_AWS, etc.).
- `tests/test_imports.py`: public exports for `http_tool`, `call_tool`, `mcp_tool`.

**Not covered (lower priority this run):** Agent `context` parameter wiring (needs HTTP mock).

## 2026-05-19 (run 2)

**Recent changes reviewed:** `bf4cd7d` (agent context), `1eb100c` (require_approval bool + TypedDict casts), client 412 handling.

**Gaps filled:**
- `tests/test_agent.py`: `context` dict forwarded on `/agents/run` for template and ad-hoc agents.
- `tests/test_errors.py`: `RequirementsNotMetError`, `RequirementError`, session error types.
- `tests/test_client.py`: 412 → `RequirementsNotMetError` on `client.run()`.
- `tests/test_tools.py`: `require_approval` defaults to `False`, `display_name()`, `.handler()`.

## 2026-05-19 (run 3 — automation 41a5)

**Recent changes reviewed:** `f2d86ad` (workflow-only, base-branch dev). Open PR #13 covers status/sessions/upload — not duplicated.

**Gaps filled:**
- `tests/test_client_helpers.py`: `_strip_task`, `_looks_like_base64`, `_process_stream_event`.
- `tests/test_client.py`: `tasks.wait_for_completion`, `run(wait=False)` strips internal fields.
- `tests/test_agent.py`: `agents.create`, `submit_tool_result` (string vs JSON widget action), client-tool dedup in `stream_all`.
- `tests/test_file.py`: data-URI URL-encoding, invalid URI, init validation.

**Validation:** 241 passed, 22 skipped.
