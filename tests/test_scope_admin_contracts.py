"""Scope catalog, admin elevation, and embed visitor_reads (b7b348f / bd09be9 / b16277a).

Guards shapes clients use for GET /scopes, GET /me, 403 scope/sign-in errors,
API key grants, and agent version embed permissions — easy to break in typegen
without runtime failures until a client mis-handles an error or omits a field.
"""

from typing import List, get_type_hints

from inferencesh.models.errors import APIError
from inferencesh.types import (
    AdminElevationDropResponse,
    AdminElevationStatus,
    AgentVersionDTO,
    ApiKeyDTO,
    ErrorCode,
    MeResponse,
    Scope,
    ScopeDefinition,
    ScopeGroup,
    ScopeGroupDefinition,
    ScopePreset,
    ScopeRefusedMeta,
    ScopesResponse,
)


def test_scope_definition_flags_for_ui_and_policy():
    hints = get_type_hints(ScopeDefinition)
    assert hints["value"] is Scope
    assert hints["group"] is ScopeGroup
    assert hints["sign_in_only"] is bool
    assert hints["not_for_apps"] is bool
    assert hints["costs_credits"] is bool
    assert hints["automation"] is bool

    entry: ScopeDefinition = {
        "value": Scope.APPROVALS_WRITE,
        "label": "Approve tools",
        "sign_in_only": True,
        "not_for_apps": True,
        "costs_credits": False,
        "automation": False,
    }
    assert entry["sign_in_only"] is True


def test_scopes_response_includes_account_scopes_and_login_preset():
    hints = get_type_hints(ScopesResponse)
    assert hints["scopes"] == List[ScopeDefinition]
    assert hints["groups"] == List[ScopeGroupDefinition]
    assert hints["account_scopes"] == List[ScopeDefinition]
    assert hints["login_preset"] is ScopePreset

    group_hints = get_type_hints(ScopeGroupDefinition)
    assert group_hints["public_rows"] is bool
    assert group_hints["staff_only"] is bool

    preset_hints = get_type_hints(ScopePreset)
    assert preset_hints["default"] is bool
    assert preset_hints["grants"] == List[Scope]

    payload: ScopesResponse = {
        "scopes": [],
        "groups": [],
        "presets": [],
        "account_scopes": [{"value": Scope.APPROVALS_WRITE, "sign_in_only": True}],
        "login_preset": {
            "id": "login",
            "scopes": [Scope.APPROVALS_WRITE],
            "grants": [Scope.APPROVALS_WRITE],
            "default": True,
        },
    }
    assert payload["login_preset"]["grants"][0] is Scope.APPROVALS_WRITE


def test_me_response_exposes_held_scopes_and_platform_power():
    hints = get_type_hints(MeResponse)
    assert hints["scopes"] == List[Scope]
    assert hints["platform_power"] is bool

    me: MeResponse = {
        "platform_power": True,
        "scopes": [Scope.APPROVALS_WRITE],
        "needs_username": False,
    }
    assert me["platform_power"] is True


def test_api_key_dto_grants_expanded_scopes():
    hints = get_type_hints(ApiKeyDTO)
    assert hints["scopes"] == List[Scope]
    assert hints["grants"] == List[Scope]

    key: ApiKeyDTO = {
        "name": "ci",
        "scopes": [],
        "grants": [Scope.APPROVALS_WRITE],
    }
    assert key["grants"][0] is Scope.APPROVALS_WRITE


def test_agent_version_visitor_reads_for_embeds():
    hints = get_type_hints(AgentVersionDTO)
    assert hints["visitor_reads"] == List[ScopeGroup]

    version: AgentVersionDTO = {
        "id": "ver_embed",
        "visitor_reads": [ScopeGroup.KNOWLEDGE, ScopeGroup.FILES],
    }
    assert version["visitor_reads"][0] is ScopeGroup.KNOWLEDGE


def test_scope_refused_meta_typed_for_insufficient_scope_errors():
    hints = get_type_hints(ScopeRefusedMeta)
    assert hints["required_scope"] is Scope

    meta: ScopeRefusedMeta = {"required_scope": Scope.APPROVALS_WRITE}
    assert meta["required_scope"] is Scope.APPROVALS_WRITE


def test_admin_elevation_status_and_drop_response_shapes():
    status_hints = get_type_hints(AdminElevationStatus)
    assert status_hints["elevated"] is bool
    assert status_hints["admin_until"] == str | None

    drop_hints = get_type_hints(AdminElevationDropResponse)
    assert drop_hints["dropped"] is bool


def test_error_codes_for_sign_in_scope_and_admin_elevation():
    assert ErrorCode.REQUIRES_SIGN_IN.value == "requires_sign_in"
    assert ErrorCode.INSUFFICIENT_SCOPE.value == "insufficient_scope"
    assert ErrorCode.ADMIN_SCOPES_NOT_APPROVED.value == "admin_scopes_not_approved"
    assert ErrorCode.ADMIN_SESSION_REQUIRED.value == "admin_session_required"
    assert ErrorCode.BROWSER_SESSION_REQUIRED.value == "browser_session_required"


def test_api_error_code_reads_insufficient_scope_from_problem_json():
    body = (
        '{"type":"https://api.inference.sh/errors/insufficient_scope",'
        '"status":403,"detail":"missing scope","meta":{"required_scope":"approvals:write"}}'
    )
    err = APIError(403, "missing scope", response_body=body)
    assert err.code == ErrorCode.INSUFFICIENT_SCOPE
