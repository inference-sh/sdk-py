"""
Sessions integration tests for inferencesh SDK

These tests hit the real API and require INFERENCE_API_KEY to be set.
Run with: INFERENCE_API_KEY=xxx python -m pytest tests/test_sessions_integration.py -v

Prerequisites:
  - API and scheduler must be running
  - Test app deployed: infsh/session-test
"""

import os
import pytest
from inferencesh import Inference
from inferencesh.types import TaskStatus

# Get API configuration from environment
API_KEY = os.environ.get("INFERENCE_API_KEY")
BASE_URL = os.environ.get("INFERENCE_BASE_URL", "https://api.inference.sh")

# Session test app with multi-function support
SESSION_TEST_APP = "infsh/session-test"

# Skip all tests if no API key is set
pytestmark = pytest.mark.skipif(
    not API_KEY,
    reason="INFERENCE_API_KEY not set - skipping integration tests"
)


@pytest.fixture
def client():
    """Create a client instance for tests."""
    return Inference(api_key=API_KEY, base_url=BASE_URL)


class TestSessionCreation:
    """Tests for session creation."""

    def test_create_new_session_returns_real_session_id(self, client):
        """Should create a new session and return real session ID."""
        result = client.run({
            "app": SESSION_TEST_APP,
            "function": "set_value",
            "input": {"key": "test_create", "value": "hello"},
            "session": "new",
        })

        assert result["status"] == TaskStatus.COMPLETED
        assert result.get("session_id") is not None
        assert result["session_id"] != "new"
        assert len(result["session_id"]) > 0

    def test_return_correct_output_data(self, client):
        """Should return correct output data."""
        result = client.run({
            "app": SESSION_TEST_APP,
            "function": "set_value",
            "input": {"key": "output_test", "value": "test_value"},
            "session": "new",
        })

        assert result["status"] == TaskStatus.COMPLETED
        output = result.get("output", {})
        assert output.get("success") is True
        assert output.get("key") == "output_test"
        assert output.get("value") == "test_value"


class TestSessionContinuity:
    """Tests for session state persistence."""

    def test_persist_state_across_calls(self, client):
        """Should persist state across calls in same session."""
        # Create session with initial value
        result1 = client.run({
            "app": SESSION_TEST_APP,
            "function": "set_value",
            "input": {"key": "persist_key", "value": "persist_value"},
            "session": "new",
        })

        assert result1["status"] == TaskStatus.COMPLETED
        session_id = result1["session_id"]
        assert len(session_id) > 0

        # Retrieve value from same session
        result2 = client.run({
            "app": SESSION_TEST_APP,
            "function": "get_value",
            "input": {"key": "persist_key"},
            "session": session_id,
        })

        assert result2["status"] == TaskStatus.COMPLETED
        assert result2["session_id"] == session_id
        output = result2.get("output", {})
        assert output.get("found") is True
        assert output.get("value") == "persist_value"

    def test_accumulate_multiple_values(self, client):
        """Should accumulate multiple values in session."""
        # Create session
        result1 = client.run({
            "app": SESSION_TEST_APP,
            "function": "set_value",
            "input": {"key": "key1", "value": "value1"},
            "session": "new",
        })

        assert result1["status"] == TaskStatus.COMPLETED
        session_id = result1["session_id"]

        # Add second value
        result2 = client.run({
            "app": SESSION_TEST_APP,
            "function": "set_value",
            "input": {"key": "key2", "value": "value2"},
            "session": session_id,
        })

        assert result2["status"] == TaskStatus.COMPLETED

        # Get all state
        result3 = client.run({
            "app": SESSION_TEST_APP,
            "function": "get_all",
            "input": {},
            "session": session_id,
        })

        assert result3["status"] == TaskStatus.COMPLETED
        output = result3.get("output", {})
        state = output.get("state", {})
        assert state.get("key1") == "value1"
        assert state.get("key2") == "value2"


class TestMultiFunctionRouting:
    """Tests for multi-function routing."""

    def test_route_to_increment_function(self, client):
        """Should route to increment function correctly."""
        result = client.run({
            "app": SESSION_TEST_APP,
            "function": "increment",
            "input": {"key": "counter", "amount": 5},
            "session": "new",
        })

        assert result["status"] == TaskStatus.COMPLETED
        output = result.get("output", {})
        assert output.get("key") == "counter"
        assert output.get("previous") == 0
        assert output.get("current") == 5


