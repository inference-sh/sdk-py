"""Artifact store document shape and single-doc requests (INF-1076 / 8018b90).

List pagination for ``ArtifactDataRequest`` / ``ArtifactDataListResponse`` is
covered separately. These tests lock the per-document DTO and get/set request
fields workers use when reading or writing one row, including private documents
scoped to ``owner_user_id``.
"""

import json
from typing import Any, Dict, get_type_hints

from inferencesh.types import ArtifactDataDTO, ArtifactDataRequest


def test_artifact_data_dto_exposes_collection_doc_body_and_timestamps():
    hints = get_type_hints(ArtifactDataDTO)
    assert set(hints) >= {"collection", "doc_id", "data", "updated_at", "owner_user_id"}
    assert hints["data"] == Dict[str, Any]
    assert hints["owner_user_id"] is str

    row: ArtifactDataDTO = {
        "collection": "events",
        "doc_id": "evt-9",
        "data": {"status": "open", "priority": 2},
        "updated_at": "2026-10-17T12:00:00Z",
    }
    wire = json.loads(json.dumps(row))
    assert wire["doc_id"] == "evt-9"
    assert wire["data"]["status"] == "open"


def test_artifact_data_dto_owner_user_id_marks_private_documents():
    private: ArtifactDataDTO = {
        "collection": "notes",
        "doc_id": "note-1",
        "data": {"text": "draft"},
        "owner_user_id": "user-42",
    }
    shared: ArtifactDataDTO = {
        "collection": "notes",
        "doc_id": "note-2",
        "data": {"text": "team"},
    }
    assert private["owner_user_id"] == "user-42"
    assert "owner_user_id" not in shared


def test_artifact_data_request_single_document_get_and_set():
    hints = get_type_hints(ArtifactDataRequest)
    assert hints["doc_id"] is str
    assert hints["data"] == Dict[str, Any]

    get_one: ArtifactDataRequest = {
        "collection": "events",
        "doc_id": "evt-9",
    }
    upsert: ArtifactDataRequest = {
        "collection": "events",
        "doc_id": "evt-9",
        "data": {"status": "closed", "closed_at": "2026-10-17"},
    }
    assert get_one["doc_id"] == "evt-9"
    assert "data" not in get_one
    assert upsert["data"]["status"] == "closed"
