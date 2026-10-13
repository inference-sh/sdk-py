"""ProviderSummary legal and docs links (144ac82 typegen).

Credential vault UIs group auth schemes under a company row. ``ProviderSummary``
is that row's identity and outbound links; dropping ``terms_url`` or
``privacy_url`` breaks compliance footers without a runtime error.
"""

from typing import get_type_hints

from inferencesh.types import CredentialConfigDTO, ProviderSummary


def test_provider_summary_exposes_link_fields():
    hints = get_type_hints(ProviderSummary)
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


def test_provider_summary_accepts_legal_urls():
    row: ProviderSummary = {
        "slug": "acme",
        "name": "Acme",
        "website": "https://acme.example",
        "docs_url": "https://docs.acme.example",
        "terms_url": "https://acme.example/terms",
        "privacy_url": "https://acme.example/privacy",
    }
    assert row["terms_url"].endswith("/terms")
    assert row["privacy_url"].endswith("/privacy")


def test_credential_config_provider_info_carries_legal_links():
    """Merged credential catalog rows embed company links for the vault UI."""
    config: CredentialConfigDTO = {
        "slug": "acme-oauth",
        "provider": "acme-oauth",
        "provider_info": {
            "slug": "acme",
            "name": "Acme",
            "terms_url": "https://acme.example/terms",
            "privacy_url": "https://acme.example/privacy",
        },
    }
    info = config["provider_info"]
    assert info is not None
    assert info["terms_url"] == "https://acme.example/terms"
    assert info["privacy_url"] == "https://acme.example/privacy"
