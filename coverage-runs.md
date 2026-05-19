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

## 2026-05-19 (run 3)

**Recent changes reviewed:** merge of PR #12 (agent context, 412 errors, tool defaults) — remaining gaps in status helpers, input upload heuristics, sessions API, async 412.

**Gaps filled:**
- `tests/test_client_status.py`: `parse_status`, `is_terminal_status`, `is_message_ready`, `_process_stream_event` (completed/failed/cancelled).
- `tests/test_client.py`: base64 and `data:` URI input upload paths; short-string false positive guard; async `RequirementsNotMetError` on 412.
- `tests/test_sessions.py`: `SessionHandle` context manager, ended-session guard, `SessionsAPI` CRUD, async sessions namespace.
- `tests/test_streamable.py`: `stream_post` / `stream_get` httpx-style helpers.
- `tests/test_agent.py`: `client.agents.create()` delegates to agent run flow.
