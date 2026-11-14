"""Engine capacity policy and sandbox plan entitlement limits (79493f8).

Owners set ``EngineCapacityPolicy`` on ``EngineDTO`` (POST /engines/{id}/capacity);
``EngineCapacityLimit`` caps over-commit and CPU slots. Plan tiers expose sandbox
size, start rate, and kept-disk warnings via new ``EntitlementResource`` values.
"""

import json
from typing import Optional, get_type_hints

from inferencesh.types import (
    EngineCapacityLimit,
    EngineCapacityPolicy,
    EngineCapability,
    EngineDTO,
    EntitlementResource,
)


def test_engine_capacity_policy_field_contract():
    hints = get_type_hints(EngineCapacityPolicy)
    assert set(hints) == {
        "sandboxes",
        "cpu_overcommit",
        "memory_overcommit",
        "cpu_slots",
    }
    assert hints["sandboxes"] == Optional[bool]
    assert hints["cpu_overcommit"] == Optional[float]
    assert hints["memory_overcommit"] == Optional[float]
    assert hints["cpu_slots"] == Optional[int]


def test_engine_dto_exposes_optional_capacity_policy():
    hints = get_type_hints(EngineDTO)
    assert hints["capacity_policy"] == Optional[EngineCapacityPolicy]

    without: EngineDTO = {
        "id": "eng_1",
        "name": "worker-host",
        "api_url": "https://engine.example/api",
        "capabilities": [EngineCapability.SANDBOXES],
    }
    assert "capacity_policy" not in without


def test_engine_capacity_limit_bounds():
    assert EngineCapacityLimit.MAX_OVERCOMMIT == 8
    assert EngineCapacityLimit.MAX_CPU_SLOTS == 1024
    assert EngineCapacityLimit(8) is EngineCapacityLimit.MAX_OVERCOMMIT
    assert EngineCapacityLimit(1024) is EngineCapacityLimit.MAX_CPU_SLOTS


def test_sandbox_plan_entitlement_resource_wire_values():
    assert EntitlementResource.RESOURCE_SANDBOXES.value == "sandboxes"
    assert EntitlementResource.RESOURCE_SANDBOX_VCP_US.value == "sandbox_vcpus"
    assert EntitlementResource.RESOURCE_SANDBOX_MAX_VCP_US.value == "sandbox_max_vcpus"
    assert EntitlementResource.RESOURCE_SANDBOX_STARTS_PER_MIN.value == "sandbox_starts_per_min"
    assert EntitlementResource.RESOURCE_SANDBOX_KEPT_DISKS.value == "sandbox_kept_disks"

    sandbox_limits = {
        EntitlementResource.RESOURCE_SANDBOXES.value,
        EntitlementResource.RESOURCE_SANDBOX_VCP_US.value,
        EntitlementResource.RESOURCE_SANDBOX_MAX_VCP_US.value,
        EntitlementResource.RESOURCE_SANDBOX_STARTS_PER_MIN.value,
        EntitlementResource.RESOURCE_SANDBOX_KEPT_DISKS.value,
    }
    assert len(sandbox_limits) == 5


def test_engine_dto_capacity_policy_round_trips_on_wire():
    policy: EngineCapacityPolicy = {
        "sandboxes": False,
        "cpu_overcommit": 2.0,
        "memory_overcommit": 1.5,
        "cpu_slots": 64,
    }
    engine: EngineDTO = {
        "id": "eng_1",
        "name": "worker-host",
        "api_url": "https://engine.example/api",
        "capabilities": [EngineCapability.SANDBOXES, EngineCapability.CAPACITY],
        "capacity_policy": policy,
    }
    wire = json.loads(
        json.dumps(
            engine,
            default=lambda o: o.value if isinstance(o, EngineCapability) else o,
        )
    )
    assert wire["capacity_policy"]["sandboxes"] is False
    assert wire["capacity_policy"]["cpu_overcommit"] == 2.0
    assert wire["capacity_policy"]["memory_overcommit"] == 1.5
    assert wire["capacity_policy"]["cpu_slots"] == 64


def test_engine_capacity_policy_partial_update_shape():
    """Nil fields keep defaults; clients may send only what they change."""
    partial: EngineCapacityPolicy = {"cpu_slots": 32}
    assert partial["cpu_slots"] == 32
    assert "sandboxes" not in partial
