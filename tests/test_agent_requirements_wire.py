"""Agent credential requirements and GET /agents/{id}/requirements (api-v1600).

Agents declare logins on their version config; sandboxes inherit them with an
auto vs ask mode. The requirements endpoint merges every source (agent, app,
MCP, HTTP tool) and returns setup errors. ``SandboxCredential`` is now the same
type as ``CredentialRequirement`` (mode on the requirement itself).
"""

from typing import List, get_type_hints

from inferencesh.types import (
    AgentConfigInput,
    AgentRequirement,
    AgentRequirementsResponse,
    AgentRequirementSource,
    AgentRequirementSourceKind,
    AgentRequirementStatus,
    AgentVersionDTO,
    CredentialRequirement,
    EngineCapability,
    InternalToolsConfig,
    RequirementError,
    SandboxCredential,
    SandboxCredentialMode,
    SystemInfo,
)


def test_credential_requirement_exposes_sandbox_credential_mode():
    hints = get_type_hints(CredentialRequirement)
    assert hints["mode"] == SandboxCredentialMode

    auto: CredentialRequirement = {
        "slug": "anthropic",
        "mode": SandboxCredentialMode.SANDBOX_CREDENTIAL_AUTO,
    }
    ask: CredentialRequirement = {
        "slug": "google",
        "mode": SandboxCredentialMode.SANDBOX_CREDENTIAL_ASK,
    }
    assert auto["mode"].value == "auto"
    assert ask["mode"].value == "ask"


def test_sandbox_credential_mode_wire_values():
    assert SandboxCredentialMode.SANDBOX_CREDENTIAL_AUTO.value == "auto"
    assert SandboxCredentialMode.SANDBOX_CREDENTIAL_ASK.value == "ask"
    assert SandboxCredentialMode.SANDBOX_CREDENTIAL_AUTO == "auto"


def test_sandbox_credential_is_credential_requirement_alias():
    """INF-1173 kept mode on the requirement; the separate SandboxCredential type is gone."""
    assert SandboxCredential is CredentialRequirement


def test_agent_version_config_carries_credentials_list():
    hints = get_type_hints(AgentConfigInput)
    assert hints["credentials"] == List[CredentialRequirement]

    cfg: AgentConfigInput = {
        "name": "remote-runner",
        "credentials": [
            {"slug": "github", "mode": SandboxCredentialMode.SANDBOX_CREDENTIAL_ASK},
        ],
    }
    assert cfg["credentials"][0]["mode"] is SandboxCredentialMode.SANDBOX_CREDENTIAL_ASK


def test_agent_version_dto_publishes_credentials():
    hints = get_type_hints(AgentVersionDTO)
    assert hints["credentials"] == List[CredentialRequirement]

    published: AgentVersionDTO = {
        "id": "ver_01",
        "credentials": [{"slug": "slack", "optional": True}],
    }
    assert published["credentials"][0]["slug"] == "slack"


def test_internal_tools_still_reads_legacy_sandbox_credentials():
    hints = get_type_hints(InternalToolsConfig)
    assert hints["sandbox_credentials"] == List[SandboxCredential]

    legacy: InternalToolsConfig = {
        "remote": True,
        "sandbox_credentials": [{"slug": "github", "mode": SandboxCredentialMode.SANDBOX_CREDENTIAL_AUTO}],
    }
    assert legacy["sandbox_credentials"][0]["slug"] == "github"


def test_agent_requirement_source_kind_wire_values():
    assert AgentRequirementSourceKind.AGENT_REQUIREMENT_FROM_AGENT.value == "agent"
    assert AgentRequirementSourceKind.AGENT_REQUIREMENT_FROM_APP.value == "app"
    assert AgentRequirementSourceKind.AGENT_REQUIREMENT_FROM_MCP.value == "mcp"
    assert AgentRequirementSourceKind.AGENT_REQUIREMENT_FROM_HTTP.value == "http"


def test_agent_requirement_status_wire_values():
    assert AgentRequirementStatus.AGENT_REQUIREMENT_CONNECTED.value == "connected"
    assert AgentRequirementStatus.AGENT_REQUIREMENT_MISSING.value == "missing"
    assert AgentRequirementStatus.AGENT_REQUIREMENT_MISSING_SCOPES.value == "missing_scopes"
    assert AgentRequirementStatus.AGENT_REQUIREMENT_UNKNOWN.value == "unknown"
    assert AgentRequirementStatus.AGENT_REQUIREMENT_NOT_GIVEN.value == "not_given"


def test_agent_requirements_response_merges_sources_and_errors():
    hints = get_type_hints(AgentRequirementsResponse)
    assert hints["requirements"] == List[AgentRequirement]
    assert hints["satisfied"] is bool

    source: AgentRequirementSource = {
        "kind": AgentRequirementSourceKind.AGENT_REQUIREMENT_FROM_APP,
        "name": "acme/search",
        "tool": "search",
    }
    err: RequirementError = {
        "type": "credential",
        "key": "google",
        "message": "Connect Google",
    }
    requirement: AgentRequirement = {
        "requirement": {"slug": "google", "scopes": ["calendar.read"]},
        "from": [source],
        "status": AgentRequirementStatus.AGENT_REQUIREMENT_MISSING,
        "errors": [err],
    }
    response: AgentRequirementsResponse = {
        "agent_id": "agt_01",
        "version_id": "ver_01",
        "satisfied": False,
        "requirements": [requirement],
    }
    assert response["requirements"][0]["from"][0]["tool"] == "search"
    assert response["requirements"][0]["errors"][0]["key"] == "google"


def test_egress_engine_capabilities_from_same_regen():
    """gRPC, dotted host suffixes, and body-bound secrets need matching engines."""
    assert EngineCapability.EGRESS_FORMS.value == "egress_forms"
    assert EngineCapability.EGRESS_H2.value == "egress_h2"
    assert EngineCapability.EGRESS_HOST_SUFFIX.value == "egress_host_suffix"


def test_system_info_reports_remote_sandbox_mechanism():
    info: SystemInfo = {
        "sandbox": {
            "mechanism": "landlock",
            "version": "abi 6",
            "available": True,
            "required": False,
        },
    }
    assert info["sandbox"]["mechanism"] == "landlock"
    assert info["sandbox"]["available"] is True