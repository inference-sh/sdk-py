# Coverage automation runs

## 2026-07-13 (push dev @ cd8e0b6, SuggestRequest.context merged; Scope/EngineStatus still missing)

**Recent changes reviewed:** `cd8e0b6` (added `SuggestRequest.context` test only — commit message claimed Scope/SetupAction/EngineStatus restore but those tests were not included). Prior ping-pong commits `8a4dc1a`/`8ca6d5a`/`cc2685a` dropped Scope/SetupActionType/EngineStatus/INTEGRATION_REQUIREMENT/PENDING coverage while landing entitlement/AppStore/UserMetadata tests.

**Open PRs checked:** none open. Remote branches `cursor/missing-test-coverage-9290`/`e655` had the dropped tests but were never merged.

**Gaps filled this run:**

- `Scope` / `ScopeGroup` enums, `AuthSessionDTO.scopes`, and `ScopesResponse` catalog shape (API key permissions)
- `SetupActionType` enum and `SetupAction` TypedDict with provider labels and scope descriptions
- `EngineStatus` lifecycle including `disconnected` and `draining` states
- `IntegrationStatus.PENDING` OAuth-in-progress state
- `GraphNodeType.INTEGRATION_REQUIREMENT` workflow node kind
- `RequirementError.from_dict` propagates `provider_name` / `scope_descriptions` through nested setup actions

**Files:** `tests/test_types.py`, `tests/test_imports.py`, `tests/test_errors.py`

## 2026-07-13 (push dev @ 7db09b9, SuggestRequest.Context field)

**Recent changes reviewed:** `7db09b9` (typegen regen: optional `context` on `SuggestRequest` for contextual app/agent suggestions). `f0a98f6` version bump only.

**Open PRs checked:** #118 and #115 (draft) restore Scope/SetupActionType/EngineStatus coverage dropped in ping-pong commits `8a4dc1a`/`8ca6d5a`/`cc2685a` — no overlap; those gaps deferred to open PRs.

**Gaps filled this run:**

- `SuggestRequest.context` optional string for disambiguating suggest queries (e.g. workflow context)

**Files:** `tests/test_types.py`

## 2026-07-13 (push dev @ 893a4cf, aiofiles + entitlement tests merged)

**Recent changes reviewed:** `893a4cf` (aiofiles RuntimeError, entitlement/IntegrationScope gaps — merged). `a71ad24` AppStoreListingDTO/UserMetadataDTO tests were accidentally dropped when `893a4cf` replaced them with entitlement coverage. `6fd3aac` production: `min_concurrency` on `AppStoreListingDTO`; `terms_accepted_at`/`terms_version` on `UserMetadataDTO`.

**Open PRs checked:** #109 (SetupActionType/EngineStatus/graph TRIGGER restore), #107 (Scope/AuthSessionDTO/setup-action parsing) — no overlap.

**Gaps filled this run:**

- `AppStoreListingDTO` `min_concurrency` / `max_concurrency` / `max_concurrency_per_team` worker scaling fields (restored)
- `UserMetadataDTO` `terms_accepted_at` / `terms_version` terms acceptance tracking (restored)
- `EntitlementSource` enum (`tier`, `override`, `whitelist`, `trial`) on `EntitlementDTO`
- `WorkerStatus` lifecycle (`reserved`, `busy`, `idle`, `inactive`) on `WorkerDTO`/`WorkerSummary`

**Files:** `tests/test_types.py`, `tests/test_imports.py`

## 2026-07-09 (push dev @ 73cdf23, aiofiles missing error fix)

