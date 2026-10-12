"""Credential model typegen (ok/credential-model): auth schemes, slug-keyed
credentials on manifests, and MCP server credential requirements."""

from typing import List, get_args, get_origin, get_type_hints

from inferencesh.types import (
    AppFunction,
    AppVersionDTO,
    AppVersionInput,
    AuthSchemeAPIKeyIn,
    AuthSchemeFlow,
    AuthSchemeHTTPScheme,
    AuthSchemeKind,
    AuthSchemeOAuth2AuthorizationCode,
    AuthSchemeRefresh,
    AuthSchemeRevokeStyle,
    AuthSchemeSpec,
    CheckRequirementsRequest,
    CredentialConfigDTO,
    CredentialRequirement,
    MCPServerDTO,
    ProviderSeed,
    ProviderSummary,
)


def test_auth_scheme_kind_and_flow_wire_values():
    assert {k.value for k in AuthSchemeKind} == {"oauth2", "api_key", "http"}
    assert AuthSchemeFlow.AUTHORIZATION_CODE.value == "authorization_code"
    assert AuthSchemeFlow.CLIENT_CREDENTIALS.value == "client_credentials"
    assert AuthSchemeAPIKeyIn.HEADER.value == "header"
    assert AuthSchemeHTTPScheme.AUTH_SCHEME_HTTP_BEARER.value == "bearer"
    # Empty string is the wire value for "refresh when expiring".
    assert AuthSchemeRefresh.WHEN_EXPIRING.value == ""
    assert AuthSchemeRefresh.ALWAYS.value == "always"
    assert AuthSchemeRevokeStyle.AUTH_SCHEME_REVOKE_BEARER.value == "bearer"


def test_oauth2_authorization_code_alias_points_at_oauth2_kind():
    assert AuthSchemeOAuth2AuthorizationCode is AuthSchemeKind.AUTH_SCHEME_O_AUTH2
    assert AuthSchemeOAuth2AuthorizationCode.value == "oauth2"


def test_credential_requirement_manifest_shape():
    hints = get_type_hints(CredentialRequirement)
    assert hints["slug"] is str
    assert hints["capabilities"] == List[str]
    assert hints["provider"] == ProviderSeed | None
    assert hints["auth"] == AuthSchemeSpec | None


def test_provider_seed_and_summary_catalog_fields():
    seed = get_type_hints(ProviderSeed)
    assert seed["logo_uri"] is str
    assert seed["docs_uri"] is str
    assert seed["policy_uri"] is str

    summary = get_type_hints(ProviderSummary)
    assert summary["icon_url"] is str
    assert summary["docs_url"] is str


def test_auth_scheme_spec_exposes_api_key_in_as_in_underscore():
    hints = get_type_hints(AuthSchemeSpec)
    assert "in_" in hints
    assert hints["in_"] is AuthSchemeAPIKeyIn
    assert hints["kind"] is AuthSchemeKind
    assert hints["flow"] is AuthSchemeFlow


def test_credential_config_dto_merges_provider_catalog_and_login_state():
    hints = get_type_hints(CredentialConfigDTO)
    assert hints["provider"] is str
    assert hints["provider_info"] == ProviderSummary | None
    assert hints["auth_scheme_id"] is str
    assert hints["connection_scope"].__name__ == "CredentialScope"


def _credential_requirements_list(hint):
    assert get_origin(hint) is list
    assert get_args(hint)[0] is CredentialRequirement


def test_app_version_and_function_carry_slug_keyed_credentials():
    version_hints = get_type_hints(AppVersionDTO)
    _credential_requirements_list(version_hints["required_credentials"])

    input_hints = get_type_hints(AppVersionInput)
    _credential_requirements_list(input_hints["required_credentials"])

    fn_hints = get_type_hints(AppFunction)
    _credential_requirements_list(fn_hints["credentials"])


def test_mcp_server_dto_declares_required_credentials():
    hints = get_type_hints(MCPServerDTO)
    _credential_requirements_list(hints["credentials"])
    assert hints["credential_slug"] is str
    assert hints["connection_scope"].__name__ == "CredentialScope"


def test_check_requirements_accepts_credential_list():
    hints = get_type_hints(CheckRequirementsRequest)
    _credential_requirements_list(hints["credentials"])
