"""Auth provider + company naming (INF-1079 / f9d5620 typegen).

Credential vault UIs group auth methods under a company row. ``CompanySummary``
is that row's identity and outbound links; ``CredentialConfigDTO.company`` is the
settled name for the same payload as ``provider_info`` during the rename window.
``AuthMethod*`` types replace ``AuthScheme*`` with unchanged JSON wire values.
"""

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


def test_credential_config_company_and_provider_info_share_shape():
    """During the rename, API may send either key; both must type-check."""
    links: CompanySummary = {
        "slug": "acme",
        "name": "Acme",
        "terms_url": "https://acme.example/terms",
        "privacy_url": "https://acme.example/privacy",
    }
    via_legacy: CredentialConfigDTO = {
        "slug": "acme-oauth",
        "provider": "acme-oauth",
        "provider_info": links,
    }
    via_company: CredentialConfigDTO = {
        "slug": "acme-oauth",
        "provider": "acme-oauth",
        "company": links,
    }
    hints = get_type_hints(CredentialConfigDTO)
    assert hints["provider_info"] == hints["company"]
    assert via_legacy["provider_info"]["terms_url"] == via_company["company"]["terms_url"]


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
