"""MCPServerDTO.connection and ConnectionInfo (207c991 / 556f8a2 typegen).

The MCP server catalog returns a nested ``connection`` object that merges
login status/scope with catalogue facts (tool count, last call, last error).
Flat ``connection_status`` / ``connection_scope`` on ``MCPServerDTO`` are
deprecated but must remain for clients that have not migrated to
``connection.status`` / ``connection.scope``.
"""

from typing import Optional, get_type_hints

from inferencesh.types import (
    ConnectionInfo,
    CredentialScope,
    MCPConnectionFacts,
    MCPServerDTO,
)


def test_mcp_server_dto_exposes_nested_connection_and_legacy_flat_fields():
    hints = get_type_hints(MCPServerDTO)
    assert hints["connection"] == Optional[ConnectionInfo]
    # Deprecated flat columns; kept in sync with connection.status / connection.scope.
    assert hints["connection_status"] is str
    assert hints["connection_scope"] is CredentialScope


def test_mcp_connection_facts_record_catalogue_and_call_metadata():
    hints = get_type_hints(MCPConnectionFacts)
    assert set(hints) == {
        "connection_id",
        "tool_count",
        "tools_listed_at",
        "last_called_at",
        "last_error",
    }
    assert hints["tools_listed_at"] == Optional[str]
    assert hints["last_called_at"] == Optional[str]


def test_connection_info_extends_facts_with_login_status_and_scope():
    facts = get_type_hints(MCPConnectionFacts)
    info = get_type_hints(ConnectionInfo)
    assert set(facts) <= set(info)
    assert info["status"] is str
    assert info["scope"] is CredentialScope


def test_connection_info_structural_example_matches_api_shape():
    connected: ConnectionInfo = {
        "connection_id": "conn-7",
        "status": "connected",
        "scope": CredentialScope.TEAM,
        "tool_count": 12,
        "tools_listed_at": "2026-10-13T08:00:00Z",
        "last_called_at": "2026-10-13T08:05:00Z",
        "last_error": "",
    }
    server: MCPServerDTO = {
        "slug": "github-mcp",
        "connection_status": "connected",
        "connection_scope": CredentialScope.TEAM,
        "connection": connected,
    }
    assert server["connection"]["tool_count"] == 12
    assert server["connection"]["scope"] is CredentialScope.TEAM
    assert server["connection_status"] == server["connection"]["status"]
    assert server["connection_scope"] == server["connection"]["scope"]
