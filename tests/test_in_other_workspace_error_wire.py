"""in_other_workspace error code and InOtherWorkspaceMeta (3e8aacb typegen).

When a resource lives in another workspace the caller belongs to, the API
returns problem+json with code ``in_other_workspace`` and meta ``team_id`` so
clients can offer a workspace switch. These tests lock the generated enum and
meta shape and that ``APIError.code`` parses the new problem type.
"""

import json
from typing import get_type_hints

from inferencesh.models.errors import APIError
from inferencesh.types import ErrorCode, InOtherWorkspaceMeta


def test_in_other_workspace_error_code_wire_value():
    assert ErrorCode.IN_OTHER_WORKSPACE.value == "in_other_workspace"
    assert ErrorCode("in_other_workspace") is ErrorCode.IN_OTHER_WORKSPACE


def test_in_other_workspace_meta_declares_team_id():
    hints = get_type_hints(InOtherWorkspaceMeta)
    assert hints == {"team_id": str}


def test_in_other_workspace_meta_accepts_team_id():
    meta: InOtherWorkspaceMeta = {"team_id": "team_acme_prod"}
    wire = json.loads(json.dumps(meta))
    assert wire == {"team_id": "team_acme_prod"}
    parsed: InOtherWorkspaceMeta = wire  # type: ignore[assignment]
    assert parsed["team_id"] == "team_acme_prod"


def test_api_error_code_reads_in_other_workspace_from_problem_json():
    body = (
        '{"type":"https://api.inference.sh/errors/in_other_workspace",'
        '"status":404,"detail":"Open this agent in Acme",'
        '"meta":{"team_id":"team_acme_prod"}}'
    )
    err = APIError(404, "Open this agent in Acme", response_body=body)
    assert err.code == ErrorCode.IN_OTHER_WORKSPACE.value


def test_in_other_workspace_distinct_from_team_role_required():
    assert ErrorCode.IN_OTHER_WORKSPACE.value != ErrorCode.TEAM_ROLE_REQUIRED.value
