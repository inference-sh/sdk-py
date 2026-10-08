"""Policy rule enforcement and remote selectors (INF-906 / 1b379ad typegen).

``enforcement`` on ``PolicyRuleDTO`` controls whether a rule decides, is
final for admins, runs in evaluate-only mode, or is kept but ignored.
``selector`` can narrow a rule to a remote id or ``tag:<name>``.
"""

from typing import get_type_hints

from inferencesh.types import (
    EnforcementMode,
    PolicyEffect,
    PolicyEnforcement,
    PolicyKind,
    PolicyRuleDTO,
)

POLICY_ENFORCEMENT_WIRE = frozenset(
    {"default", "enforced", "evaluate", "disabled"},
)


def test_policy_enforcement_values_match_api_wire():
    assert {m.value for m in PolicyEnforcement} == POLICY_ENFORCEMENT_WIRE


def test_policy_enforcement_is_not_entitlement_enforcement_mode():
    """Billing entitlements use EnforcementMode; policy rules use PolicyEnforcement."""
    assert PolicyEnforcement is not EnforcementMode
    assert {m.value for m in EnforcementMode}.isdisjoint(POLICY_ENFORCEMENT_WIRE)


def test_policy_rule_dto_accepts_enforcement_and_remote_tag_selector():
    hints = get_type_hints(PolicyRuleDTO)
    assert hints["enforcement"] is PolicyEnforcement
    assert hints["selector"] is str
    assert hints["specifier"] is str

    remote_exec: PolicyRuleDTO = {
        "effect": PolicyEffect.ASK,
        "enforcement": PolicyEnforcement.DEFAULT,
        "kind": PolicyKind.REMOTE_EXEC,
        "selector": "remote_01h2example",
        "specifier": "git push:*",
        "label": "git push on Laptop",
    }
    tagged_workspace: PolicyRuleDTO = {
        "effect": PolicyEffect.DENY,
        "enforcement": PolicyEnforcement.ENFORCED,
        "kind": PolicyKind.WORKSPACE,
        "selector": "tag:prod",
        "specifier": "~/secrets/**",
        "label": "prod remotes secrets folder",
    }
    evaluate_only: PolicyRuleDTO = {
        "effect": PolicyEffect.ALLOW,
        "enforcement": PolicyEnforcement.EVALUATE,
        "kind": PolicyKind.TOOL,
        "selector": "",
        "specifier": "Bash",
        "label": "dry-run allow Bash",
    }
    disabled: PolicyRuleDTO = {
        "effect": PolicyEffect.DENY,
        "enforcement": PolicyEnforcement.DISABLED,
        "kind": PolicyKind.HARNESS,
        "selector": "",
        "specifier": "Edit",
        "label": "retired edit rule",
    }

    assert remote_exec["enforcement"] is PolicyEnforcement.DEFAULT
    assert not remote_exec["selector"].startswith("tag:")
    assert remote_exec["specifier"].endswith(":*")

    assert tagged_workspace["selector"] == "tag:prod"
    assert tagged_workspace["enforcement"] is PolicyEnforcement.ENFORCED
    assert "/**" in tagged_workspace["specifier"]

    assert evaluate_only["enforcement"] is PolicyEnforcement.EVALUATE
    assert disabled["enforcement"] is PolicyEnforcement.DISABLED
