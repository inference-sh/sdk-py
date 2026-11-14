"""Second factor, agent wait statuses, and content scope (models v0.8.132 / 83f7a87).

Sign-in must expose ``otp_methods`` (not the retired ``otp_method`` string) so
clients offer TOTP, passkey, recovery, or email verification. Chat and tool rows
use a distinct ``waiting`` status when the agent paused on its own wait call —
not ``awaiting_input``, which means a person must act. Platform content editors
need ``content:write`` scoped like store pricing; removing the last enrolled
authenticator while 2FA stays on returns ``last_authenticator``.
"""

import json
from typing import get_type_hints

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


def test_auth_response_exposes_otp_methods_not_otp_method():
    hints = get_type_hints(AuthResponse)
    assert "otp_methods" in hints
    assert hints["otp_methods"].__origin__ is list
    assert hints["otp_methods"].__args__[0] is SecondFactor
    assert "otp_method" not in hints


def test_second_factor_wire_values():
    assert {m.value for m in SecondFactor} == {
        "totp",
        "passkey",
        "recovery",
        "email",
    }


def test_auth_response_otp_challenge_lists_methods():
    body: AuthResponse = {
        "otp_required": True,
        "challenge_token": "ch_abc",
        "otp_methods": [SecondFactor.TOTP, SecondFactor.PASSKEY],
    }
    wire = json.loads(json.dumps(body, default=lambda x: x.value))
    assert wire["otp_methods"] == ["totp", "passkey"]
    assert wire["challenge_token"] == "ch_abc"


def test_user_dto_exposes_two_factor_enabled():
    hints = get_type_hints(UserDTO)
    assert hints["two_factor_enabled"] is bool
    assert hints["totp_enabled"] is bool

    user: UserDTO = {
        "email": "dev@example.com",
        "totp_enabled": True,
        "two_factor_enabled": True,
    }
    assert user["two_factor_enabled"] is True


def test_waiting_status_is_distinct_from_awaiting_input():
    assert ChatStatus.WAITING.value == "waiting"
    assert ChatStatus.AWAITING_INPUT.value == "awaiting_input"
    assert ToolInvocationStatus.WAITING.value == "waiting"
    assert ToolInvocationStatus.AWAITING_INPUT.value == "awaiting_input"
    assert ChatStatus.WAITING.value != ChatStatus.AWAITING_INPUT.value


def test_content_write_scope_and_group():
    assert Scope.CONTENT_WRITE.value == "content:write"
    assert ScopeGroup.CONTENT.value == "content"
    assert Scope.CONTENT_WRITE.value.startswith("content:")


def test_last_authenticator_error_code():
    assert ErrorCode.LAST_AUTHENTICATOR.value == "last_authenticator"
