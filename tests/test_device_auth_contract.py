"""Contract guards for device-auth and scope errors (models v0.8.95)."""

from typing import get_type_hints

from inferencesh.models.errors import APIError
from inferencesh.types import (
    DeviceAuthPollResponse,
    DeviceAuthStatus,
    DeviceTokenKind,
    ErrorCode,
)


class TestDeviceAuthStatusWireValues:
    def test_rfc8628_slow_down_status(self):
        assert DeviceAuthStatus.SLOW_DOWN.value == "slow_down"

    def test_pending_flow_statuses(self):
        assert DeviceAuthStatus.PENDING.value == "pending"
        assert DeviceAuthStatus.APPROVED.value == "approved"
        assert DeviceAuthStatus.DENIED.value == "denied"
        assert DeviceAuthStatus.EXPIRED.value == "expired"

    def test_session_validation_statuses(self):
        assert DeviceAuthStatus.VALID.value == "valid"
        assert DeviceAuthStatus.INVALID.value == "invalid"
        assert DeviceAuthStatus.LOADING.value == "loading"


class TestDeviceTokenKindWireValues:
    def test_session_vs_api_key_selects_credential_type(self):
        assert DeviceTokenKind.SESSION.value == "session"
        assert DeviceTokenKind.API_KEY.value == "api_key"


class TestDeviceAuthPollResponseShape:
    def test_slow_down_carries_interval_seconds(self):
        """RFC 8628 §3.5: slow_down responses include the new polling interval."""
        hints = get_type_hints(DeviceAuthPollResponse)
        assert "interval" in hints
        assert hints["interval"] is int


class TestDeviceAuthErrorCodes:
    def test_invalid_scope_wire_value(self):
        assert ErrorCode.INVALID_SCOPE.value == "invalid_scope"

    def test_code_confirmation_required_wire_value(self):
        assert ErrorCode.CODE_CONFIRMATION_REQUIRED.value == "code_confirmation_required"

    def test_api_error_reads_invalid_scope_from_problem_json(self):
        body = (
            '{"type":"https://api.inference.sh/errors/invalid_scope",'
            '"status":400,"detail":"unknown scope: foo:bar"}'
        )
        err = APIError(400, "unknown scope", response_body=body)
        assert err.code == ErrorCode.INVALID_SCOPE

    def test_api_error_reads_code_confirmation_required_from_problem_json(self):
        body = (
            '{"type":"https://api.inference.sh/errors/code_confirmation_required",'
            '"status":400,"detail":"enter the code shown on your device"}'
        )
        err = APIError(400, "confirmation required", response_body=body)
        assert err.code == ErrorCode.CODE_CONFIRMATION_REQUIRED
