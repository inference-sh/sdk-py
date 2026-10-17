"""Engine capability reporting and artifact data list pagination (INF-1076 / 8018b90).

Engines advertise optional features via ``EngineDTO.capabilities`` (a list of
``EngineCapability`` wire values). Artifact collection reads accept cursor,
order, and filter fields on ``ArtifactDataRequest``; list responses expose
``next_cursor`` for paging.
"""

import json
from typing import List, get_type_hints

from inferencesh.types import (
    ArtifactDataListResponse,
    ArtifactDataRequest,
    EngineCapability,
    EngineDTO,
)


def test_engine_capability_egress_gateway_wire_value():
    assert EngineCapability.EGRESS_GATEWAY.value == "egress_gateway"
    assert json.dumps(EngineCapability.EGRESS_GATEWAY) == '"egress_gateway"'


def test_engine_dto_exposes_capabilities_list():
    hints = get_type_hints(EngineDTO)
    assert hints["capabilities"] == List[EngineCapability]

    engine: EngineDTO = {
        "engine_version": "v1.9.3",
        "capabilities": [EngineCapability.EGRESS_GATEWAY],
    }
    assert engine["capabilities"][0] is EngineCapability.EGRESS_GATEWAY


def test_engine_dto_capabilities_empty_list_means_base_contract_only():
    engine: EngineDTO = {"capabilities": []}
    assert engine["capabilities"] == []


def test_artifact_data_request_list_query_fields():
    hints = get_type_hints(ArtifactDataRequest)
    assert set(hints) >= {"collection", "limit", "cursor", "order", "where"}

    req: ArtifactDataRequest = {
        "collection": "events",
        "limit": 50,
        "cursor": "page-2-token",
        "order": "-updated_at",
        "where": {"status": "open", "priority": 1, "archived": False},
    }
    assert req["order"].startswith("-")
    assert req["where"]["status"] == "open"


def test_artifact_data_list_response_next_cursor_pagination():
    hints = get_type_hints(ArtifactDataListResponse)
    assert hints["next_cursor"] is str

    last_page: ArtifactDataListResponse = {
        "collection": "events",
        "documents": [],
        "count": 0,
        "next_cursor": "",
    }
    more: ArtifactDataListResponse = {
        "collection": "events",
        "documents": [{"collection": "events", "doc_id": "a1"}],
        "count": 1,
        "next_cursor": "page-3-token",
    }
    assert last_page["next_cursor"] == ""
    assert more["next_cursor"] == "page-3-token"