**Recent changes reviewed:** `73cdf23` (RuntimeError when aiofiles absent; importorskip on async path upload test). Remaining gaps from `9c89152` typegen: `IntegrationScope`, `EntitlementResource`/`RESOURCE_TRIGGERS`, `IntegrationRequirement` secrets/scopes, `GraphNodeType.TRIGGER` (closed PRs #92/#99 never merged).

**Open PRs checked:** none open — no overlapping test work.

**Gaps filled this run:**

- `_aio_open_file()` raises `RuntimeError` with `pip install aiofiles` hint when dependency missing (regression guard for `73cdf23`)
- `GraphNodeType.TRIGGER` workflow node kind
- `IntegrationScope` enum (`team`, `platform`) on `IntegrationDTO`
- `EntitlementResource` plan limit keys including `RESOURCE_TRIGGERS`
- `IntegrationRequirement` TypedDict `secrets`/`scopes` fields for app manifests
- `PlanDTO.limits` `PlanLimits` mapping with `PlanLimit` entries

**Files:** `tests/test_client_helpers.py`, `tests/test_types.py`, `tests/test_imports.py`

## 2026-07-09 (push dev @ 1f8ad37, device auth + GOOGLE_SA DTO tests merged)

**Recent changes reviewed:** `1f8ad37` (DeviceAuthResponse, scope updates, GOOGLE_SA DTO — already merged). Remaining gap from `f1a3cbe`: `RequirementType` enum, `IntegrationConfigDTO.slug`, typed `RequirementError`/`CheckRequirementsResponse` (closed PR #94 never merged).

**Open PRs checked:** #92 (draft) covers IntegrationScope/entitlement/TRIGGER/IntegrationRequirement secrets — no overlap.

**Gaps filled this run:**

- `RequirementType` enum (`secret`, `integration`, `scope`) for 412 requirement errors
- `IntegrationConfigDTO.slug` provider catalog key (e.g. `google-sa`)
- `CheckRequirementsResponse` errors typed with `RequirementType`
- `IntegrationProvider.GOOGLE_SA` enum stability in integration parametrize

**Files:** `tests/test_types.py`, `tests/test_imports.py`

## 2026-07-09 (push dev @ e8716c2, lint-only import cleanup)

**Recent changes reviewed:** `e8716c2` (F401 unused-import cleanup only — no behavior change). Prior commits `11edeb4`/`00b289b` (device auth session tokens — already covered in #95), `f1a3cbe` (GOOGLE_SA/RequirementType — open PR #94).

**Open PRs checked:** #94 covers GOOGLE_SA/RequirementType/IntegrationConfigDTO — no overlap. #92 (draft) covers IntegrationScope/entitlement/TRIGGER — no overlap.

**Gaps filled this run:**

- `DeviceAuthResponse` init payload shape (user_code, device_code, poll/approve URLs, timing)
- `UpdateIntegrationScopesRequest` TypedDict for OAuth scope expansion
- `IntegrationDTO.service_account_email` with `IntegrationProvider.GOOGLE_SA` / `SERVICE_ACCOUNT` auth
- `IntegrationAuthType.SERVICE_ACCOUNT` enum stability

**Files:** `tests/test_types.py`, `tests/test_imports.py`

## 2026-07-08 (push dev @ 11edeb4, device auth session token types)

**Recent changes reviewed:** `11edeb4` (DeviceTokenKind enum, DeviceAuthInitRequest.token_kind, DeviceAuthPollResponse.session_token).

**Open PRs checked:** #94 (draft) covers `f1a3cbe` GOOGLE_SA/RequirementType — no overlap. #92 (draft) covers IntegrationScope/entitlement limits from `9c89152` — no overlap. #93 is lint-only.

**Gaps filled this run:**

- `DeviceTokenKind` enum (`session`, `api_key`) for CLI credential selection
- `DeviceAuthInitRequest` TypedDict with optional `token_kind`
- `DeviceAuthPollResponse` session-token vs legacy API-key credential paths

**Files:** `tests/test_types.py`, `tests/test_imports.py`

## 2026-06-14 (push main @ 9b57a33, wait_for_completion + StreamManager gaps)

**Recent changes reviewed:** `9b57a33` (stream GET-reconcile, partial NDJSON, instance/suggest types — already covered), `caa2b79` (v2 wait_for_completion timeout + GET reconciliation escape hatch).

**Open PRs checked:** none open — no overlapping test work.

**Gaps filled this run:**

- `wait_for_completion` / async: GET-reconcile when stream ends without terminal event; `TimeoutError` when task stays non-terminal; immediate FAILED/CANCELLED from stream; GET-reconcile FAILED after stream end
- `AsyncTaskStream` GET-reconcile FAILED/CANCELLED parity with sync
- `StreamManager` routes `{data, fields}` partial envelopes to `on_partial_data` (falls back to `on_data`)
- `AsyncInference.upload_file()` from filesystem path (also fixed broken `aiofiles.open` usage)

**Files:** `tests/test_client.py`, `src/inferencesh/client.py` (aiofiles bugfix)

## 2026-06-14 (push main @ 300c884, stream reconcile + typegen field gaps)

**Recent changes reviewed:** `300c884` (KnowledgeType/async RFC 9457 — already covered), `28cd082`/`eff7d5e` (InstanceTypeDTO fields), `fb56d97` (Suggest types), `caa2b79` (v2 stream reconcile escape hatch).

**Open PRs checked:** none open — no overlapping test work.

**Gaps filled this run:**

- `TaskStream` / `AsyncTaskStream` GET-reconcile when NDJSON stream ends without terminal event (COMPLETED/FAILED/CANCELLED)
- `_iter_ndjson` unwraps `{data, fields}` partial update envelope
- Async RFC 9457 parity: `detail` over `title`, `message` fallback
- `InstanceTypeConfiguration.gpu_manufacturer` / `nvlink`, `InstanceTypeDTO.cloud_logo_url`
- `SuggestRequest` / `SuggestResponse` / `SuggestResult` TypedDict shape

**Files:** `tests/test_client.py`, `tests/test_types.py`, `tests/test_imports.py`

## 2026-05-23 (push main @ c071c14, merge suggest + billing tests)

**Recent changes reviewed:** `c071c14` (merge conflict: suggest + billing type imports), `7ed8d78`/`2965cbc` (tests already merged for ChatInput, RFC 9457, billing enums).

**Open PRs checked:** none open — PRs #66 and #77 already merged; no overlapping test work.

**Gaps filled this run:**

- `KnowledgeType` / `KnowledgeLifecycle` enum stability (commit `510d3d9`)
- Async client RFC 9457 `detail` / `title` error parsing parity with sync (commit `bedb60e`)
- Sync `message` fallback when `detail` and `title` are absent
- `AsyncInference._headers()` sends `X-API-Version: 2`

**Files:** `tests/test_types.py`, `tests/test_client.py`, `tests/test_imports.py`

## 2026-05-22 (push main @ 76f33e6, v0.7.9)

**Skipped (open PR #66):** billing/knowledge/oauth/notification enum tests from `0c6e23a` — draft PR `cursor/test-coverage-automation-4901` already covers those.

**Gaps filled this run:**

- `ChatInput` / `ModelSettings` — nested sampling schema, validation bounds, `build_openai_messages` compatibility (commit `3eda863`)
- RFC 9457 problem+json error parsing — `detail` / `title` fallback in sync client (commit `bedb60e`)
- `X-API-Version: 2` header on requests
- `SuggestRequest` / `SuggestResponse` / `SuggestResult` import smoke (commit `0637e77`)

**Files:** `tests/test_llm.py`, `tests/test_client.py`, `tests/test_imports.py`

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
