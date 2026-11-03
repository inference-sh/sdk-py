"""Step-up auth, web access restriction, and team member add wire (2c8a601).

Security release types: StepUpAction on OAuth approve and admin flows,
TeamMemberAddResultDTO outcomes, FeatureAccess for gates, device-auth
scope requests, and sandbox credential declarations on agents/sandboxes.
"""

from typing import List, Optional, get_type_hints

import pytest

from inferencesh.models.errors import APIError
from inferencesh.types import (
    CreateSandboxRequest,
    CredentialRequirement,
    DeviceAuthInitRequest,
    EntitlementResource,
    ErrorCode,
    FeatureAccess,
    InternalToolsConfig,
    MeResponse,
    OAuthAuthorizeInfoResponse,
    Scope,
    StepUpAction,
    TeamInviteDTO,
    TeamMemberAddOutcome,
    TeamMemberAddResultDTO,
    TeamMemberDTO,
)


@pytest.mark.parametrize(
    ("member", "wire"),
    [
        (StepUpAction.STEP_UP_EXPORT, "export"),
        (StepUpAction.STEP_UP_DELETE, "delete"),
        (StepUpAction.STEP_UP_FACTOR_ENROLL, "factor_enroll"),
        (StepUpAction.STEP_UP_FACTOR_CHANGE, "factor_change"),
        (StepUpAction.STEP_UP_DEVICE_APPROVE, "device_approve"),
        (StepUpAction.STEP_UP_ADMIN_ELEVATION_APPROVE, "admin_elevation_approve"),
        (StepUpAction.STEP_UP_O_AUTH_APPROVE, "oauth_approve"),
        (StepUpAction.STEP_UP_API_KEY_CREATE, "api_key_create"),
        (StepUpAction.STEP_UP_SECRET_REVEAL, "secret_reveal"),
        (StepUpAction.STEP_UP_ADMIN_SESSION, "admin_session"),
        (StepUpAction.STEP_UP_ADMIN_SENSITIVE, "admin_sensitive"),
        (StepUpAction.STEP_UP_TEAM_MEMBER_CHANGE, "team_member_change"),
        (StepUpAction.STEP_UP_TEAM_SSO_CHANGE, "team_sso_change"),
    ],
)
def test_step_up_action_wire_values(member, wire):
    assert member.value == wire


def test_team_member_add_outcome_wire_values():
    assert TeamMemberAddOutcome.TEAM_MEMBER_ADD_ADDED.value == "added"
    assert TeamMemberAddOutcome.TEAM_MEMBER_ADD_INVITED.value == "invited"


def test_team_member_add_result_dto_shape():
    hints = get_type_hints(TeamMemberAddResultDTO)
    assert hints["outcome"] is TeamMemberAddOutcome
    assert hints["member"] == Optional[TeamMemberDTO]
    assert hints["invite"] == Optional[TeamInviteDTO]

    added: TeamMemberAddResultDTO = {
        "outcome": TeamMemberAddOutcome.TEAM_MEMBER_ADD_ADDED,
        "member": {"id": "tm_1", "user_id": "u_1", "role": "member"},
    }
    assert added["outcome"] is TeamMemberAddOutcome.TEAM_MEMBER_ADD_ADDED

    invited: TeamMemberAddResultDTO = {
        "outcome": TeamMemberAddOutcome.TEAM_MEMBER_ADD_INVITED,
        "invite": {"id": "inv_1", "email": "a@example.com", "status": "pending"},
    }
    assert invited["invite"]["email"] == "a@example.com"


def test_feature_access_carries_gate_decision():
    hints = get_type_hints(FeatureAccess)
    assert hints["resource"] is EntitlementResource
    assert hints["allowed"] is bool

    row: FeatureAccess = {
        "resource": EntitlementResource.RESOURCE_FEATURE_SANDBOXES,
        "allowed": True,
    }
    assert row["resource"] is EntitlementResource.RESOURCE_FEATURE_SANDBOXES


def test_oauth_authorize_info_exposes_step_up_fields():
    hints = get_type_hints(OAuthAuthorizeInfoResponse)
    assert hints["step_up_required"] is bool
    assert hints["step_up_action"] is StepUpAction
    assert hints["step_up_target"] is str

    info: OAuthAuthorizeInfoResponse = {
        "client_id": "cli",
        "scopes": [Scope.APPS_READ],
        "step_up_required": True,
        "step_up_action": StepUpAction.STEP_UP_O_AUTH_APPROVE,
        "step_up_target": "team|tm_abc",
    }
    assert info["step_up_action"] is StepUpAction.STEP_UP_O_AUTH_APPROVE


def test_device_auth_init_request_accepts_requested_scopes():
    hints = get_type_hints(DeviceAuthInitRequest)
    assert hints["scopes"] == List[Scope]

    body: DeviceAuthInitRequest = {
        "scopes": [Scope.ADMIN_READ, Scope.ADMIN_WRITE],
    }
    assert body["scopes"][0] is Scope.ADMIN_READ


def test_me_response_carries_operator_notice_for_restricted_access():
    hints = get_type_hints(MeResponse)
    assert hints["notice"] is str

    me: MeResponse = {"notice": "Use the CLI from this network."}
    assert me["notice"].startswith("Use the CLI")


def test_web_access_restricted_error_code_wire_and_problem_json():
    assert ErrorCode.WEB_ACCESS_RESTRICTED.value == "web_access_restricted"

    body = (
        '{"type":"https://api.inference.sh/errors/web_access_restricted",'
        '"status":403,"detail":"CLI only from this network"}'
    )
    err = APIError(403, "restricted", response_body=body)
    assert err.code == ErrorCode.WEB_ACCESS_RESTRICTED


def test_sandbox_and_agent_declarations_use_credential_requirements():
    agent_hints = get_type_hints(InternalToolsConfig)
    assert agent_hints["sandbox_credentials"] == List[CredentialRequirement]

    sandbox_hints = get_type_hints(CreateSandboxRequest)
    assert sandbox_hints["credentials"] == List[CredentialRequirement]

    req: CredentialRequirement = {"slug": "github-app"}
    cfg: InternalToolsConfig = {"remote": True, "sandbox_credentials": [req]}
    create: CreateSandboxRequest = {"name": "dev", "credentials": [req]}
    assert cfg["sandbox_credentials"][0]["slug"] == "github-app"
    assert create["credentials"] == cfg["sandbox_credentials"]
