"""Notification preference refusal wire contract (5f6d025).

Broadcast and job flows that deliver notifications return 409 with
``ErrorCode.notifications_disabled`` when the recipient turned that channel off.
Clients must not treat it like a retriable delivery failure or a form conflict.
"""

from inferencesh.models.errors import APIError
from inferencesh.types import ErrorCode


class TestNotificationsDisabledErrorCode:
    def test_notifications_disabled_wire_value(self):
        assert ErrorCode.NOTIFICATIONS_DISABLED.value == "notifications_disabled"

    def test_notifications_disabled_distinct_from_form_and_entitlement_conflicts(self):
        form_and_entitlement = {
            ErrorCode.FORM_CLOSED.value,
            ErrorCode.ALREADY_SUBMITTED.value,
            ErrorCode.ALREADY_ENTITLED.value,
            ErrorCode.REQUEST_OPEN.value,
        }
        assert ErrorCode.NOTIFICATIONS_DISABLED.value not in form_and_entitlement

    def test_notifications_disabled_distinct_from_billing_entitlement_errors(self):
        billing = {
            ErrorCode.LIMIT_EXCEEDED.value,
            ErrorCode.FEATURE_NOT_AVAILABLE.value,
            ErrorCode.ENTITLEMENT_UNAVAILABLE.value,
        }
        assert ErrorCode.NOTIFICATIONS_DISABLED.value not in billing

    def test_api_error_reads_notifications_disabled_from_problem_json(self):
        body = (
            '{"type":"https://api.inference.sh/errors/notifications_disabled",'
            '"status":409,"detail":"This notification is disabled in your preferences"}'
        )
        err = APIError(409, "disabled", response_body=body)
        assert err.code == ErrorCode.NOTIFICATIONS_DISABLED
