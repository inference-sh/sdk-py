"""Usage policy rules share PolicyRuleDTO with execution policy (40c7f73 typegen).

Usage kinds use specifier for a resource id or ``publisher:<team id>``, and
label for the human-facing name or glob the rule was written with.
"""

from typing import get_type_hints

from inferencesh.types import PolicyEffect, PolicyKind, PolicyRuleDTO

USAGE_POLICY_KINDS = (
    PolicyKind.APP,
    PolicyKind.AGENT,
    PolicyKind.KNOWLEDGE,
    PolicyKind.MCP,
    PolicyKind.FLOW,
)


def test_usage_policy_kinds_are_distinct_policy_kind_members():
    values = {kind.value for kind in USAGE_POLICY_KINDS}
    assert values == {"App", "Agent", "Knowledge", "Mcp", "Flow"}


def test_policy_rule_dto_accepts_usage_resource_and_publisher_specifiers():
    hints = get_type_hints(PolicyRuleDTO)
    assert hints["specifier"] is str
    assert hints["label"] is str

    by_id: PolicyRuleDTO = {
        "effect": PolicyEffect.ASK,
        "kind": PolicyKind.APP,
        "selector": "",
        "specifier": "app_01h2example",
        "label": "bytedance/seedance",
    }
    by_publisher: PolicyRuleDTO = {
        "effect": PolicyEffect.ALLOW,
        "kind": PolicyKind.FLOW,
        "selector": "",
        "specifier": "publisher:team_01h2example",
        "label": "bytedance/*",
    }
    assert by_id["specifier"] == "app_01h2example"
    assert by_publisher["specifier"].startswith("publisher:")
    assert by_id["label"].count("/") == 1
    assert by_id["label"].endswith("seedance")
    assert by_publisher["label"].endswith("/*")
