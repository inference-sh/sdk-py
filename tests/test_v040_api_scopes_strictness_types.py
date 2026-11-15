"""Vault cleanup, chat strictness, and related v0.40 typegen (f4fa5f1 / v0.40.0).

Sandboxes and agents no longer pin a vault id: inference.sh access is
``api_scopes`` on ``AgentConfigInput``, ``AgentVersionDTO``, and
``CreateSandboxRequest``. Content-guard strictness is wired through chat
settings and ``ChatStrictnessDTO``. Credential vault setup exposes
``CredentialConfigDTO.own_app_scope`` for platform-team apps.
"""

import json
from typing import List, Optional, get_type_hints

from inferencesh.types import (
    AgentConfigInput,
    AgentVersionDTO,
    ChatData,
    ChatSettingsDTO,
    ChatSettingsRequest,
    ChatStrictness,
    ChatStrictnessDTO,
    ContentGuardConfig,
    ContentGuardMode,
    CreateSandboxRequest,
    CredentialConfigDTO,
    CredentialScope,
    ErrorCode,
    PolicySubject,
    RunEndReason,
    Scope,
)

CHAT_STRICTNESS_WIRE = frozenset({"watch", "ask", "strict"})
POLICY_SUBJECT_WIRE = frozenset(
    {"remote", "chat", "agent", "user", "team", "org", "platform"},
)


def test_chat_strictness_enum_matches_api_wire():
    assert {m.value for m in ChatStrictness} == CHAT_STRICTNESS_WIRE
    assert ChatStrictness.WATCH.value == "watch"
    assert ChatStrictness.STRICT.value == "strict"


def test_policy_subject_enum_matches_api_wire():
    assert {m.value for m in PolicySubject} == POLICY_SUBJECT_WIRE
    assert PolicySubject.TEAM.value == "team"
    assert PolicySubject is not CredentialScope


def test_agent_config_uses_api_scopes_not_vault_id():
    hints = get_type_hints(AgentConfigInput)
    assert "vault_id" not in hints
    assert hints["api_scopes"] == List[Scope]

    cfg: AgentConfigInput = {
        "name": "sandbox-spawner",
        "api_scopes": [Scope.APPS_EXECUTE, Scope.FILES_WRITE],
    }
    assert cfg["api_scopes"][0] is Scope.APPS_EXECUTE
    payload = json.loads(json.dumps(cfg, default=lambda v: v.value if hasattr(v, "value") else v))
    assert payload["api_scopes"] == ["apps:execute", "files:write"]


def test_create_sandbox_request_uses_api_scopes_not_vault_id():
    hints = get_type_hints(CreateSandboxRequest)
    assert "vault_id" not in hints
    assert hints["api_scopes"] == List[Scope]

    req: CreateSandboxRequest = {
        "remote_id": "remote_01",
        "api_scopes": [Scope.APPS_READ],
    }
    assert req["api_scopes"] == [Scope.APPS_READ]


def test_agent_version_dto_uses_api_scopes_not_vault_id():
    hints = get_type_hints(AgentVersionDTO)
    assert "vault_id" not in hints
    assert hints["api_scopes"] == List[Scope]

    version: AgentVersionDTO = {
        "id": "ver_1",
        "api_scopes": [Scope.APPS_EXECUTE],
    }
    assert version["api_scopes"][0].value == "apps:execute"


def test_content_guard_and_chat_settings_carry_strictness():
    guard_hints = get_type_hints(ContentGuardConfig)
    assert guard_hints["strictness"] == Optional[ChatStrictness]

    guard: ContentGuardConfig = {
        "mode": ContentGuardMode.CONTENT_GUARD_SHADOW,
        "strictness": ChatStrictness.ASK,
    }
    assert guard["strictness"] is ChatStrictness.ASK

    settings_req_hints = get_type_hints(ChatSettingsRequest)
    assert settings_req_hints["strictness"] == Optional[ChatStrictness]

    settings: ChatSettingsRequest = {"strictness": ChatStrictness.STRICT}
    assert settings["strictness"].value == "strict"

    settings_dto_hints = get_type_hints(ChatSettingsDTO)
    assert settings_dto_hints["strictness"] == Optional[ChatStrictness]


def test_chat_data_strictness_is_required_level_when_set():
    hints = get_type_hints(ChatData)
    assert hints["strictness"] is ChatStrictness

    data: ChatData = {"strictness": ChatStrictness.WATCH}
    assert data["strictness"] is ChatStrictness.WATCH


def test_chat_strictness_dto_effective_resolution_shape():
    hints = get_type_hints(ChatStrictnessDTO)
    assert hints["chat"] == Optional[ChatStrictness]
    assert hints["agent_default"] is ChatStrictness
    assert hints["minimum"] == Optional[ChatStrictness]
    assert hints["minimum_set_by"] is PolicySubject
    assert hints["delegated"] == Optional[ChatStrictness]
    assert hints["flagged"] is bool
    assert hints["effective"] is ChatStrictness

    dto: ChatStrictnessDTO = {
        "chat_id": "chat_1",
        "chat": ChatStrictness.ASK,
        "agent_default": ChatStrictness.WATCH,
        "minimum": ChatStrictness.STRICT,
        "minimum_set_by": PolicySubject.TEAM,
        "delegated": None,
        "flagged": True,
        "effective": ChatStrictness.STRICT,
    }
    assert dto["minimum_set_by"] is PolicySubject.TEAM
    assert dto["effective"] is ChatStrictness.STRICT
    wire = json.loads(json.dumps(dto, default=lambda v: v.value if hasattr(v, "value") else v))
    assert wire["effective"] == "strict"
    assert wire["minimum_set_by"] == "team"
    assert wire["flagged"] is True


def test_credential_config_own_app_scope_for_platform_apps():
    hints = get_type_hints(CredentialConfigDTO)
    assert hints["own_app_scope"] is CredentialScope

    cfg: CredentialConfigDTO = {
        "slug": "github",
        "provider": "github",
        "own_app_scope": CredentialScope.PLATFORM,
    }
    assert cfg["own_app_scope"] is CredentialScope.PLATFORM
    payload = json.loads(
        json.dumps(cfg, default=lambda v: v.value if hasattr(v, "value") else v),
    )
    assert payload["own_app_scope"] == "platform"


def test_v040_error_codes_and_run_end_reason_content_flagged():
    assert ErrorCode.FILE_IN_USE.value == "file_in_use"
    assert ErrorCode.LISTING_NOT_LIVE.value == "listing_not_live"
    assert RunEndReason.CONTENT_FLAGGED.value == "content_flagged"
    assert RunEndReason.CONTENT_FLAGGED.value not in {
        RunEndReason.REFUSAL.value,
        RunEndReason.NO_REPLY.value,
    }