# Coverage automation runs

## 2026-08-19 (push dev @ c601ad4, remove A2UIHTML component type)

**Recent changes reviewed:** `c601ad4` (regen: remove `A2UIHTML` component type and `htmlContent` field from `A2UIComponent`). `0e3d4e3` (track uv.lock — build infra only). `5e8d5ec` (`AuthResponse.is_new`). `9ee7459` (`llm_types_gen` BaseModel migration).

**Open PRs checked:** #255 (`cursor/missing-test-coverage-15f4`) — AuthResponse.is_new, llm_types_gen BaseModel, A2UI widget tests (includes stale `A2UIHTML` entry); not duplicated. #252 — TypedDict wire contracts (stale after BaseModel migration). #249 — assistant tool_calls content=null.

**Gaps filled this run:**

- Replaced stale `WidgetNodeType` tests (26 failures on `dev`) with `A2UIComponentType` enum stability
- Regression guard: `A2UIHTML` enum member and `htmlContent` field must stay removed after c601ad4
- `Widget = A2UISurface` alias, flat adjacency `A2UISurface` shape, and `ToolInvocationDTO.widget` interactive payloads

**Files:** `tests/test_types.py`, `tests/test_imports.py`

**Validation:** `pytest tests/` — pending.

## 2026-08-01 (push dev @ cd4152f, stream termination via active_run.state)

**Recent changes reviewed:** `45608aa` (feat: migrate stream termination to `active_run.state` — `Agent.stream_all()` now stops when `active_run.state` is not `working`/`submitted`, instead of checking the derived `status` field). `cd4152f` (version bump only).

**Open PRs checked:** #170 (`cursor/missing-test-coverage-a9e5`) — `AgentRunState`/`InterruptReason` type guards (no overlap with production `stream_all` logic). #168 — `EngineStatus.RESTARTING`. #166 — `Metadata.gpu_ids`. #163 — Metadata identity fields. #161 / #159 — scheduled publishing / `AvailabilityResponse`.

**Gaps filled this run:**

- `Agent.stream_all()` termination via `active_run.state` (not legacy `status` field)
- Continues streaming while `active_run.state` is `working` or `submitted`
- Stops on all terminal run states (`completed`, `failed`, `canceled`, `input_required`, `auth_required`, `rejected`)
- Stops when `active_run` is absent (run finished)
- Regression guard: `status: "idle"` alone must not terminate if `active_run.state` is still `working`

**Files:** `tests/test_agent.py`

**Validation:** `pytest tests/test_agent.py` — 34 passed.

## 2026-07-26 (push dev @ 8e90e52, PlanVersionDTO + device auth PKCE + AppStatus)

**Recent changes reviewed:** `8e90e52` (device auth PKCE fields on `DeviceAuthInitRequest`). `eceba3c` (PlanVersionDTO monthly/yearly amounts; `SkillDTO`/`KnowledgeDTO` uses/installs). `06ecea2` (`PlanDTO.active_version` replaces flat pricing and `prices` list; `AppStatus` on `AppDTO`).

**Open PRs checked:** #154 (draft, `cursor/missing-test-coverage-ea8b`) — overlaps on corrupted `required_plan_ids` stub, `ScopePreset.hidden`, and `AppPricing.description_rendered`; this run includes those fixes plus new typegen gaps.

**Gaps filled this run:**

