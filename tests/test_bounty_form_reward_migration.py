"""Bounty claims vs form submissions after reward fields moved (ccfddaf typegen).

Form submissions record answers only; credit rewards flow through POST /me/bounty.
Guards clients from reading removed reward fields on forms and from confusing
409 already_claimed with form already_submitted conflicts.
"""

from typing import Any, get_type_hints

from inferencesh.types import (
    BountyProgramDTO,
    ErrorCode,
    FormDTO,
    FormStatus,
    FormSubmissionDTO,
    FormSubmitPolicy,
    SubmitFormResponse,
    SubmitSurveyResponse,
    UpdateFormRequest,
)


def test_form_dtos_no_longer_carry_bounty_or_inline_rewards():
    form_hints = get_type_hints(FormDTO)
    assert "bounty_name" not in form_hints
    assert form_hints["status"] is FormStatus
    assert form_hints["submit_policy"] is FormSubmitPolicy

    submission_hints = get_type_hints(FormSubmissionDTO)
    assert "reward_amount" not in submission_hints
    assert "reward_blocked_reason" not in submission_hints
    assert submission_hints["data"] is Any

    update_hints = get_type_hints(UpdateFormRequest)
    assert "bounty_name" not in update_hints
    assert update_hints["status"] == FormStatus | None


def test_submit_form_response_returns_submission_only():
    hints = get_type_hints(SubmitFormResponse)
    assert set(hints) == {"submission"}
    assert hints["submission"] is FormSubmissionDTO


def test_survey_response_keeps_cli_reward_fields_as_compat_stubs():
    """Surveys still expose granted_amount for older CLIs; bounties use /me/bounty."""
    hints = get_type_hints(SubmitSurveyResponse)
    assert hints["granted_amount"] is int
    assert hints["reward_blocked_reason"] is str


def test_bounty_program_form_proof_type_names_proof_form():
    hints = get_type_hints(BountyProgramDTO)
    assert hints["proof_form"] is str
    assert hints["proof_type"] is str


def test_bounty_already_claimed_is_distinct_from_form_conflicts():
    assert ErrorCode.ALREADY_CLAIMED.value == "already_claimed"
    assert ErrorCode.ALREADY_SUBMITTED.value == "already_submitted"
    assert ErrorCode.FORM_CLOSED.value == "form_closed"

    form_conflicts = {
        ErrorCode.FORM_CLOSED.value,
        ErrorCode.ALREADY_SUBMITTED.value,
    }
    bounty_conflicts = {ErrorCode.ALREADY_CLAIMED.value}
    assert form_conflicts.isdisjoint(bounty_conflicts)
