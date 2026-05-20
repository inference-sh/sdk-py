"""Tests for structured API error types."""

import pytest

from inferencesh.models.errors import (
    APIError,
    RequirementError,
    RequirementsNotMetError,
    SessionEndedError,
    SessionExpiredError,
    SessionNotFoundError,
    SetupAction,
    WorkerLostError,
)


class TestSetupAction:
    def test_from_dict_none(self):
        assert SetupAction.from_dict(None) is None

    def test_from_dict_parses_fields(self):
        action = SetupAction.from_dict({
            "type": "connect",
            "provider": "github",
            "scopes": ["repo:read"],
        })
        assert action.type == "connect"
        assert action.provider == "github"
        assert action.scopes == ["repo:read"]


class TestRequirementError:
    def test_from_dict_with_nested_action(self):
        err = RequirementError.from_dict({
            "type": "integration",
            "key": "github",
            "message": "Connect GitHub",
            "action": {"type": "connect", "provider": "github"},
        })
        assert err.type == "integration"
        assert err.key == "github"
        assert err.message == "Connect GitHub"
        assert err.action is not None
        assert err.action.provider == "github"


class TestRequirementsNotMetError:
    def test_from_response_builds_errors(self):
        exc = RequirementsNotMetError.from_response({
            "errors": [
                {
                    "type": "secret",
                    "key": "OPENAI_API_KEY",
                    "message": "Add OPENAI_API_KEY",
                },
            ],
        })
        assert exc.status_code == 412
        assert len(exc.errors) == 1
        assert exc.errors[0].key == "OPENAI_API_KEY"
        assert str(exc) == "Add OPENAI_API_KEY"

    def test_empty_errors_uses_default_message(self):
        exc = RequirementsNotMetError([], status_code=412)
        assert str(exc) == "requirements not met"

    def test_repr_includes_errors(self):
        err = RequirementError.from_dict({
            "type": "secret",
            "key": "KEY",
            "message": "missing",
        })
        exc = RequirementsNotMetError([err])
        assert "RequirementsNotMetError" in repr(exc)
        assert "KEY" in repr(exc)


class TestSessionErrors:
    def test_session_not_found_repr(self):
        err = SessionNotFoundError("sess_x")
        assert err.status_code == 404
        assert err.session_id == "sess_x"
        assert "sess_x" in repr(err)

    def test_session_expired_repr(self):
        err = SessionExpiredError("sess_y")
        assert err.status_code == 410

    def test_session_ended_repr(self):
        err = SessionEndedError("sess_z")
        assert err.status_code == 410

    def test_worker_lost_repr(self):
        err = WorkerLostError("sess_w")
        assert err.status_code == 500


def test_api_error_repr():
    err = APIError(500, "internal error", response_body='{"detail":"boom"}')
    assert err.status_code == 500
    assert "internal error" in repr(err)
