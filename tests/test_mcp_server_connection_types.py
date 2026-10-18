"""MCPServerDTO.connection and ConnectionInfo (207c991 / 556f8a2 typegen).

Store and agent UIs list MCP servers with the caller's login status on each row.
``connection`` replaces the deprecated ``connection_status`` / ``connection_scope``
pair with a single nested object that also carries connection facts (tool catalogue,
last call). Tool configs reference servers by slug; calls sign in with the runner's own login.
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


def test_mcp_tool_config_is_server_slug_and_tool_name_only():
    """INF-1012: no credential pin; the runner's own login is used at run time."""
    hints = get_type_hints(MCPToolConfig)
    assert hints == {"server": str, "tool_name": str}

    cfg: MCPToolConfig = {"server": "exa", "tool_name": "search"}
    assert cfg == {"server": "exa", "tool_name": "search"}
