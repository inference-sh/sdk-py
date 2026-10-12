"""AuthSchemeSpec OAuth metadata (models v0.8.97 typegen).

Covers RFC 8707 resource indicators, RFC 9207 issuer validation flags,
shared MCP callback/profile wiring, and public-client token auth (none).
"""

from typing import get_type_hints

from inferencesh.types import AuthSchemeClientAuth, AuthSchemeSpec


def test_auth_scheme_client_auth_includes_public_client_none():
    assert AuthSchemeClientAuth.NONE.value == "none"
    assert {m.value for m in AuthSchemeClientAuth} == {"basic", "body", "none"}


def test_auth_scheme_spec_exposes_oauth_metadata_fields():
    hints = get_type_hints(AuthSchemeSpec)
    assert hints["resource"] is str
    assert hints["issuer"] is str
    assert hints["authorization_response_iss_parameter_supported"] is bool
    assert hints["callback"] is str
    assert hints["profile"] is str
    assert hints["client_auth"] is AuthSchemeClientAuth


def test_partial_mcp_public_client_scheme_is_a_valid_typed_dict():
    scheme: AuthSchemeSpec = {
        "resource": "https://mcp.example.com",
        "issuer": "https://auth.example.com",
        "authorization_response_iss_parameter_supported": True,
        "callback": "mcp",
        "profile": "mcp-dynamic-client",
        "client_auth": AuthSchemeClientAuth.NONE,
        "pkce": True,
    }
    assert scheme["client_auth"] is AuthSchemeClientAuth.NONE
    assert scheme["callback"] == "mcp"
