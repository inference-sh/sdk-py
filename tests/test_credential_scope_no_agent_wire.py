"""CredentialScope wire contract after removing agent scope (86ae28b).

The API no longer exposes ``agent`` as a credential connection scope; agent
credentials are composed via vaults (INF-737). SDK clients still parse
CredentialDTO.scope, connect payloads, and MCP ConnectionInfo.scope — these
tests lock the four remaining wire values and guard against reintroducing
``agent`` as a CredentialScope member.
"""

import json
from typing import get_type_hints

import pytest

from inferencesh.types import (
    ConnectionInfo,
    CredentialConnectRequest,
    CredentialDTO,
    CredentialScope,
    CredentialStatus,
    CredentialType,
)


def test_credential_scope_members_use_documented_wire_strings_without_agent():
    assert CredentialScope.PLATFORM.value == "platform"
    assert CredentialScope.ORG.value == "org"
    assert CredentialScope.TEAM.value == "team"
    assert CredentialScope.USER.value == "user"
    assert len(CredentialScope) == 4
    assert "agent" not in {member.value for member in CredentialScope}
    with pytest.raises(AttributeError):
        _ = CredentialScope.AGENT  # type: ignore[attr-defined]


def test_credential_dto_declares_scope():
    hints = get_type_hints(CredentialDTO)
    assert hints["scope"] is CredentialScope


def test_credential_connect_request_declares_connection_scope():
    hints = get_type_hints(CredentialConnectRequest)
    assert hints["connection_scope"] is CredentialScope


def test_connection_info_declares_scope():
    hints = get_type_hints(ConnectionInfo)
    assert hints["scope"] is CredentialScope


def test_credential_scope_round_trips_on_wire():
    for scope in CredentialScope:
        row: ConnectionInfo = {
            "status": "connected",
            "scope": scope,
        }
        wire = json.loads(json.dumps(row))
        assert wire["scope"] == scope.value
        parsed: ConnectionInfo = wire  # type: ignore[assignment]
        assert parsed["scope"] == scope.value


def test_credential_dto_scope_round_trips_on_wire():
    cred: CredentialDTO = {
        "id": "cred_team_slack",
        "provider": "slack",
        "type": CredentialType.O_AUTH,
        "scope": CredentialScope.TEAM,
        "status": CredentialStatus.CONNECTED,
        "display_name": "Team Slack",
    }
    wire = json.loads(json.dumps(cred))
    assert wire["scope"] == "team"
