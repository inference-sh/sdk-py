"""Redlist access notice and egress grant wire types (09bd3a2 / INF-1173).

The API now refuses redlisted callers with ``access_restricted`` (403) instead
of ``web_access_restricted``, surfaces notice reference/contact on GET /me,
and models per-scope egress login decisions as ``EgressGrantDTO`` on task and
sandbox grant listings. Engines advertise ``egress_grants`` alongside
``egress_pending``.
"""

import json
from typing import Optional, get_type_hints

import pytest

from inferencesh.models.errors import APIError
from inferencesh.types import (
    EgressGrantDTO,
    EgressGrantReason,
    EgressGrantScope,
    EgressGrantSource,
    EgressGrantState,
    EngineCapability,
    ErrorCode,
    MeResponse,
    SandboxCredentialMode,
)


def test_me_response_exposes_redlist_notice_reference_and_contact():
    hints = get_type_hints(MeResponse)
    assert hints["notice"] is str
    assert hints["notice_reference"] is str
    assert hints["notice_contact"] is str

    me: MeResponse = {
        "notice": "Sign in from an approved network.",
        "notice_reference": "POL-42",
        "notice_contact": "security@example.com",
    }
    assert me["notice_reference"] == "POL-42"
    assert me["notice_contact"] == "security@example.com"


@pytest.mark.parametrize(
    ("member", "wire"),
    [
        (ErrorCode.ACCESS_RESTRICTED, "access_restricted"),
        (ErrorCode.WEB_ACCESS_RESTRICTED, "web_access_restricted"),
    ],
)
def test_redlist_error_code_wire_values(member, wire):
    assert member.value == wire


def test_access_restricted_problem_json_maps_through_api_error():
    body = (
        '{"type":"https://api.inference.sh/errors/access_restricted",'
        '"status":403,"detail":"Use the CLI from this network.",'
        '"meta":{"reference":"POL-42","contact":"security@example.com"}}'
    )
    err = APIError(403, "restricted", response_body=body)
    assert err.code == ErrorCode.ACCESS_RESTRICTED


def test_egress_grant_dto_shape_and_sandbox_credential_mode():
    hints = get_type_hints(EgressGrantDTO)
    assert hints["scope"] is EgressGrantScope
    assert hints["state"] is EgressGrantState
    assert hints["source"] is EgressGrantSource
    assert hints["mode"] is SandboxCredentialMode
    assert hints["reason"] is EgressGrantReason
    assert hints["ended_at"] == Optional[str]

    grant: EgressGrantDTO = {
        "id": "egr_1",
        "scope": EgressGrantScope.TASK,
        "scope_id": "task_1",
        "provider": "github-app",
        "mode": SandboxCredentialMode.SANDBOX_CREDENTIAL_ASK,
        "state": EgressGrantState.EGRESS_GRANT_ASKED,
        "source": EgressGrantSource.APP_DECLARED,
        "granted_by": "user_1",
        "host": "api.github.com",
        "created_at": "2026-11-03T00:00:00Z",
        "updated_at": "2026-11-03T00:00:00Z",
    }
    assert grant["state"] is EgressGrantState.EGRESS_GRANT_ASKED


@pytest.mark.parametrize(
    ("member", "wire"),
    [
        (EgressGrantScope.TASK, "task"),
        (EgressGrantScope.SANDBOX, "sandbox"),
    ],
)
def test_egress_grant_scope_wire_values(member, wire):
    assert member.value == wire


@pytest.mark.parametrize(
    ("member", "wire"),
    [
        (EgressGrantState.EGRESS_GRANT_OPEN, "open"),
        (EgressGrantState.EGRESS_GRANT_ASKED, "asked"),
        (EgressGrantState.EGRESS_GRANT_ALLOWED, "allowed"),
        (EgressGrantState.EGRESS_GRANT_DECLINED, "declined"),
        (EgressGrantState.EGRESS_GRANT_ENDED, "ended"),
    ],
)
def test_egress_grant_state_wire_values(member, wire):
    assert member.value == wire


@pytest.mark.parametrize(
    ("member", "wire"),
    [
        (EgressGrantSource.APP_DECLARED, "app_declared"),
        (EgressGrantSource.AGENT_CONFIG, "agent_config"),
        (EgressGrantSource.SANDBOX_CREATE, "sandbox_create"),
        (EgressGrantSource.OWNER_APPROVAL, "owner_approval"),
        (EgressGrantSource.CONNECTED_OFFER, "connected_offer"),
        (EgressGrantSource.RECONNECT, "reconnect"),
    ],
)
def test_egress_grant_source_wire_values(member, wire):
    assert member.value == wire


@pytest.mark.parametrize(
    ("member", "wire"),
    [
        (EgressGrantReason.DECLINED, "declined"),
        (EgressGrantReason.LOGIN_DELETED, "login_deleted"),
        (EgressGrantReason.LOGIN_DISCONNECTED, "login_disconnected"),
        (EgressGrantReason.NOT_OWNER, "not_owner"),
        (EgressGrantReason.EXPIRED_LIFETIME, "expired_lifetime"),
        (EgressGrantReason.SCOPES_MISSING, "scopes_missing"),
        (EgressGrantReason.SCOPE_ENDED, "scope_ended"),
        (EgressGrantReason.REVOKED_BY_OWNER, "revoked_by_owner"),
    ],
)
def test_egress_grant_reason_wire_values(member, wire):
    assert member.value == wire


def test_engine_capability_egress_grants_wire_value():
    assert EngineCapability.EGRESS_GRANTS.value == "egress_grants"


def test_egress_grant_dto_round_trips_enum_fields_on_wire():
    grant: EgressGrantDTO = {
        "id": "egr_2",
        "scope": EgressGrantScope.SANDBOX,
        "scope_id": "sbx_1",
        "provider": "openai",
        "mode": SandboxCredentialMode.SANDBOX_CREDENTIAL_AUTO,
        "state": EgressGrantState.EGRESS_GRANT_ALLOWED,
        "source": EgressGrantSource.OWNER_APPROVAL,
        "credential_id": "cred_1",
        "reason": EgressGrantReason.SCOPE_ENDED,
        "ended_at": "2026-11-03T01:00:00Z",
    }
    wire = json.loads(
        json.dumps(grant, default=lambda o: o.value if hasattr(o, "value") else o)
    )
    assert wire["scope"] == "sandbox"
    assert wire["state"] == "allowed"
    assert wire["source"] == "owner_approval"
    assert wire["mode"] == "auto"
    assert wire["reason"] == "scope_ended"
