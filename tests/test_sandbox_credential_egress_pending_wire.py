"""Sandbox credential modes and egress-pending engine wire (1759590 / INF-1173).

Sandboxes declare logins as ``SandboxCredential`` (requirement fields plus
``mode``: auto at create vs ask on first host reach). Engines advertise
``EngineCapabilityEgressPending``; runs pause with ``InterruptReasonEgressLogin``
until a person approves giving the login through egress resolve.
"""

from typing import List, get_type_hints

import pytest

from inferencesh.types import (
    AuthMethodKind,
    CreateSandboxRequest,
    CredentialRequirement,
    CredentialScope,
    EngineCapability,
    InternalToolsConfig,
    InterruptReason,
    SandboxCredential,
    SandboxCredentialMode,
)


def test_sandbox_credential_mode_wire_values():
    assert SandboxCredentialMode.SANDBOX_CREDENTIAL_AUTO.value == "auto"
    assert SandboxCredentialMode.SANDBOX_CREDENTIAL_ASK.value == "ask"


def test_sandbox_credential_extends_requirement_fields_with_mode():
    req_hints = get_type_hints(CredentialRequirement)
    cred_hints = get_type_hints(SandboxCredential)
    assert set(req_hints) <= set(cred_hints)
    assert cred_hints["mode"] is SandboxCredentialMode
    assert set(cred_hints) - set(req_hints) == {"mode"}


def test_sandbox_credential_accepts_auto_and_ask_entries():
    auto: SandboxCredential = {"slug": "github-app"}
    ask: SandboxCredential = {
        "slug": "openai",
        "scopes": ["chat"],
        "connection_scope": CredentialScope.USER,
        "mode": SandboxCredentialMode.SANDBOX_CREDENTIAL_ASK,
    }
    seeded: SandboxCredential = {
        "slug": "acme",
        "provider": {"name": "Acme"},
        "auth": {"kind": AuthMethodKind.AUTH_METHOD_API_KEY},
        "mode": SandboxCredentialMode.SANDBOX_CREDENTIAL_AUTO,
    }
    assert auto.get("mode") is None
    assert ask["mode"] is SandboxCredentialMode.SANDBOX_CREDENTIAL_ASK
    assert seeded["auth"]["kind"] is AuthMethodKind.AUTH_METHOD_API_KEY


def test_agent_and_create_sandbox_use_sandbox_credentials_not_requirements():
    agent_hints = get_type_hints(InternalToolsConfig)
    assert agent_hints["sandbox_credentials"] == List[SandboxCredential]

    sandbox_hints = get_type_hints(CreateSandboxRequest)
    assert sandbox_hints["credentials"] == List[SandboxCredential]

    cred: SandboxCredential = {
        "slug": "github-app",
        "mode": SandboxCredentialMode.SANDBOX_CREDENTIAL_ASK,
    }
    cfg: InternalToolsConfig = {"remote": True, "sandbox_credentials": [cred]}
    create: CreateSandboxRequest = {"name": "dev", "credentials": [cred]}
    assert cfg["sandbox_credentials"][0]["mode"] is SandboxCredentialMode.SANDBOX_CREDENTIAL_ASK
    assert create["credentials"] == cfg["sandbox_credentials"]


@pytest.mark.parametrize(
    ("member", "wire"),
    [
        (EngineCapability.EGRESS_PENDING, "egress_pending"),
        (InterruptReason.EGRESS_LOGIN, "egress_login"),
    ],
)
def test_inf1173_enum_wire_values(member, wire):
    assert member.value == wire
