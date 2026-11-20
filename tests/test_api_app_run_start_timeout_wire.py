"""POST /apps/run ``start_timeout`` wire (3708fd8 / api#2344).

If no worker starts the task within ``start_timeout`` seconds (from ``run_at``
when scheduled), the task is cancelled without billing. SDK callers pass it via
``client.run`` params; this pins the generated ``ApiAppRunRequest`` field.
"""

import json
from typing import Optional, get_type_hints

from inferencesh.types import ApiAppRunRequest


def test_api_app_run_request_start_timeout_optional_int():
    hints = get_type_hints(ApiAppRunRequest)
    assert hints["start_timeout"] == Optional[int]
    assert hints["run_at"] == Optional[str]
    assert hints["session_timeout"] == Optional[int]


def test_api_app_run_request_start_timeout_json_round_trip():
    req: ApiAppRunRequest = {
        "app": "okaris/flux@abc1",
        "input": {"prompt": "hello"},
        "run_at": "2026-11-11T12:00:00Z",
        "start_timeout": 600,
    }
    wire = json.loads(json.dumps(req))
    assert wire["start_timeout"] == 600
    assert wire["run_at"] == "2026-11-11T12:00:00Z"


def test_api_app_run_request_start_timeout_omitted_for_immediate_run():
    """total=False: immediate runs need not send start_timeout."""
    req: ApiAppRunRequest = {
        "app": "okaris/flux@abc1",
        "input": {"prompt": "now"},
        "wait": True,
    }
    wire = json.loads(json.dumps(req))
    assert "start_timeout" not in wire


def test_api_app_run_request_start_timeout_accepts_documented_bounds():
    """API accepts 1–86400 seconds per typegen comment."""
    low: ApiAppRunRequest = {"app": "x/y@z1", "input": {}, "start_timeout": 1}
    high: ApiAppRunRequest = {"app": "x/y@z1", "input": {}, "start_timeout": 86400}
    assert json.loads(json.dumps(low))["start_timeout"] == 1
    assert json.loads(json.dumps(high))["start_timeout"] == 86400


def test_api_app_run_request_start_timeout_with_session_scheduling_fields():
    """Coexists with session pinning fields on the same run body."""
    req: ApiAppRunRequest = {
        "app": "demo/browser@w1",
        "input": {},
        "session": "new",
        "session_timeout": 300,
        "start_timeout": 120,
    }
    wire = json.loads(json.dumps(req))
    assert wire["session_timeout"] == 300
    assert wire["start_timeout"] == 120
