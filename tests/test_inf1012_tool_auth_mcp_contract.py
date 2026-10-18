"""Tool auth and MCP tool wire contracts (INF-1012 / afbadaf).

``credential_id`` pinning was removed from ``HTTPToolBuilder.auth()`` and
``mcp_tool()``. HTTP credential auth is provider-only; MCP tools require
``server`` and ``tool_name`` and sign in with the runner's own login at run time.
"""

import json
from typing import Optional, get_type_hints

from inferencesh.tools import http_tool, mcp_tool
from inferencesh.types import (
    AgentToolDTO,
    HTTPToolConfigDTO,
    MCPToolConfig,
    MCPToolConfigDTO,
    ToolAuthConfig,
    ToolAuthType,
    ToolType,
)


def test_tool_auth_config_excludes_credential_id_pin():
    hints = get_type_hints(ToolAuthConfig)
    assert "credential_id" not in hints
    assert set(hints) >= {"type", "provider", "secret", "header"}

    auth: ToolAuthConfig = {"type": ToolAuthType.CREDENTIAL, "provider": "github"}
    wire = json.loads(json.dumps(auth))
    assert wire == {"type": "credential", "provider": "github"}
    assert "credential_id" not in wire


def test_mcp_tool_config_dto_matches_runtime_config_shape():
    assert get_type_hints(MCPToolConfigDTO) == get_type_hints(MCPToolConfig)
    assert set(get_type_hints(MCPToolConfigDTO)) == {"server", "tool_name"}

    built = mcp_tool("search", server="exa", tool_name="search").build()["mcp"]
    dto: MCPToolConfigDTO = {"server": "exa", "tool_name": "search"}
    assert built == dto
    assert json.loads(json.dumps(built)) == dto


def test_http_tool_config_dto_auth_matches_builder_without_connection_pin():
    hints = get_type_hints(HTTPToolConfigDTO)
    assert hints["auth"] == Optional[ToolAuthConfig]

    built_auth = (
        http_tool("gh", "https://api.github.com/user")
        .auth(credential="github")
        .build()["http"]["auth"]
    )
    dto: HTTPToolConfigDTO = {
        "url": "https://api.github.com/user",
        "auth": {"type": ToolAuthType.CREDENTIAL, "provider": "github"},
    }
    assert dto["auth"] == built_auth
    assert "credential_id" not in dto["auth"]


def test_agent_tool_dto_mcp_field_uses_slim_mcp_config():
    hints = get_type_hints(AgentToolDTO)
    assert hints["mcp"] == Optional[MCPToolConfigDTO]

    row: AgentToolDTO = {
        "name": "web_search",
        "type": ToolType.MCP,
        "mcp": {"server": "exa", "tool_name": "search"},
    }
    assert row["mcp"] == {"server": "exa", "tool_name": "search"}
    assert "credential_id" not in row["mcp"]
