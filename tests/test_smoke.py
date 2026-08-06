"""Smoke tests against the live API to verify V3 envelope parsing end-to-end.

Run with: INFERENCE_SMOKE=1 pytest tests/test_smoke.py -v
Uses INFERENCE_API_KEY env var, or falls back to session token from CLI config.
"""

import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("INFERENCE_SMOKE") != "1",
    reason="set INFERENCE_SMOKE=1 to run smoke tests against the live API",
)


def _get_api_key():
    key = os.environ.get("INFERENCE_API_KEY", "")
    if key:
        return key
    config_path = Path.home() / ".inferencesh" / "config.json"
    if config_path.exists():
        cfg = json.loads(config_path.read_text())
        return cfg.get("session_token", cfg.get("api_key", ""))
    return ""


@pytest.fixture
def client():
    from inferencesh import Inference
    return Inference(api_key=_get_api_key())


@pytest.fixture
def async_client():
    from inferencesh import AsyncInference
    return AsyncInference(api_key=_get_api_key())


def test_get_me(client):
    me = client._request("GET", "/me")
    assert me is not None
    assert "user" in me
    assert me["user"]["id"]


def test_list_tasks(client):
    result = client._request("POST", "/tasks/list", data={"limit": 1})
    assert "items" in result
    assert isinstance(result["items"], list)


def test_list_plans(client):
    plans = client._request("GET", "/plans")
    assert isinstance(plans, list)
    assert len(plans) > 0
    assert "name" in plans[0]


def test_get_balance(client):
    result = client._request("GET", "/billing/balance")
    assert "balance" in result


@pytest.mark.asyncio
async def test_async_get_me(async_client):
    me = await async_client._request("GET", "/me")
    assert me is not None
    assert "user" in me
    assert me["user"]["id"]


@pytest.mark.asyncio
async def test_async_list_plans(async_client):
    plans = await async_client._request("GET", "/plans")
    assert isinstance(plans, list)
    assert len(plans) > 0
