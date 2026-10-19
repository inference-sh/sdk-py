"""Auth provider + company naming (INF-1079 / f9d5620 typegen).

Credential vault UIs group auth methods under a company row. ``CompanySummary``
is that row's identity and outbound links; ``CredentialConfigDTO.company`` carries
it (``provider_info``, its old name, is gone).
``AuthMethod*`` types replace ``AuthScheme*`` with unchanged JSON wire values.
"""

import json
from typing import get_type_hints

import pytest

from inferencesh import types
from inferencesh.types import (
    AuthMethod,
    AuthMethodKind,
    AuthMethodOAuth2AuthorizationCode,
    CompanySeed,
    CompanySummary,
    CredentialConfigDTO,
    CredentialRequirement,
)


def test_company_summary_exposes_link_fields():
    hints = get_type_hints(CompanySummary)
    assert set(hints) >= {
        "slug",
        "name",
        "icon_url",
        "website",
        "docs_url",
        "terms_url",
        "privacy_url",
    }
    assert all(hint is str for hint in hints.values())


def test_company_summary_accepts_legal_urls():
    row: CompanySummary = {
        "slug": "acme",
        "name": "Acme",
        "website": "https://acme.example",
        "docs_url": "https://docs.acme.example",
        "terms_url": "https://acme.example/terms",
        "privacy_url": "https://acme.example/privacy",
    }
    assert row["terms_url"].endswith("/terms")
    assert row["privacy_url"].endswith("/privacy")


def test_credential_config_names_company_and_auth_provider_id():
    """INF-1079 retired provider_info and auth_scheme_id."""
    links: CompanySummary = {
        "slug": "acme",
        "name": "Acme",
        "terms_url": "https://acme.example/terms",
    }
    cfg: CredentialConfigDTO = {
        "slug": "acme-oauth",
        "provider": "acme-oauth",
        "company": links,
        "auth_provider_id": "ap1",
    }
    hints = get_type_hints(CredentialConfigDTO)
    assert "provider_info" not in hints
    assert "auth_scheme_id" not in hints
    assert hints["auth_provider_id"] is str
    assert cfg["company"]["terms_url"].endswith("/terms")


@pytest.mark.parametrize("removed_field", ["auth_scheme_id", "provider_info"])
def test_credential_config_dto_dropped_legacy_inf1079_fields(removed_field):
    hints = get_type_hints(CredentialConfigDTO)
    assert removed_field not in hints


def test_credential_config_parses_auth_provider_id_from_api_json():
    """Vault list rows use auth_provider_id on the wire (not auth_scheme_id)."""
    payload = json.loads(
        """
        {
          "slug": "acme-oauth",
          "provider": "acme-oauth",
          "auth_provider_id": "ap-7f3c",
          "company": {"slug": "acme", "name": "Acme Corp"}
        }
        """
    )
    cfg: CredentialConfigDTO = payload
    assert cfg["auth_provider_id"] == "ap-7f3c"
    assert "auth_scheme_id" not in cfg
    assert "provider_info" not in cfg
    assert cfg["company"]["name"] == "Acme Corp"


def test_credential_config_team_auth_provider_with_multi_account():
    """Team-defined providers expose auth_provider_id alongside account lists."""
    primary = {
        "provider": "acme-oauth",
        "account_id": "acct-work",
        "account_identifier": "work@acme.example",
        "is_primary": True,
    }
    secondary = {
        "provider": "acme-oauth",
        "account_id": "acct-personal",
        "account_identifier": "me@acme.example",
        "is_primary": False,
    }
    cfg: CredentialConfigDTO = {
        "slug": "acme-oauth",
        "provider": "acme-oauth",
        "auth_provider_id": "ap-team-1",
        "multi_account": True,
        "credential": primary,
        "accounts": [primary, secondary],
        "company": {"slug": "acme", "name": "Acme"},
    }
    assert cfg["auth_provider_id"] == "ap-team-1"
    assert [a["account_id"] for a in cfg["accounts"]] == ["acct-work", "acct-personal"]


def test_credential_requirement_seeds_company_and_auth_method():
    hints = get_type_hints(CredentialRequirement)
    assert hints["provider"] == CompanySeed | None
    assert hints["auth"] == AuthMethod | None

    req: CredentialRequirement = {
        "slug": "acme",
        "provider": {"name": "Acme", "website": "https://acme.example"},
        "auth": {"kind": AuthMethodKind.AUTH_METHOD_API_KEY},
    }
    assert req["provider"]["name"] == "Acme"
    assert req["auth"]["kind"] is AuthMethodKind.AUTH_METHOD_API_KEY


def test_auth_method_kind_wire_values_unchanged_after_rename():
    """JSON payloads still use oauth2 / api_key / http; only Python names moved."""
    assert AuthMethodKind.AUTH_METHOD_O_AUTH2.value == "oauth2"
    assert AuthMethodKind.AUTH_METHOD_API_KEY.value == "api_key"
    assert AuthMethodKind.AUTH_METHOD_HTTP.value == "http"


def test_auth_method_oauth2_authorization_code_alias():
    assert AuthMethodOAuth2AuthorizationCode is AuthMethodKind.AUTH_METHOD_O_AUTH2


@pytest.mark.parametrize(
    "legacy_name",
    [
        "ProviderSummary",
        "ProviderSeed",
        "AuthSchemeSpec",
        "AuthSchemeKind",
    ],
)
def test_legacy_auth_scheme_and_provider_type_names_removed(legacy_name):
    assert not hasattr(types, legacy_name), (
        f"inferencesh.types.{legacy_name} was removed in INF-1079; "
        "use CompanySummary / CompanySeed / AuthMethod instead"
    )
