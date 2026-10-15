"""MCPServerDTO.connection and ConnectionInfo (207c991 / 556f8a2 typegen).

Store and agent UIs list MCP servers with the caller's login status on each row.
``connection`` replaces the deprecated ``connection_status`` / ``connection_scope``
pair with a single nested object that also carries connection facts (tool catalogue,
last call). Tool configs reference servers by slug with an optional credential pin.
"""

from typing import Optional, get_type_hints

from inferencesh.types import (
    ConnectionInfo,
    CredentialScope,
    MCPServerDTO,
    MCPToolConfig,
    MCPConnectionFacts,
)


def test_mcp_server_dto_exposes_connection_and_deprecated_status_fields():
    hints = get_type_hints(MCPServerDTO)
    assert hints["connection"] == Optional[ConnectionInfo]
    assert hints["connection_status"] is str
    assert hints["connection_scope"] is CredentialScope


def test_connection_info_merges_login_status_with_connection_facts():
    facts_hints = get_type_hints(MCPConnectionFacts)
    conn_hints = get_type_hints(ConnectionInfo)
    assert set(facts_hints) <= set(conn_hints)
    assert conn_hints["status"] is str
    assert conn_hints["scope"] is CredentialScope

    row: ConnectionInfo = {
        "status": "connected",
        "scope": CredentialScope.TEAM,
        "connection_id": "conn-7",
        "tool_count": 12,
        "tools_listed_at": "2026-10-15T12:00:00Z",
        "last_called_at": "2026-10-15T12:05:00Z",
        "last_error": "",
    }
    assert row["scope"] is CredentialScope.TEAM
    assert row["tool_count"] == 12


def test_mcp_tool_config_server_slug_and_optional_credential_id():
    hints = get_type_hints(MCPToolConfig)
    assert hints["server"] is str
    assert hints["tool_name"] is str
    assert hints["credential_id"] is str

    pinned: MCPToolConfig = {
        "server": "github-mcp",
        "tool_name": "search_repos",
        "credential_id": "cred-42",
    }
    default_login: MCPToolConfig = {
        "server": "exa",
        "tool_name": "search",
    }
    assert pinned["credential_id"] == "cred-42"
    assert "credential_id" not in default_login
