"""Sandbox vault access and box API scopes wire (c8aed89 / INF-1062).

Vaults grant inference.sh API access to sandboxes: agents pin a vault on
``AgentConfigInput`` / ``AgentVersionDTO``; ``CreateSandboxRequest`` can set
``vault_id`` explicitly; created boxes expose the copied scopes on
``SandboxDTO.api_scopes``. ``ScopeDefinition.sandbox`` marks which scopes a
vault may grant to a box (for scope catalog UIs).
"""

import json
from typing import List, Optional, get_type_hints

from inferencesh.types import (
    AgentConfigInput,
    AgentVersionDTO,
    CreateSandboxRequest,
    SandboxDTO,
    Scope,
    ScopeDefinition,
)


def test_scope_definition_sandbox_flag_contract():
    hints = get_type_hints(ScopeDefinition)
    assert "sandbox" in hints
    assert hints["sandbox"] is bool

    apps_execute: ScopeDefinition = {
        "value": Scope.APPS_EXECUTE,
        "label": "Run apps",
        "description": "Execute store apps",
        "group": None,
        "sandbox": True,
        "costs_credits": True,
    }
    assert apps_execute["sandbox"] is True
    assert apps_execute["value"] is Scope.APPS_EXECUTE


def test_agent_config_and_version_vault_id_contracts():
    config_hints = get_type_hints(AgentConfigInput)
    version_hints = get_type_hints(AgentVersionDTO)
    assert config_hints["vault_id"] == Optional[str]
    assert version_hints["vault_id"] == Optional[str]

    config: AgentConfigInput = {
        "name": "sandbox-spawner",
        "vault_id": "vault_team_ops",
    }
    version: AgentVersionDTO = {
        "id": "aver_1",
        "vault_id": "vault_team_ops",
    }
    assert config["vault_id"] == version["vault_id"]


def test_create_sandbox_request_vault_id_contract_and_round_trip():
    hints = get_type_hints(CreateSandboxRequest)
    assert hints["vault_id"] == Optional[str]

    req: CreateSandboxRequest = {
        "name": "build-box",
        "vault_id": "vault_ci",
        "vcpus": 2,
        "memory_mib": 4096,
    }
    wire = json.loads(json.dumps(req))
    assert wire["vault_id"] == "vault_ci"
    assert wire["name"] == "build-box"


def test_sandbox_dto_api_scopes_contract():
    hints = get_type_hints(SandboxDTO)
    assert hints["api_scopes"] == List[Scope]

    box: SandboxDTO = {
        "id": "sbx_1",
        "vault_id": "vault_ci",
        "api_scopes": [
            Scope.APPS_EXECUTE,
            Scope.FILES_READ,
        ],
    }
    assert box["api_scopes"][0] is Scope.APPS_EXECUTE
    assert box["api_scopes"][1].value == "files:read"

    empty: SandboxDTO = {"id": "sbx_2", "api_scopes": []}
    assert empty["api_scopes"] == []


def test_sandbox_api_scopes_json_round_trip_uses_scope_wire_values():
    payload = {
        "id": "sbx_metered",
        "api_scopes": ["apps:execute", "apps:read"],
    }
    wire = json.loads(json.dumps(payload))
    scopes = [Scope(v) for v in wire["api_scopes"]]
    assert scopes == [Scope.APPS_EXECUTE, Scope.APPS_READ]


def test_vault_id_optional_on_create_without_scopes():
    """Empty vault: box runs its remote only; api_scopes absent or empty."""
    req: CreateSandboxRequest = {"name": "remote-only"}
    box: SandboxDTO = {"id": "sbx_remote", "api_scopes": []}
    assert "vault_id" not in req
    assert box.get("vault_id") is None
    assert box["api_scopes"] == []
