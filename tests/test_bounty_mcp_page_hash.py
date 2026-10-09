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
    ErrorCode,
    PaymentMethodRequiredMeta,
)


def test_bounty_program_no_longer_exposes_proof_min_length():
    hints = get_type_hints(BountyProgramDTO)
    assert "proof_min_length" not in hints
    assert hints["proof_type"] is str
    assert hints["requires_payment_method"] is bool


def test_payment_method_required_error_links_bounty_to_billing():
    assert ErrorCode.PAYMENT_METHOD_REQUIRED.value == "payment_method_required"

    meta_hints = get_type_hints(PaymentMethodRequiredMeta)
    assert meta_hints["bounty_id"] is str
    assert meta_hints["billing_page"] is str


def test_a2ui_mcp_app_supports_page_hash_and_inline_html():
    hints = get_type_hints(A2UIComponent)
    assert hints["mcpPageHash"] is str
    assert hints["mcpHtml"] is str
    assert A2UIComponentType.A2UI_MCP_APP.value == "McpApp"
