# Coverage automation runs

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

## 2026-05-19 (run 6)

**Recent changes reviewed:** `e39d401`–`f3bbb54` on main (docs for namespaced client API, session.call options, ToolParamType split). Production risk remains in agent file upload/run helpers and SessionHandle wrappers (doc-only session.py changes).

**Open PRs checked:** #46–#53 are documentation drafts — no overlapping test work.

**Gaps filled:**
- `tests/test_agent.py`: `agent.run()` finish output, `reset()`, `upload_file()` (bytes/data URI/invalid URI), `send_message(files=...)`, `AsyncAgentsAPI.create()`.
- `tests/test_sessions.py`: `SessionHandle.info()` / `keepalive()` delegation.

## 2026-05-20

**Recent changes reviewed:** `df3473b` on main (merge of PR #54 — agent run/upload_file and session handle tests).

**Open PRs checked:** #55 and #56 are documentation drafts — no overlapping test work.

**Gaps filled:**
- `tests/test_agent.py`: sync `stream_messages()` / `stream_chat()`, `stop_chat()`, `get_chat()`, `send_message` streaming callbacks.
- `tests/test_sessions.py`: `AsyncSessionHandle.info()` / `keepalive()`, ended-session guard on async `call()`.
- `tests/test_download.py`: `download()` cache layout, query-string hashing, cache hit skip, failure path.
- `tests/test_models_base.py`: `BaseApp` default `setup`/`unload` and `run()` NotImplemented guard.
- `tests/test_client.py`: `tasks.stream()` namespace delegation.
- `tests/test_errors.py`: `RequirementsNotMetError.__repr__`.

## 2026-05-20 (run 2)

**Recent changes reviewed:** `f5a5eb5` on main (typegen regen: `GraphEdgeType.REFERENCES`), merges of lint/async-test-support PRs (no production logic).

**Open PRs checked:** none open — no overlapping test work.

**Gaps filled:**
- `tests/test_types.py`: `GraphEdgeType` (including `REFERENCES`), `GraphNodeType`, `GraphNodeStatus` enum stability.
- `tests/test_imports.py`: typegen exports for graph workflow enums.
- `tests/test_client.py`: async `tasks.wait_for_completion()` / `tasks.stream()`, `files.upload()` namespace delegation.
- `tests/test_errors.py`: `SessionExpiredError`, `SessionEndedError`, `WorkerLostError` `__repr__` paths.
- `tests/test_download.py`: default filename when URL has no path; `StorageDir.path` mkdir behavior.
- `tests/test_streamable.py`: `streamable_raw()` scalar/array JSON wrapping.

## 2026-05-21

**Recent changes reviewed:** `0c6e23a` on main (typegen regen: knowledge/oauth/subscription/billing request types and 12 new enums).

**Open PRs checked:** none open — PR #64 (graph/async gaps) already merged; no overlapping test work.

**Gaps filled:**
- `tests/test_types.py`: subscription, resource, secret scope, device auth, MCP server auth (O_AUTH acronym), ref routes, integration chat types, notification enums.
- `tests/test_imports.py`: typegen exports for billing/knowledge/oauth/subscription DTOs and enums.
