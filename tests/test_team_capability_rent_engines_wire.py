"""TeamCapability rent_engines (api-v1577 / 1addf5e typegen).

Renting and extending cloud engine rentals debits the team balance; the API
gates those routes on the rent_engines capability. Clients read it from
TeamViewDTO.can and from team_role_required error meta.
"""

from typing import List, get_type_hints

from inferencesh.types import (
    TeamCapability,
    TeamRole,
    TeamRoleRequiredMeta,
    TeamViewDTO,
    TeamViewOrg,
)


def test_rent_engines_capability_wire_value():
    assert TeamCapability.RENT_ENGINES.value == "rent_engines"
    assert TeamCapability.RENT_ENGINES == "rent_engines"
    assert "RENT_ENGINES" in TeamCapability.__members__


def test_team_role_required_meta_names_rent_engines_capability():
    hints = get_type_hints(TeamRoleRequiredMeta)
    assert hints["capability"] == TeamCapability

    meta: TeamRoleRequiredMeta = {
        "capability": TeamCapability.RENT_ENGINES,
        "actual_role": TeamRole.MEMBER,
        "required_role": TeamRole.ADMIN,
    }
    assert meta["capability"] == TeamCapability.RENT_ENGINES


def test_team_view_surfaces_rent_engines_in_can_lists():
    hints = get_type_hints(TeamViewDTO)
    assert hints["can"] == List[TeamCapability]

    org: TeamViewOrg = {
        "id": "org_01",
        "name": "Acme Org",
        "slug": "acme",
        "can": [TeamCapability.VIEW_BILLING, TeamCapability.RENT_ENGINES],
    }
    view: TeamViewDTO = {
        "team_id": "team_01",
        "can": [
            TeamCapability.MANAGE_BILLING,
            TeamCapability.RENT_ENGINES,
        ],
        "needs_admin_access": [TeamCapability.RENT_ENGINES],
        "org": org,
    }
    assert TeamCapability.RENT_ENGINES in view["can"]
    assert view["needs_admin_access"] == [TeamCapability.RENT_ENGINES]
    assert TeamCapability.RENT_ENGINES in view["org"]["can"]


def test_rent_engines_sits_with_billing_capabilities_in_enum():
    """Billing gates often precede engine rental in settings UIs."""
    members = list(TeamCapability)
    assert TeamCapability.VIEW_BILLING in members
    assert TeamCapability.MANAGE_BILLING in members
    billing_idx = members.index(TeamCapability.MANAGE_BILLING)
    rent_idx = members.index(TeamCapability.RENT_ENGINES)
    assert rent_idx == billing_idx + 1