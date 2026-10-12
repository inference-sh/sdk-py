"""MCP tool config and server DTO contracts (INF-1063 / 5dc4400 typegen).

MCP agent tools are keyed by server slug plus tool name; ``credential_id`` is
optional and pins which connection signs the call. MCP is no longer a vault
``CredentialProvider`` / ``CredentialType`` — servers declare OAuth via their
provider. ``MCPServerDTO`` no longer exposes ``oauth_client_id`` on the wire.
"""

from typing import Optional, get_type_hints

from inferencesh.types import (
    AgentTool,
    AgentToolDTO,
    CredentialProvider,
    CredentialScope,
    CredentialType,
    MCPServerDTO,
    MCPToolConfig,
    MCPToolConfigDTO,
    ToolType,
)


def test_mcp_tool_config_requires_server_and_tool_name_fields():
    hints = get_type_hints(MCPToolConfig)
    assert set(hints) == {"server", "tool_name", "credential_id"}
    assert all(hint is str for hint in hints.values())


def test_mcp_tool_config_dto_mirrors_agent_tool_config():
    assert get_type_hints(MCPToolConfigDTO) == get_type_hints(MCPToolConfig)


def test_mcp_tool_config_partial_rows_allow_missing_credential_id():
    """Runner default connection is used when credential_id is omitted."""
    minimal: MCPToolConfig = {"server": "github-mcp", "tool_name": "search_repos"}
    pinned: MCPToolConfig = {
        "server": "github-mcp",
        "tool_name": "search_repos",
        "credential_id": "cred-abc",
    }
    assert minimal["server"] == "github-mcp"
    assert "credential_id" not in minimal
    assert pinned["credential_id"] == "cred-abc"


def test_agent_tool_wires_mcp_through_mcp_tool_config():
    tool_hints = get_type_hints(AgentTool)
    dto_hints = get_type_hints(AgentToolDTO)
    assert tool_hints["mcp"] == Optional[MCPToolConfig]
    assert dto_hints["mcp"] == Optional[MCPToolConfigDTO]

    tool: AgentTool = {
        "name": "gh_search",
        "type": ToolType.MCP,
        "mcp": {"server": "github-mcp", "tool_name": "search_repos"},
    }
    assert tool["type"] == ToolType.MCP
    assert tool["mcp"]["tool_name"] == "search_repos"


def test_mcp_server_dto_drops_oauth_client_id():
    hints = get_type_hints(MCPServerDTO)
    assert "oauth_client_id" not in hints
    assert hints["connection_scope"] is CredentialScope
    assert hints["slug"] is str
    assert hints["server_url"] is str


def test_credential_enums_no_longer_include_mcp_provider_or_type():
    provider_values = {p.value for p in CredentialProvider}
    type_values = {t.value for t in CredentialType}
    assert "mcp" not in provider_values
    assert "mcp" not in type_values
    assert CredentialProvider.GIT_HUB.value == "github"
    assert CredentialType.O_AUTH.value == "oauth"
