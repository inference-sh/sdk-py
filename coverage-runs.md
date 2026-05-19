# Coverage automation runs

## 2026-05-19 (documentation)

**Trigger:** sdk-py `2c2f455` — agent context API (`client.agent` vs `agents.create`), `call_tool` / `http_tool` / `mcp_tool` examples.

**Public docs updated:** `inference-sh/skills` python-sdk + javascript-sdk references (tool-builder, agent-patterns, SKILL.md). sdk-py `AgentsAPI.create` docstrings.

**Still needs sync (private docs repo):** [inference.sh/docs/api/agent-tools](https://inference.sh/docs/api/agent-tools) — add Call/HTTP and MCP sections; agent API page for per-chat `context`.

## 2026-05-19

**Recent changes reviewed:** `f404999` (ToolType.MCP + gotypegen acronym enums), `bf4cd7d` (call_tool/mcp_tool builders).

**Gaps filled:**
- `tests/test_tools.py`: HTTP/call/MCP tool builders (auth, method, schema) — would have caught `ToolType.M_C_P` AttributeError.
- `tests/test_types.py`: enum acronym regression (HTTP, MCP, CLOUD_AWS, etc.).
- `tests/test_imports.py`: public exports for `http_tool`, `call_tool`, `mcp_tool`.

**Not covered (lower priority this run):** Agent `context` parameter wiring (needs HTTP mock).

## 2026-05-19 (run 5)

**Recent changes reviewed:** `eff538d` (ToolParamType const split, integration enums, InstanceStatus lifecycle).

**Open PRs checked:** #42 covers `3df5ec8` session/agent streams — no overlap. #37/#39/#41/#44 are docs-only.

**Gaps filled:**
- `tests/test_types.py`: `ToolParamType` vs `ToolCallType` split, integration enums, `InstanceStatus` lifecycle.
- `tests/test_imports.py`: typegen exports for new enums.

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

## 2026-05-19 (run 4)

**Recent changes reviewed:** `8cb6eaf` on main (Pydantic v2 base models, `list.any()` fix in `render_message`, `parse_status` export, LLM/client/file test additions from PRs #15–#25).

**Open PRs checked:** #26–#28 are draft mypy/import fixes — no overlapping test work.

**Gaps filled:**
- `tests/test_models_base.py`: `Metadata` extra fields + `update()`, media mixin `contentMediaType` in JSON schema (Pydantic v2 `json_schema_extra` migration), `OrderedSchemaModel` field order.
- `tests/test_llm.py`: assistant plain-string content, file attachments, local image base64 encoding, data URI helpers, real `list.any()` regression via multipart image messages, `build_messages` alias.
- `tests/test_imports.py`: `parse_status`, `is_terminal_status`, `is_message_ready` in public API smoke list.

## 2026-05-19 (run 5)

**Recent changes reviewed:** `3df5ec8` on main (mypy fixes — SessionHandle.call return types, session creation guards, AsyncAgent stream casts, OrderedSchemaModel AST narrowing).

**Open PRs checked:** #37, #39, #41 are documentation-only — no overlapping test work.

**Gaps filled:**
- `tests/test_sessions.py`: `session.call()` wait/stream parity with `client.run()`; missing `session_id` error; async session context manager.
- `tests/test_agent.py`: `AsyncAgent.stream_messages()` / `stream_chat()` event filtering; guard when no active chat.
- `tests/test_models_base.py`: nested `OrderedSchemaModel` field-order fallback path.
