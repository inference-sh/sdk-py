"""Bounty program shape and MCP App page-hash routing (7df44f5 typegen).

Guards the API contract when proof length moves server-side (proof_min_length
removed from BountyProgramDTO) and when MCP App pages are referenced by hash
instead of duplicated inline HTML in every chat message.
"""

from typing import get_type_hints

from inferencesh.types import (
    A2UIComponent,
    A2UIComponentType,
    BountyProgramDTO,
    BountySubmissionDTO,
    ErrorCode,
    PaymentMethodRequiredMeta,
    SubmitBountyRequest,
    SubmitBountyResponse,
)


def test_bounty_program_no_longer_exposes_proof_min_length():
    hints = get_type_hints(BountyProgramDTO)
    assert "proof_min_length" not in hints
    assert hints["proof_type"] is str
    assert hints["requires_payment_method"] is bool


def test_bounty_claim_request_and_response_shapes():
    program: BountyProgramDTO = {
        "name": "marketplace-launch",
        "proof_type": "url",
        "requires_payment_method": True,
        "amount_microcents": 5_000_000,
        "max_per_user": 1,
        "max_per_day": 10,
    }
    assert program["proof_type"] == "url"
    assert program["requires_payment_method"] is True

    req_hints = get_type_hints(SubmitBountyRequest)
    assert req_hints["bounty_id"] is str
    assert req_hints["proof_id"] is str

    claim: SubmitBountyRequest = {
        "bounty_id": "bounty_1",
        "proof_id": "https://example.com/post/123",
        "agent": "acme/assistant@latest",
        "source": "web",
    }
    response: SubmitBountyResponse = {
        "submission": {
            "bounty_id": claim["bounty_id"],
            "proof_id": claim["proof_id"],
            "proof_ref": "proof_ref_1",
            "agent": claim["agent"],
            "source": claim["source"],
        },
        "granted_amount": program["amount_microcents"],
    }
    submission_hints = get_type_hints(BountySubmissionDTO)
    assert submission_hints["proof_ref"] is str
    assert response["submission"]["proof_id"] == claim["proof_id"]
    assert response["granted_amount"] == 5_000_000


def test_payment_method_required_error_links_bounty_to_billing():
    assert ErrorCode.PAYMENT_METHOD_REQUIRED.value == "payment_method_required"

    meta_hints = get_type_hints(PaymentMethodRequiredMeta)
    assert meta_hints["bounty_id"] is str
    assert meta_hints["billing_page"] is str

    meta: PaymentMethodRequiredMeta = {
        "bounty_id": "bounty_1",
        "billing_page": "/settings/billing",
    }
    assert meta["billing_page"].startswith("/")


def test_a2ui_mcp_app_supports_page_hash_and_inline_html():
    hints = get_type_hints(A2UIComponent)
    assert hints["mcpPageHash"] is str
    assert hints["mcpHtml"] is str

    by_hash: A2UIComponent = {
        "component": A2UIComponentType.A2UI_MCP_APP,
        "mcpPageHash": "sha256:abc123",
        "mcpServerSlug": "analytics",
        "mcpCredentialId": "cred_1",
        "mcpToolName": "show_dashboard",
    }
    inline: A2UIComponent = {
        "component": A2UIComponentType.A2UI_MCP_APP,
        "mcpHtml": "<html><body>legacy</body></html>",
        "mcpServerSlug": "analytics",
        "mcpCredentialId": "cred_1",
        "mcpToolName": "show_dashboard",
    }
    assert by_hash["mcpPageHash"].startswith("sha256:")
    assert "legacy" in inline["mcpHtml"]
    assert by_hash.get("mcpHtml") is None
    assert inline.get("mcpPageHash") is None