- Restored `PlanDTO.required_plan_ids` prerequisite chain test body (batch merge #126–#153 left docstring-only stub)
- `PlanVersionDTO` monthly/yearly amounts and `PlanDTO.active_version` embedded pricing shape
- Regression guard: `PlanDTO` must not reintroduce `price_monthly`/`price_yearly`/`prices` top-level fields
- `DeviceAuthInitRequest` PKCE `code_challenge` / `code_challenge_method` for secure CLI login
- `AppStatus` enum (`active`, `maintenance`, `deprecated`, `retired`) and `AppDTO` status fields
- `SkillDTO` / `KnowledgeDTO` `uses` and `installs` catalog popularity metrics
- `ScopePreset.hidden=True` admin-only presets; `AppPricing.description_rendered` human-readable pricing

**Files:** `tests/test_types.py`, `tests/test_imports.py`

**Validation:** `pytest tests/test_types.py tests/test_imports.py` — 594 passed.

## 2026-07-14 (push dev @ c5ba7b7, merge PR #125 Scope/EngineStatus coverage)

**Recent changes reviewed:** `c5ba7b7` (merge PR #125: Scope catalog, SetupActionType, EngineStatus, probe_video export — already merged). `b8502d3`/`3616277`/`c6a3241` (EngineStatus tests, lint-only, probe_video `__all__`).

**Open PRs checked:** None open. Remote branches `849c`/`9290`/`e655`/`be5d` restore overlapping Scope/SetupActionType tests now merged in #125 — no duplicate work.

**Gaps filled this run:**

- `AppCategory` enum including `_3D` digit-prefix member (gotypegen acronym regression guard)
- `Visibility` enum for public/private/unlisted resource access
- `ChatStatus` / `ChatMessageRole` / `ChatMessageStatus` / `ChatMessageContentType` chat lifecycle enums
- `PlanStepStatus` agent planning progress states
- `FlowRunStatus` IntEnum workflow run lifecycle (numeric values must not shift)
- `ToolInvocationStatus` full lifecycle including `AWAITING_INPUT` (agent client-tool loop)
- `AppSessionStatus` warm worker session lifecycle
- `FilterOperator` search/filter operator tokens for cursor list APIs
- `MetaItemType` output metadata media discriminators
- `ChatDTO` / `FlowRunDTO` / `AppSessionDTO` status field shape
## 2026-07-14 (push dev @ eeb8cd6, v0.7.12 version bump)

**Recent changes reviewed:** `eeb8cd6` (version bump only). `c5ba7b7` (merge PR #125: Scope catalog, SetupActionType, EngineStatus, probe_video export — already merged).

**Open PRs checked:** #126 (draft) covers chat/workflow/app-store enum stability (`ChatStatus`, `FlowRunStatus`, `FilterOperator` enum, etc.) — no overlap; this run targets team/CMS/billing/widget gaps instead.

**Gaps filled this run:**

- `GPUType` full vendor list for worker/instance GPU config
- `PageStatus` / `PageType` CMS publish lifecycle (IntEnum + doc/blog/page kinds)
- `ProjectType` workspace grouping (`agent`, `app`, `flow`, `other`)
- `TeamInviteStatus` / `TeamRole` / `TeamType` / `TeamStatus` team management enums
- `ContentRating` moderation ratings with `CONTENT_` acronym prefix guard
- `UsageEventResourceTier` private vs cloud billing tier
- `Infra` task routing (`private`, `cloud`, `private_first`)
- `TaskLogType` IntEnum log stream discriminators
- `Role` permission tokens
- `EntitlementType` / `EnforcementMode` plan limit vs feature gate enums
- `ToolType` full lifecycle (all eight tool kinds)
- `WidgetNodeType` agent widget tree discriminators
- `PageDTO` / `ProjectDTO` / `TeamInviteDTO` / `FileDTO` / `UsageEventDTO` status field shapes
- `Filter` / `CursorListRequest` list API filter envelope (uses `FilterOperator`)

**Files:** `tests/test_types.py`, `tests/test_imports.py`
## 2026-07-14 (push dev @ bd4cfaa, EngineDTO.engine_version + GraphEdgeType.SUPERSEDES)

**Recent changes reviewed:** `bd4cfaa` (typegen regen: `engine_version` on `EngineDTO`, `SUPERSEDES` on `GraphEdgeType`). `eeb8cd6` version bump only.

**Open PRs checked:** #128 (team/CMS/billing/widget enums on `cursor/missing-test-coverage-e699`), #126 (chat/workflow/app-store enums on `cursor/missing-test-coverage-e307`) — no overlap with this run's gaps.

**Gaps filled this run:**

- `GraphEdgeType.SUPERSEDES` workflow edge kind for version/supersession graph links
- `EngineDTO.engine_version` top-level version field for engine dashboard/API responses
## 2026-07-17 (push dev @ a156502, NotificationType.DATA_EXPORT)

**Recent changes reviewed:** `a156502` (typegen regen: `NotificationType.DATA_EXPORT` for data-export completion notifications). `a386bf7` README copy only.

**Open PRs checked:** #131 (`GraphEdgeType.SUPERSEDES`, `EngineDTO.engine_version` on `cursor/missing-test-coverage-99ec`), #128 (team/CMS/billing/widget enums), #126 (chat/workflow/app-store enums) — no overlap; this run covers the new notification kind only.

**Gaps filled this run:**

- `NotificationType.DATA_EXPORT` for data-export job completion/failure notification routing
## 2026-07-17 (push dev @ fb75385, SuggestResult.tag field)

**Recent changes reviewed:** `fb75385` (typegen regen: optional `tag` on `SuggestResult` for subscription/category grouping in suggest UI). `a156502` (`NotificationType.DATA_EXPORT` — open PR #133). `bd4cfaa` (`EngineDTO.engine_version`, `GraphEdgeType.SUPERSEDES` — open PR #131).

**Open PRs checked:** #133 (DATA_EXPORT), #131 (engine_version/SUPERSEDES), #128 (team/CMS/billing/widget), #126 (chat/workflow/app-store) — no overlap with SuggestResult.tag.

**Gaps filled this run:**

- `SuggestResult.tag` optional category label on suggest results (e.g. subscription stats grouping)
- `SuggestResult.command` CLI invocation string on suggest results (documented field, same TypedDict)
## 2026-07-18 (push dev @ d7aa6cb, drop stripe_subscription_id from SubscriptionDTO)

**Recent changes reviewed:** `d7aa6cb` (typegen regen: remove `stripe_subscription_id` from `SubscriptionDTO` — Stripe IDs are internal, not part of the public SDK surface). `fb75385` (`SuggestResult.tag` — open PR #137). `a156502` (`NotificationType.DATA_EXPORT` — open PR #133; `EngineDTO.engine_version` / `GraphEdgeType.SUPERSEDES` — open PR #131).

**Open PRs checked:** #137 (SuggestResult.tag), #133 (DATA_EXPORT), #131 (engine_version/SUPERSEDES), #128 (team/CMS/billing/widget), #126 (chat/workflow/app-store) — no overlap with SubscriptionDTO stripe field removal.

**Gaps filled this run:**

- `SubscriptionDTO` billing response shape (`team_id`, `plan_id`, `interval`, `status`, period/trial/credits fields)
- Regression guard: `stripe_subscription_id` must not reappear on `SubscriptionDTO` after backend typegen cleanup

**Files:** `tests/test_types.py`
## 2026-07-20 (push dev @ b525449, plan add-ons INF-588)

**Recent changes reviewed:** `b525449` (typegen regen: `PlanType` enum, `PlanDTO.plan_type`, `EntitlementSource.ADDON`, `EntitlementDTO.team_plan_id`, `scope` on knowledge/suggest types). `3883610` (`AppStoreListingDTO.required_feature` for feature-gated listings). `d7aa6cb` (`stripe_subscription_id` removal — covered by open PR #138).

**Open PRs checked:** #138 (SubscriptionDTO), #137 (SuggestResult.tag), #133 (DATA_EXPORT), #131 (SUPERSEDES/engine_version), #128 (team/CMS/billing/widget), #126 (chat/workflow/app-store) — no overlap.

**Gaps filled this run:**

- `PlanType` enum (`base`, `addon`) for distinguishing subscription tiers vs add-on plans
- `PlanDTO.plan_type` on base and add-on plan catalog entries
- `EntitlementSource.ADDON` for entitlements granted by purchased add-ons
- `EntitlementDTO.team_plan_id` linking entitlements to the add-on plan that granted them
- `AppStoreListingDTO.required_feature` for feature-gated app store listings
- `SuggestRequest.scope` for scoping suggest queries to team/public catalogs
- `KnowledgeVersionInput` / `KnowledgeVersionDTO.scope` for namespace-scoped knowledge content
## 2026-07-21 (push dev @ c23f1ce, RefRouteMode + feature:seedance)

**Recent changes reviewed:** `c23f1ce` (typegen regen: `RefRouteMode` enum, `RefRouteDTO.mode`, `EntitlementResource.RESOURCE_FEATURE_SEEDANCE`).

**Open PRs checked:** #140 (plan add-ons/INF-588), #138 (SubscriptionDTO), #137 (SuggestResult.tag), #133 (DATA_EXPORT), #131 (SUPERSEDES/engine_version), #128 (team/CMS/billing/widget), #126 (chat/workflow/app-store) — no overlap.

**Gaps filled this run:**

- `RefRouteMode` enum (`rewrite`, `redirect`) for alias routing behavior
- `RefRouteDTO.mode` TypedDict field for rewrite vs redirect ref routes
- `EntitlementResource.RESOURCE_FEATURE_SEEDANCE` (`feature:seedance`) video-generation feature gate

**Files:** `tests/test_types.py`, `tests/test_imports.py`
## 2026-07-22 (push dev @ f60c176, GraphEdgeType INPUT/OUTPUT)

**Recent changes reviewed:** `f60c176` (typegen regen: `GraphEdgeType.INPUT` / `OUTPUT` for workflow graph I/O edges). `c23f1ce` (RefRouteMode, `feature:seedance`) — covered by open PR #142.

**Open PRs checked:** #142 (RefRouteMode/seedance), #140 (plan add-ons/INF-588), #138 (SubscriptionDTO), #137 (SuggestResult.tag), #133 (DATA_EXPORT), #131 (SUPERSEDES/engine_version), #128 (team/CMS/billing/widget), #126 (chat/workflow/app-store) — no overlap with INPUT/OUTPUT.

**Gaps filled this run:**

- `GraphEdgeType.INPUT` / `OUTPUT` workflow graph edge kinds for data-flow I/O links between nodes
## 2026-07-22 (push dev @ 357a038, PlanDTO.required_plan_ids)

**Recent changes reviewed:** `357a038` (typegen regen: `required_plan_ids` on `PlanDTO` for plan prerequisite chains). `f60c176` (`GraphEdgeType.INPUT`/`OUTPUT` — open PR #143).

**Open PRs checked:** #143 (GraphEdgeType INPUT/OUTPUT), #142 (RefRouteMode/seedance), #140 (plan add-ons/INF-588 — covers `plan_type` but not `required_plan_ids`), #138–#126 — no overlap with `required_plan_ids`.

**Gaps filled this run:**

- `PlanDTO.required_plan_ids` prerequisite plan ID list for add-on eligibility (empty for base plans, populated for add-ons)

**Files:** `tests/test_types.py`
## 2026-07-22 (push dev @ 9025916, EntitlementErrorMeta + PlanDTO.required_plan_names)

**Recent changes reviewed:** `9025916` (typegen regen: `EntitlementErrorMeta` for structured entitlement error payloads; `required_plan_names` on `PlanDTO`). `357a038` (`required_plan_ids` — open PR #145).

**Open PRs checked:** #145 (`required_plan_ids`), #143 (GraphEdgeType INPUT/OUTPUT), #142 (RefRouteMode/seedance), #140–#126 — no overlap with `EntitlementErrorMeta` or `required_plan_names`.

**Gaps filled this run:**

- `EntitlementErrorMeta` limit-exceeded and feature-gate error payload shapes (usage, upgrade hints, add-on plan pricing)
- `PlanDTO.required_plan_names` human-readable prerequisite plan names for add-on eligibility UIs
## 2026-07-22 (push dev @ 7c9f333, cost estimation + scope preset fields)

**Recent changes reviewed:** `7c9f333` (typegen regen: `EstimateCostRequest`/`EstimateCostResponse`, `AppPricing.estimate`/`estimable`). `6c0973d` (`ScopePreset.summary`/`hidden` for standard read-only preset UI).

**Open PRs checked:** #148 (EntitlementErrorMeta), #145 (`required_plan_ids`), #143 (GraphEdgeType INPUT/OUTPUT), #142 (RefRouteMode/seedance), #140–#126 — no overlap with cost estimation or scope preset summary/hidden.

**Gaps filled this run:**

- `EstimateCostRequest` shape for POST `/store/apps/{appId}/estimate`
- `EstimateCostResponse` confidence variants (`exact`, `range`, `unknown`) with microcents, min/max, or `depends_on`
- `AppPricing.estimate` CEL expression and `estimable` flag for pre-execution pricing
- `ScopePreset.summary` bullet labels and `hidden` flag on scope catalog presets

**Files:** `tests/test_types.py`, `tests/test_imports.py`
## 2026-07-22 (push dev @ 07c8ad1, estimate_error + PlanDTO.stackable)

**Recent changes reviewed:** `07c8ad1` (typegen: `EstimateCostResponse.estimate_error` for failed CEL evaluation; `PlanDTO.stackable` for add-on vs base tier plans).

**Open PRs checked:** #150 covers cost estimation types (`EstimateCostRequest`/`Response`, `AppPricing`) and scope preset `summary`/`hidden` but not `estimate_error`. #148/#145 cover `PlanDTO.required_plan_names`/`required_plan_ids` but not `stackable`. No overlap.

**Gaps filled this run:**

- `EstimateCostResponse.estimate_error` when estimate expression exists but CEL evaluation fails
- `PlanDTO.stackable` flag distinguishing base tiers from stackable add-ons

**Files:** `tests/test_types.py`

## 2026-07-14 (push dev @ b8502d3, EngineStatus + probe_video __all__)

**Recent changes reviewed:** `b8502d3` (EngineStatus enum coverage — merged). `3616277` (lint-only). `c6a3241` (`probe_video` added to `__all__` for wildcard import parity).

**Open PRs checked:** Remote branches `cursor/missing-test-coverage-849c`, `9290`, `e655` restore overlapping Scope/SetupActionType tests dropped in ping-pong commits — those gaps filled here to avoid duplicate PR work.

**Gaps filled this run:**

- API key `Scope` enum stability (`agents:read`, `apikeys:write`, etc.) for permission checks
- `ScopeGroup` catalog groups for GET `/scopes` UI rendering
- `AuthSessionDTO.scopes` session listing shape
- `ScopesResponse` / `ScopeDefinition` / `ScopePreset` catalog TypedDict shape
- `SetupActionType` enum for 412 requirement actions (`add_secret`, `connect`, `add_scopes`)
- `SetupAction` TypedDict `provider_name` / `scope_descriptions` for setup UIs
- `RequirementError` propagation of nested setup-action UI fields
- `probe_video` public export smoke test (regression guard for `c6a3241`)

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
