"""Two-factor auth, agent wait statuses, and content scope (83f7a87 / models v0.8.132).

``AuthResponse.otp_method`` is replaced by ``otp_methods`` (``SecondFactor`` list).
``UserDTO`` adds ``two_factor_enabled`` while keeping deprecated ``totp_enabled``.
Chat and tool runs expose a distinct ``waiting`` status separate from
``awaiting_input``. Platform content editing uses ``Scope.CONTENT_WRITE``.
"""

import json
from typing import List, get_type_hints

import pytest

from inferencesh.models.errors import APIError
from inferencesh.types import (
    AuthResponse,
    ChatStatus,
    ErrorCode,
    Scope,
    ScopeGroup,
    SecondFactor,
    ToolInvocationStatus,
    UserDTO,
)


class TestSecondFactorWireValues:
    def test_second_factor_methods_match_otp_verify_contract(self):
        assert SecondFactor.TOTP.value == "totp"
        assert SecondFactor.PASSKEY.value == "passkey"
        assert SecondFactor.RECOVERY.value == "recovery"
        assert SecondFactor.EMAIL.value == "email"


class TestAuthResponseOtpMethods:
    def test_auth_response_lists_otp_methods_not_legacy_otp_method(self):
        hints = get_type_hints(AuthResponse)
        assert "otp_methods" in hints
        assert hints["otp_methods"] == List[SecondFactor]
        assert "otp_method" not in hints

    def test_auth_response_otp_methods_round_trip_wire_json(self):
        resp: AuthResponse = {
            "otp_required": True,
            "otp_methods": [SecondFactor.TOTP, SecondFactor.PASSKEY],
            "challenge_token": "ch_1",
        }
        wire = json.loads(
            json.dumps(resp, default=lambda o: o.value if hasattr(o, "value") else o)
        )
        assert wire["otp_methods"] == ["totp", "passkey"]
        assert "otp_method" not in wire


class TestUserDTOTwoFactorFields:
    def test_user_dto_exposes_two_factor_and_legacy_totp_enabled(self):
        hints = get_type_hints(UserDTO)
        assert hints["two_factor_enabled"] is bool
        assert hints["totp_enabled"] is bool

    def test_user_dto_accepts_both_two_factor_flags(self):
        user: UserDTO = {
            "id": "u1",
            "email": "a@example.com",
            "two_factor_enabled": True,
            "totp_enabled": True,
        }
        assert user["two_factor_enabled"] is True
        assert user["totp_enabled"] is True


class TestWaitingRunStatuses:
    @pytest.mark.parametrize(
        "status_enum,value",
        [
            (ChatStatus.WAITING, "waiting"),
            (ToolInvocationStatus.WAITING, "waiting"),
        ],
    )
    def test_waiting_status_wire_value(self, status_enum, value):
        assert status_enum.value == value

    def test_waiting_is_distinct_from_awaiting_input(self):
        assert ChatStatus.WAITING.value != ChatStatus.AWAITING_INPUT.value
        assert ToolInvocationStatus.WAITING.value != ToolInvocationStatus.AWAITING_INPUT.value
        assert ChatStatus.WAITING.value != ToolInvocationStatus.AWAITING_APPROVAL.value


class TestContentScope:
    def test_content_write_scope_and_group(self):
        assert Scope.CONTENT_WRITE.value == "content:write"
        assert ScopeGroup.CONTENT.value == "content"


class TestLastAuthenticatorErrorCode:
    def test_last_authenticator_wire_value(self):
        assert ErrorCode.LAST_AUTHENTICATOR.value == "last_authenticator"

    def test_api_error_reads_last_authenticator_from_problem_json(self):
        body = (
            '{"type":"https://api.inference.sh/errors/last_authenticator",'
            '"status":409,"detail":"enroll another method or disable 2FA first"}'
        )
        err = APIError(409, "last authenticator", response_body=body)
        assert err.code == ErrorCode.LAST_AUTHENTICATOR
