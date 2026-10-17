"""Engine release channels, artifact site files, compaction markers (87aa1b8).

Workers pin engine builds via ``EngineDTO.engine_pin`` and update endpoints
accept ``EngineUpdateRequest``. Release heads are ``EngineReleasesResponse``.
Artifact publishes replace the whole site: ``files`` on create/publish requests
and ``ArtifactVersionDTO.files`` list published paths. Chat compaction stores
``CompactionMeta`` on messages. OAuth app credentials may expose
``CredentialDTO.allowed_scopes``.
"""

import json
from typing import List, Optional, get_type_hints

from inferencesh.types import (
    ArtifactCreateRequest,
    ArtifactFileInput,
    ArtifactPublishRequest,
    ArtifactVersionDTO,
    ArtifactVersionFileDTO,
    ChatMessageDTO,
    CompactionMeta,
    CredentialDTO,
    EngineDTO,
    EngineRelease,
    EngineReleasesResponse,
    EngineUpdateRequest,
)


def test_engine_update_request_accepts_channel_or_version():
    hints = get_type_hints(EngineUpdateRequest)
    assert hints == {"version": str}
    for body in (
        EngineUpdateRequest(version="stable"),
        EngineUpdateRequest(version="canary"),
        EngineUpdateRequest(version="v1.9.3"),
        EngineUpdateRequest(version=""),
    ):
        assert "version" in body


def test_engine_releases_response_heads_use_engine_release_shape():
    hints = get_type_hints(EngineReleasesResponse)
    assert hints["stable"] == Optional[EngineRelease]
    assert hints["canary"] == Optional[EngineRelease]
    release_hints = get_type_hints(EngineRelease)
    assert set(release_hints) == {"version", "release_date"}

    response: EngineReleasesResponse = {
        "stable": {"version": "v1.9.3", "release_date": "2026-10-01"},
        "canary": {"version": "v1.9.4-rc1", "release_date": "2026-10-15"},
    }
    assert response["stable"]["version"] == "v1.9.3"


def test_engine_dto_exposes_engine_pin():
    hints = get_type_hints(EngineDTO)
    assert hints["engine_pin"] is str

    pinned: EngineDTO = {"engine_version": "v1.9.2", "engine_pin": "v1.9.2"}
    following: EngineDTO = {"engine_version": "v1.9.3", "engine_pin": ""}
    assert pinned["engine_pin"] == pinned["engine_version"]
    assert following["engine_pin"] == ""


def test_artifact_file_input_and_version_file_dto_contracts():
    input_hints = get_type_hints(ArtifactFileInput)
    assert set(input_hints) >= {"path", "content", "content_encoding"}

    file_hints = get_type_hints(ArtifactVersionFileDTO)
    assert set(file_hints) == {"path", "size_bytes", "content_type"}

    asset: ArtifactFileInput = {
        "path": "styles/site.css",
        "content": "body{margin:0}",
        "content_encoding": "",
    }
    published: ArtifactVersionFileDTO = {
        "path": "styles/site.css",
        "size_bytes": 14,
        "content_type": "text/css",
    }
    assert asset["path"] == published["path"]


def test_artifact_publish_requests_carry_whole_site_files_list():
    for cls in (ArtifactCreateRequest, ArtifactPublishRequest):
        hints = get_type_hints(cls)
        assert hints["files"] == List[ArtifactFileInput]

    publish: ArtifactPublishRequest = {
        "content": "# hello",
        "files": [
            {"path": "extra.md", "content": "sidecar"},
            {"path": "data.json", "content": "{}", "content_encoding": "base64"},
        ],
    }
    assert len(publish["files"]) == 2
    assert publish["files"][1]["content_encoding"] == "base64"


def test_artifact_version_dto_lists_published_files():
    hints = get_type_hints(ArtifactVersionDTO)
    assert hints["files"] == List[ArtifactVersionFileDTO]

    version: ArtifactVersionDTO = {
        "id": "ver-1",
        "files": [
            {"path": "index.html", "size_bytes": 120, "content_type": "text/html"},
        ],
    }
    wire = json.loads(json.dumps(version))
    assert wire["files"][0]["path"] == "index.html"


def test_chat_message_dto_compaction_meta_contract():
    hints = get_type_hints(ChatMessageDTO)
    assert hints["compaction_meta"] == Optional[CompactionMeta]

    meta_hints = get_type_hints(CompactionMeta)
    assert set(meta_hints) >= {
        "compacted_up_to_order",
        "compacted_count",
        "estimated_tokens",
        "method",
        "analysis",
    }

    marker: ChatMessageDTO = {
        "content": "",
        "compaction_meta": {
            "compacted_up_to_order": 41,
            "compacted_count": 12,
            "estimated_tokens": 8000,
            "method": "summarize",
            "analysis": "retired tool traces",
        },
    }
    assert marker["compaction_meta"]["compacted_count"] == 12


def test_credential_dto_allowed_scopes_for_oauth_apps():
    hints = get_type_hints(CredentialDTO)
    assert hints["allowed_scopes"] == List[str]

    grant_app: CredentialDTO = {
        "provider": "slack",
        "allowed_scopes": ["channels:read", "chat:write"],
    }
    login: CredentialDTO = {
        "provider": "slack",
        "scopes": ["channels:read"],
    }
    assert grant_app["allowed_scopes"] == ["channels:read", "chat:write"]
    assert "allowed_scopes" not in login
