"""Store scope catalog (v0.8.91): store:pricing / store:submit replace admin:pricing."""

from typing import List, get_type_hints

from inferencesh.types import Scope, ScopeDefinition, ScopeGroup, ScopeGroupDefinition, ScopesResponse


def test_scope_definition_dropped_automation_flag():
    hints = get_type_hints(ScopeDefinition)
    assert "automation" not in hints
    assert hints["costs_credits"] is bool


def test_store_group_and_scopes_on_wire():
    assert ScopeGroup.STORE in ScopeGroup
    assert Scope.STORE_PRICING.value == "store:pricing"
    assert Scope.STORE_SUBMIT.value == "store:submit"


def test_scopes_response_shape_unchanged():
    hints = get_type_hints(ScopesResponse)
    assert hints["scopes"] == List[ScopeDefinition]
    assert hints["groups"] == List[ScopeGroupDefinition]

    group: ScopeGroupDefinition = {
        "id": ScopeGroup.STORE,
        "label": "Store",
        "staff_only": True,
    }
    assert group["id"] is ScopeGroup.STORE
