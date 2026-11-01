"""Task egress and GPU price history wire types (309909b, 2af88cd).

Workers surface sandbox egress on completed tasks; pricing clients chart daily
cheapest instance rates from InstancePriceHistoryPointDTO rows.
"""

import json
from typing import List, Optional, get_type_hints

from inferencesh.types import InstancePriceHistoryPointDTO, TaskDTO, TaskEgress


def test_task_egress_byte_counters():
    hints = get_type_hints(TaskEgress)
    assert hints["bytes_out"] is int
    assert hints["bytes_in"] is int

    egress: TaskEgress = {"bytes_out": 4096, "bytes_in": 8192}
    assert egress["bytes_out"] < egress["bytes_in"]


def test_task_dto_carries_optional_egress():
    hints = get_type_hints(TaskDTO)
    assert hints["egress"] == Optional[TaskEgress]

    row: TaskDTO = {
        "id": "task-1",
        "egress": {"bytes_out": 100, "bytes_in": 200},
    }
    assert row["egress"]["bytes_in"] == 200


def test_instance_price_history_point_fields():
    hints = get_type_hints(InstancePriceHistoryPointDTO)
    assert set(hints) >= {
        "day",
        "on_demand",
        "spot",
        "on_demand_in_stock",
        "spot_in_stock",
        "providers",
        "regions",
    }
    assert all(hint is int for name, hint in hints.items() if name != "day")
    assert hints["day"] is str


def test_price_history_row_accepts_partial_stock_prices():
    point: InstancePriceHistoryPointDTO = {
        "day": "2026-10-01",
        "on_demand_in_stock": 125,
        "spot_in_stock": 40,
        "providers": 3,
        "regions": 2,
    }
    wire = json.loads(json.dumps(point))
    assert wire["day"] == "2026-10-01"
    assert "on_demand" not in wire
