"""Forms and bounties OAuth/API scopes (f719ece typegen).

New ``Scope`` and ``ScopeGroup`` members gate form management, submissions,
and bounty program listing/claims. Clients parse these on keys, sessions, and
``ScopeRefusedMeta.required_scope`` when an operation is refused.
"""

import json
from typing import get_type_hints

import pytest

from inferencesh.types import Scope, ScopeGroup, ScopeRefusedMeta


def test_scope_resource_level_forms_and_bounties_wire_values():
    assert Scope.FORMS.value == "forms"
    assert Scope.BOUNTIES.value == "bounties"


def test_scope_action_level_forms_and_bounties_wire_values():
    assert Scope.FORMS_READ.value == "forms:read"
    assert Scope.FORMS_WRITE.value == "forms:write"
    assert Scope.FORMS_EXECUTE.value == "forms:execute"
    assert Scope.BOUNTIES_READ.value == "bounties:read"
    assert Scope.BOUNTIES_EXECUTE.value == "bounties:execute"


def test_scope_group_includes_forms_and_bounties():
    assert ScopeGroup.FORMS.value == "forms"
    assert ScopeGroup.BOUNTIES.value == "bounties"


def test_scope_refused_meta_required_scope_is_scope_enum():
    hints = get_type_hints(ScopeRefusedMeta)
    assert hints["required_scope"] is Scope


@pytest.mark.parametrize(
    "scope",
    [
        Scope.FORMS_READ,
        Scope.FORMS_EXECUTE,
        Scope.BOUNTIES_READ,
        Scope.BOUNTIES_EXECUTE,
    ],
)
def test_forms_and_bounties_scopes_round_trip_on_wire(scope: Scope):
    meta: ScopeRefusedMeta = {"required_scope": scope}
    wire = json.loads(json.dumps(meta))
    assert wire["required_scope"] == scope.value
    parsed: ScopeRefusedMeta = wire  # type: ignore[assignment]
    assert parsed["required_scope"] == scope.value
    assert Scope(parsed["required_scope"]) is scope