class TestSessionIsolation:
    """Tests for session isolation."""

    def test_different_sessions_for_new_requests(self, client):
        """Should create different sessions for different 'new' requests."""
        # Create first session
        result1 = client.run({
            "app": SESSION_TEST_APP,
            "function": "set_value",
            "input": {"key": "isolated", "value": "session1"},
            "session": "new",
        })

        assert result1["status"] == TaskStatus.COMPLETED
        session1 = result1["session_id"]

        # Create second session
        result2 = client.run({
            "app": SESSION_TEST_APP,
            "function": "set_value",
            "input": {"key": "isolated", "value": "session2"},
            "session": "new",
        })

        assert result2["status"] == TaskStatus.COMPLETED
        session2 = result2["session_id"]

        # Sessions should be different
        assert session1 != session2


class TestSessionsAPI:
    """Tests for Sessions API methods."""

    def test_get_session_info(self, client):
        """Should get session info."""
        # Create a session
        result = client.run({
            "app": SESSION_TEST_APP,
            "function": "set_value",
            "input": {"key": "api_test", "value": "hello"},
            "session": "new",
        })

        assert result["status"] == TaskStatus.COMPLETED
        session_id = result["session_id"]

        # Get session info via API
        session_info = client.sessions.get(session_id)

        assert session_info.get("id") == session_id
        assert session_info.get("status") == "active"
        assert session_info.get("call_count", 0) >= 1

    def test_list_sessions(self, client):
        """Should list sessions."""
        sessions = client.sessions.list()
        assert isinstance(sessions, list)

    def test_keepalive_session(self, client):
        """Should keepalive a session."""
        # Create a session
        result = client.run({
            "app": SESSION_TEST_APP,
            "function": "set_value",
            "input": {"key": "keepalive_test", "value": "hello"},
            "session": "new",
        })

        assert result["status"] == TaskStatus.COMPLETED
        session_id = result["session_id"]

        # Keepalive
        updated = client.sessions.keepalive(session_id)

        assert updated.get("id") == session_id
        assert updated.get("status") == "active"

    def test_end_session(self, client):
        """Should end a session."""
        # Create a session
        result = client.run({
            "app": SESSION_TEST_APP,
            "function": "set_value",
            "input": {"key": "end_test", "value": "goodbye"},
            "session": "new",
        })

        assert result["status"] == TaskStatus.COMPLETED
        session_id = result["session_id"]

        # End the session
        client.sessions.end(session_id)

        # Trying to use ended session should fail
        with pytest.raises(Exception):
            client.run({
                "app": SESSION_TEST_APP,
                "function": "get_value",
                "input": {"key": "end_test"},
                "session": session_id,
            })


class TestErrorCases:
    """Tests for error cases."""

    def test_fail_with_invalid_session_id(self, client):
        """Should fail with invalid session ID."""
        with pytest.raises(Exception):
            client.run({
                "app": SESSION_TEST_APP,
                "function": "get_value",
                "input": {"key": "foo"},
                "session": "sess_invalid_does_not_exist_12345",
            })


class TestPerformance:
    """Performance tests."""

    def test_warm_worker_faster(self, client):
        """Should be faster on warm worker."""
        import time

        # Create session (cold start)
        result1 = client.run({
            "app": SESSION_TEST_APP,
            "function": "set_value",
            "input": {"key": "perf_test", "value": "1"},
            "session": "new",
        })

        assert result1["status"] == TaskStatus.COMPLETED
        session_id = result1["session_id"]

        # Second call should be fast (warm worker)
        start = time.time()
        result2 = client.run({
            "app": SESSION_TEST_APP,
            "function": "set_value",
            "input": {"key": "perf_test", "value": "2"},
            "session": session_id,
        })
        elapsed = (time.time() - start) * 1000

        assert result2["status"] == TaskStatus.COMPLETED

        print(f"Warm worker call took: {elapsed:.0f}ms")

        # Should be under 2 seconds for warm worker
        assert elapsed < 2000


# This always runs to ensure pytest doesn't complain about no tests
class TestSessionsIntegrationSetup:
    """Basic setup verification."""

    def test_api_key_check(self):
        """Verify test setup is working."""
        if not API_KEY:
            print("Warning: Skipping sessions integration tests - INFERENCE_API_KEY not set")
        assert True
