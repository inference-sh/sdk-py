"""Engine egress_decide capability wire (dbd5320 / v0.38.10, INF-1173).

Engines that report ``EngineCapabilityEgressDecide`` observe egress resolve
requests (``EgressResolveRequest.Observed``), apply hold/resend/retry fields
from the API decision, wake held traffic on ``egress_answer``, and ack
``egress_revoke``. This sits alongside ``egress_pending`` and ``egress_grants``
in the INF-1173 gateway contract.
"""

import json
from typing import List, get_type_hints

from inferencesh.types import EngineCapability, EngineDTO

INF1173_EGRESS_CAPABILITIES = (
    (EngineCapability.EGRESS_GATEWAY, "egress_gateway"),
    (EngineCapability.EGRESS_PENDING, "egress_pending"),
    (EngineCapability.EGRESS_GRANTS, "egress_grants"),
    (EngineCapability.EGRESS_DECIDE, "egress_decide"),
)


def test_egress_decide_wire_value():
    assert EngineCapability.EGRESS_DECIDE.value == "egress_decide"


def test_egress_decide_parses_from_api_wire_string():
    assert EngineCapability("egress_decide") is EngineCapability.EGRESS_DECIDE


def test_inf1173_egress_engine_capabilities_are_distinct():
    wires = [wire for _, wire in INF1173_EGRESS_CAPABILITIES]
    assert len(wires) == len(set(wires))
    for member, wire in INF1173_EGRESS_CAPABILITIES:
        assert member.value == wire


def test_engine_dto_capabilities_typed_as_engine_capability_list():
    hints = get_type_hints(EngineDTO)
    assert hints["capabilities"] == List[EngineCapability]


def test_engine_dto_accepts_egress_decide_in_capabilities():
    engine: EngineDTO = {
        "name": "gateway-1",
        "capabilities": [
            EngineCapability.EGRESS_GATEWAY,
            EngineCapability.EGRESS_DECIDE,
        ],
    }
    assert EngineCapability.EGRESS_DECIDE in engine["capabilities"]
    payload = json.dumps({"capabilities": [c.value for c in engine["capabilities"]]})
    restored = json.loads(payload)["capabilities"]
    assert restored == ["egress_gateway", "egress_decide"]
