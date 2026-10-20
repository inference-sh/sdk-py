"""Instance price history points (2af88cd / GET /instances/types/price-history).

Each row is one day's cheapest hourly GPU prices in cents. Listed prices can
differ from in-stock minima; fields with no listing or stock that day are
omitted on the wire (``total=False``).
"""

import json
from typing import get_type_hints

from inferencesh.types import InstancePriceHistoryPointDTO


def test_instance_price_history_point_field_contract():
    hints = get_type_hints(InstancePriceHistoryPointDTO)
    assert set(hints) == {
        "day",
        "on_demand",
        "spot",
        "on_demand_in_stock",
        "spot_in_stock",
        "providers",
        "regions",
    }
    assert hints["day"] is str
    for key in (
        "on_demand",
        "spot",
        "on_demand_in_stock",
        "spot_in_stock",
        "providers",
        "regions",
    ):
        assert hints[key] is int


def test_instance_price_history_point_allows_partial_daily_rows():
    """API omits price slots when there was no listing or stock that day."""
    listed_only: InstancePriceHistoryPointDTO = {
        "day": "2026-10-19",
        "on_demand": 249,
        "spot": 119,
        "providers": 3,
    }
    assert listed_only["on_demand"] == 249
    assert "on_demand_in_stock" not in listed_only

    in_stock_only: InstancePriceHistoryPointDTO = {
        "day": "2026-10-20",
        "on_demand_in_stock": 299,
        "spot_in_stock": 149,
        "regions": 2,
    }
    assert in_stock_only["regions"] == 2
    assert "on_demand" not in in_stock_only


def test_instance_price_history_point_serializes_snake_case_wire_keys():
    point: InstancePriceHistoryPointDTO = {
        "day": "2026-10-18",
        "on_demand": 199,
        "on_demand_in_stock": 229,
        "spot_in_stock": 99,
        "providers": 4,
        "regions": 1,
    }
    payload = json.loads(json.dumps(point))
    assert payload == {
        "day": "2026-10-18",
        "on_demand": 199,
        "on_demand_in_stock": 229,
        "spot_in_stock": 99,
        "providers": 4,
        "regions": 1,
    }
    assert "onDemand" not in payload
    assert "spotInStock" not in payload
