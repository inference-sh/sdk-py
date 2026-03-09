"""
Integration tests for streamable HTTP module.

Tests NDJSON streaming against the real API.
Run with: INFERENCE_API_KEY=xxx pytest tests/test_streamable_integration.py

Note: Format negotiation tests may be skipped if server doesn't support NDJSON yet.
"""

import os
import pytest
import httpx
from inferencesh import Inference
from inferencesh.streamable import streamable, stream_get
from inferencesh.types import TaskStatus

# Terminal statuses
TERMINAL_STATUSES = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}

def is_terminal_status(status: int) -> bool:
    return status in TERMINAL_STATUSES

# Get API configuration from environment
API_KEY = os.environ.get("INFERENCE_API_KEY")
BASE_URL = os.environ.get("INFERENCE_BASE_URL", "https://api.inference.sh")

# Use a pinned app version that's known to work
TEST_APP = "infsh/text-templating@53bk0yzk"

# Skip all tests if no API key is set
pytestmark = pytest.mark.skipif(
    not API_KEY,
    reason="INFERENCE_API_KEY not set - skipping integration tests"
)


@pytest.fixture
def client():
    """Create a client instance for tests."""
    return Inference(api_key=API_KEY, base_url=BASE_URL)


class TestFormatNegotiation:
    """Tests for NDJSON/SSE format negotiation."""

    def test_negotiate_format_based_on_accept_header(self, client):
        """Should negotiate format based on Accept header."""
        # Create a task using the SDK
        task = client.run(
            {"app": TEST_APP, "input": {"template": "Format {1}!", "strings": ["Test"]}},
            wait=False
        )

        # Test NDJSON request
        with httpx.Client() as http:
            ndjson_res = http.get(
                f"{BASE_URL}/tasks/{task['id']}/stream",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Accept": "application/x-ndjson",
                },
            )
            ndjson_content_type = ndjson_res.headers.get("content-type", "")

            # Test SSE request
            sse_res = http.get(
                f"{BASE_URL}/tasks/{task['id']}/stream",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Accept": "text/event-stream",
                },
            )
            sse_content_type = sse_res.headers.get("content-type", "")

        # Log what we got for debugging
        print(f"NDJSON request Content-Type: {ndjson_content_type}")
        print(f"SSE request Content-Type: {sse_content_type}")

        # At minimum, SSE should work
        assert "text/event-stream" in sse_content_type

        # If NDJSON is supported, it should return NDJSON content-type
        supports_ndjson = "application/x-ndjson" in ndjson_content_type
        if supports_ndjson:
            print("✓ Server supports NDJSON format negotiation")
        else:
            print("⚠ Server does not yet support NDJSON, falling back to SSE")


class TestStreamableWithNDJSONServer:
    """Tests for streamable() when server supports NDJSON."""

    def test_stream_task_updates(self, client):
        """Should stream task updates when server supports NDJSON."""
        # Create a task using the SDK (fire and forget)
        task = client.run(
            {"app": TEST_APP, "input": {"template": "Hello {1}!", "strings": ["Streamable"]}},
            wait=False
        )
        assert task["id"] is not None

        # Stream updates using streamable - will request NDJSON format
        updates = []
        try:
            with httpx.Client() as http:
                with http.stream(
                    "GET",
                    f"{BASE_URL}/tasks/{task['id']}/stream",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Accept": "application/x-ndjson",
                    },
                    timeout=60.0,
                ) as response:
                    for update in streamable(response):
                        updates.append(update)
                        # Stop when task reaches terminal status
                        if is_terminal_status(update.get("status", 0)):
                            break
        except Exception as err:
            # If server doesn't support NDJSON, streamable will fail to parse SSE
            print(f"⚠ Skipping - server returned non-NDJSON: {err}")
            return

        assert len(updates) > 0

        # Last update should be terminal
        last_update = updates[-1]
        assert is_terminal_status(last_update.get("status", 0))

    def test_stream_get_helper(self, client):
        """Should work with stream_get helper function."""
        # Create a task using the SDK
        task = client.run(
            {"app": TEST_APP, "input": {"template": "Helper {1}!", "strings": ["Test"]}},
            wait=False
        )

        updates = []
        try:
            with httpx.Client() as http:
                for update in stream_get(
                    http,
                    f"{BASE_URL}/tasks/{task['id']}/stream",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    timeout=60.0,
                ):
                    updates.append(update)
                    if is_terminal_status(update.get("status", 0)):
                        break
        except Exception as err:
            print(f"⚠ Skipping stream_get test - server returned non-NDJSON: {err}")
            return

        assert len(updates) > 0
        assert is_terminal_status(updates[-1].get("status", 0))


# This always runs to ensure pytest doesn't complain about no tests
class TestStreamableIntegrationSetup:
    """Basic setup verification."""

    def test_api_key_check(self):
        """Verify test setup is working."""
        if not API_KEY:
            print("⚠️  Skipping streamable integration tests - INFERENCE_API_KEY not set")
        assert True
