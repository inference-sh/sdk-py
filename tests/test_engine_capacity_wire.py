"""Engine capacity telemetry types (3976968 / models v0.8.153, INF-1156).

Engines with ``EngineCapability.CAPACITY`` report ``EngineCapacity`` on
``EngineDTO``: machine totals, host reserve, allocatable headroom, committed
quotas (workers and sandboxes), and current use. Fractional CPU in ``used`` is
valid on the wire.
"""

import json
from typing import List, Optional, get_type_hints

from inferencesh.types import (
    CapacityAmount,
    CapacityGPU,
    EngineCapability,
    EngineCapacity,
    EngineDTO,
)


def test_engine_capacity_field_contract():
    hints = get_type_hints(EngineCapacity)
    assert set(hints) == {
        "cpus",
        "cores",
        "memory_bytes",
        "disk_bytes",
        "disk_free_bytes",
        "gpus",
        "reserve",
        "allocatable",
        "committed",
        "used",
    }
    assert hints["cpus"] is int
    assert hints["cores"] is int
    assert hints["memory_bytes"] is int
    assert hints["disk_bytes"] is int
    assert hints["disk_free_bytes"] is int
    assert hints["gpus"] == List[CapacityGPU]
    assert hints["reserve"] is CapacityAmount
    assert hints["allocatable"] is CapacityAmount
    assert hints["committed"] is CapacityAmount
    assert hints["used"] is CapacityAmount


def test_capacity_amount_supports_fractional_cpus():
    hints = get_type_hints(CapacityAmount)
    assert hints["cpus"] is float
    assert hints["memory_bytes"] is int

    used: CapacityAmount = {"cpus": 1.5, "memory_bytes": 6_442_450_944}
    assert used["cpus"] == 1.5


def test_capacity_gpu_fields():
    hints = get_type_hints(CapacityGPU)
    assert hints["id"] is str
    assert hints["vram_bytes"] is int

    gpu: CapacityGPU = {"id": "GPU-0", "vram_bytes": 24_169_435_136}
    assert gpu["id"] == "GPU-0"


def test_engine_dto_exposes_optional_capacity():
    hints = get_type_hints(EngineDTO)
    assert hints["capacity"] == Optional[EngineCapacity]

    without: EngineDTO = {
        "id": "eng_1",
        "name": "worker-host",
        "api_url": "https://engine.example/api",
        "capabilities": [EngineCapability.EGRESS_GATEWAY],
    }
    assert "capacity" not in without


def test_engine_capability_capacity_wire_value():
    assert EngineCapability.CAPACITY.value == "capacity"
    assert EngineCapability("capacity") is EngineCapability.CAPACITY


def test_engine_dto_capacity_round_trips_on_wire():
    capacity: EngineCapacity = {
        "cpus": 32,
        "cores": 16,
        "memory_bytes": 137_438_953_472,
        "disk_bytes": 2_000_000_000_000,
        "disk_free_bytes": 1_500_000_000_000,
        "gpus": [{"id": "GPU-0", "vram_bytes": 24_169_435_136}],
        "reserve": {"cpus": 2.0, "memory_bytes": 4_294_967_296},
        "allocatable": {"cpus": 28.0, "memory_bytes": 128_849_018_880},
        "committed": {"cpus": 8.0, "memory_bytes": 34_359_738_368},
        "used": {"cpus": 1.5, "memory_bytes": 6_442_450_944},
    }
    engine: EngineDTO = {
        "id": "eng_1",
        "name": "worker-host",
        "api_url": "https://engine.example/api",
        "capabilities": [EngineCapability.CAPACITY, EngineCapability.SANDBOXES],
        "capacity": capacity,
    }
    wire = json.loads(
        json.dumps(
            engine,
            default=lambda o: o.value if isinstance(o, EngineCapability) else o,
        )
    )
    assert wire["capabilities"] == ["capacity", "sandboxes"]
    assert wire["capacity"]["used"]["cpus"] == 1.5
    assert wire["capacity"]["gpus"][0]["id"] == "GPU-0"
