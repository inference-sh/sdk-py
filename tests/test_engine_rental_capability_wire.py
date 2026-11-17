"""Engine rental capability and billing wire (api-v1577 / v1572 on dev).

Rent and extend routes return ``team_role_required`` when the caller lacks
``rent_engines``, and successful instance payloads still carry rental billing
fields after ``launch_configuration`` / ``envs`` were removed from InstanceDTO.
"""

from typing import List, get_type_hints

from inferencesh.types import (
    ErrorCode,
    InstanceDTO,
    InstanceRentalType,
    TeamCapability,
    TeamRoleRequiredMeta,
    TeamViewDTO,
)


def test_team_role_required_error_code_wire():
    assert ErrorCode.TEAM_ROLE_REQUIRED.value == "team_role_required"
    assert "TEAM_ROLE_REQUIRED" in ErrorCode.__members__


def test_rent_engines_meta_may_carry_capability_alone():
    """TeamRoleRequiredMeta documents RequiredRole as optional on the wire."""
    hints = get_type_hints(TeamRoleRequiredMeta)
    assert hints["capability"] == TeamCapability

    meta: TeamRoleRequiredMeta = {"capability": TeamCapability.RENT_ENGINES}
    assert meta["capability"] is TeamCapability.RENT_ENGINES
    assert "required_role" not in meta


def test_instance_dto_still_exposes_rental_billing_fields():
    hints = get_type_hints(InstanceDTO)
    assert hints["rental_type"] == InstanceRentalType
    assert hints["hourly_price"] == int
    assert "launch_configuration" not in hints
    assert "envs" not in hints

    row: InstanceDTO = {
        "name": "gpu-1",
        "rental_type": InstanceRentalType.ON_DEMAND,
        "hourly_price": 420,
        "configuration": {"gpu": "a10"},
    }
    assert row["rental_type"] is InstanceRentalType.ON_DEMAND
    assert row["hourly_price"] == 420


def test_team_view_needs_admin_access_lists_capabilities():
    hints = get_type_hints(TeamViewDTO)
    assert hints["needs_admin_access"] == List[TeamCapability]