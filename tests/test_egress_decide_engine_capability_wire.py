"""EngineCapability egress_decide wire (dbd5320 / INF-1173).

Engines that advertise ``egress_decide`` report observed egress traffic
(``EgressResolveRequest.Observed``), apply API hold/resend/retry fields, wake
held requests on ``egress_answer``, and ack ``egress_revoke``. This sits
alongside ``egress_pending`` (first-use resolve + host reporting) and
``egress_grants`` (scoped grant lifecycle).
"""

import pytest

from inferencesh.types import EngineCapability


@pytest.mark.parametrize(
    ("member", "wire"),
    [
        (EngineCapability.EGRESS_GATEWAY, "egress_gateway"),
        (EngineCapability.EGRESS_PENDING, "egress_pending"),
        (EngineCapability.EGRESS_GRANTS, "egress_grants"),
        (EngineCapability.EGRESS_DECIDE, "egress_decide"),
    ],
)
def test_inf1173_egress_engine_capability_wire_values(member, wire):
    assert member.value == wire


def test_egress_decide_is_distinct_inf1173_capability():
    egress = {
        EngineCapability.EGRESS_GATEWAY,
        EngineCapability.EGRESS_PENDING,
        EngineCapability.EGRESS_GRANTS,
        EngineCapability.EGRESS_DECIDE,
    }
    assert len(egress) == 4
    assert EngineCapability.EGRESS_DECIDE.value == "egress_decide"
