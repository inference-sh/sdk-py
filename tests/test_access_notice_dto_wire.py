"""Structured redlist access notice wire types (8c14bec).

GET /me can carry the same redlist notice as flat ``notice`` /
``notice_reference`` / ``notice_contact`` fields in structured
``access_notice`` (lure vs legal stage, CLI install hints, legal case id).
Refusal meta may embed the same object under ``notice``.
"""

import json
from typing import Optional, get_type_hints

from inferencesh.types import AccessNoticeDTO, MeResponse


def test_access_notice_dto_exposes_redlist_fields():
    hints = get_type_hints(AccessNoticeDTO)
    assert set(hints) >= {
        "stage",
        "text",
        "reference",
        "contact",
        "install_url",
        "install_command",
        "case",
    }
    assert all(hint is str for hint in hints.values())


def test_me_response_access_notice_is_optional_structured_notice():
    hints = get_type_hints(MeResponse)
    assert hints["access_notice"] == Optional[AccessNoticeDTO]

    lure: AccessNoticeDTO = {
        "stage": "lure",
        "text": "Install the CLI and sign in from an approved network.",
        "reference": "POL-42",
        "contact": "security@example.com",
        "install_url": "https://inference.sh/install",
        "install_command": "curl -fsSL https://inference.sh/install | sh",
    }
    me: MeResponse = {
        "notice": lure["text"],
        "notice_reference": lure["reference"],
        "notice_contact": lure["contact"],
        "access_notice": lure,
    }
    assert me["access_notice"]["stage"] == "lure"
    assert me["access_notice"]["install_command"].startswith("curl")


def test_access_notice_legal_stage_carries_case_reference():
    legal: AccessNoticeDTO = {
        "stage": "legal",
        "text": "Access is restricted pending review.",
        "reference": "REF-9",
        "contact": "legal@example.com",
        "case": "CASE-2026-11",
    }
    wire = json.loads(json.dumps(legal))
    assert wire["stage"] == "legal"
    assert wire["case"] == "CASE-2026-11"
    assert "install_url" not in wire
