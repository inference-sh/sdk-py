"""Task file wire types for GET/DELETE /tasks/{id}/files (v0.19 typegen).

Clients list task attachments and interpret delete outcomes via TaskFileDTO and
DeleteTaskFilesResponse. Guards against drift in role values and delete payloads.
"""

from typing import List, get_type_hints

from inferencesh.types import (
    DeleteTaskFilesResponse,
    TaskFileDTO,
    TaskFileRole,
    TaskFileSkipped,
)


def test_task_file_role_matches_api_query_values():
    assert TaskFileRole.INPUT.value == "input"
    assert TaskFileRole.OUTPUT.value == "output"
    assert set(TaskFileRole.__members__) == {"INPUT", "OUTPUT"}


def test_task_file_dto_lists_attachment_metadata():
    hints = get_type_hints(TaskFileDTO)
    assert hints["id"] is str
    assert hints["role"] is TaskFileRole
    assert hints["uri"] is str
    assert hints["filename"] is str
    assert hints["content_type"] is str
    assert hints["size"] is int
    assert hints["created_at"] is str

    file_row: TaskFileDTO = {
        "id": "file-abc",
        "created_at": "2026-10-07T12:00:00Z",
        "role": TaskFileRole.OUTPUT,
        "uri": "https://cdn.test/out.png",
        "filename": "out.png",
        "content_type": "image/png",
        "size": 4096,
    }
    assert file_row["role"] is TaskFileRole.OUTPUT


def test_delete_task_files_response_reports_deleted_and_skipped():
    skipped_hints = get_type_hints(TaskFileSkipped)
    assert skipped_hints["id"] is str
    assert skipped_hints["reason"] is str

    response_hints = get_type_hints(DeleteTaskFilesResponse)
    assert response_hints["deleted"] == List[str]
    assert response_hints["skipped"] == List[TaskFileSkipped]

    payload: DeleteTaskFilesResponse = {
        "deleted": ["file-1"],
        "skipped": [{"id": "file-2", "reason": "referenced_by_other_task"}],
    }
    assert payload["deleted"] == ["file-1"]
    assert payload["skipped"][0]["reason"] == "referenced_by_other_task"
