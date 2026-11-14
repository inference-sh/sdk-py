"""Sandbox filesystem import/export wire types (92e2300).

Running sandboxes expose directory listings and file transfer endpoints:
``GET /sandboxes/{id}/files`` returns ``SandboxFileEntry`` rows;
``POST .../files/import`` and ``.../files/export`` take the request DTOs and
answer with ``SandboxFileTransferDTO`` (platform ``FileDTO`` plus optional
download URL on export).
"""

import json
from typing import List, Optional, get_type_hints

from inferencesh.types import (
    FileDTO,
    SandboxFileEntry,
    SandboxFileExportRequest,
    SandboxFileImportRequest,
    SandboxFileKind,
    SandboxFileTransferDTO,
)


def test_sandbox_file_kind_wire_values():
    assert SandboxFileKind.FILE.value == "file"
    assert SandboxFileKind.DIR.value == "dir"
    assert SandboxFileKind.LINK.value == "link"
    assert SandboxFileKind.OTHER.value == "other"


def test_sandbox_file_entry_directory_listing_contract():
    hints = get_type_hints(SandboxFileEntry)
    assert set(hints) == {"name", "kind", "size", "mode", "modified_at"}
    assert hints["name"] is str
    assert hints["kind"] is SandboxFileKind
    assert hints["size"] is int
    assert hints["mode"] is str
    assert hints["modified_at"] == Optional[str]


def test_sandbox_file_entry_accepts_listing_row():
    entries: List[SandboxFileEntry] = [
        {
            "name": "src",
            "kind": SandboxFileKind.DIR,
            "size": 4096,
            "mode": "0755",
            "modified_at": "2026-11-10T09:00:00Z",
        },
        {
            "name": "README.md",
            "kind": SandboxFileKind.FILE,
            "size": 128,
            "mode": "0644",
            "modified_at": "2026-11-10T08:30:00Z",
        },
        {
            "name": "venv",
            "kind": SandboxFileKind.LINK,
            "size": 0,
            "mode": "0777",
        },
    ]
    assert entries[0]["kind"] is SandboxFileKind.DIR
    assert entries[1]["name"] == "README.md"
    assert "modified_at" not in entries[2]


def test_sandbox_file_import_and_export_request_contracts():
    import_hints = get_type_hints(SandboxFileImportRequest)
    export_hints = get_type_hints(SandboxFileExportRequest)
    assert set(import_hints) == {"path", "file_id"}
    assert set(export_hints) == {"path"}
    assert import_hints["path"] is str
    assert import_hints["file_id"] is str
    assert export_hints["path"] is str


def test_sandbox_file_import_and_export_requests_round_trip():
    pull: SandboxFileImportRequest = {
        "path": "/workspace/model.bin",
        "file_id": "file_abc123",
    }
    push: SandboxFileExportRequest = {"path": "/workspace/out/result.json"}

    wire = json.loads(json.dumps({"pull": pull, "push": push}))
    assert wire["pull"]["path"] == "/workspace/model.bin"
    assert wire["pull"]["file_id"] == "file_abc123"
    assert wire["push"]["path"] == "/workspace/out/result.json"


def test_sandbox_file_transfer_dto_contract():
    hints = get_type_hints(SandboxFileTransferDTO)
    assert set(hints) == {"path", "file", "download_url"}
    assert hints["path"] is str
    assert hints["file"] == Optional[FileDTO]
    assert hints["download_url"] is str


def test_sandbox_file_transfer_dto_import_and_export_shapes():
    platform_file: FileDTO = {
        "id": "file_abc123",
        "uri": "https://files.example/file_abc123",
        "filename": "model.bin",
        "size": 1_048_576,
        "content_type": "application/octet-stream",
    }
    after_import: SandboxFileTransferDTO = {
        "path": "/workspace/model.bin",
        "file": platform_file,
    }
    after_export: SandboxFileTransferDTO = {
        "path": "/workspace/out/result.json",
        "file": {
            "id": "file_export99",
            "uri": "https://files.example/file_export99",
            "filename": "result.json",
            "size": 4096,
            "content_type": "application/json",
        },
        "download_url": "https://files.example/download/file_export99?token=short",
    }
    assert after_import["file"]["size"] == 1_048_576
    assert after_export["download_url"].startswith("https://")
    assert "download_url" not in after_import
