"""Bounty claims vs form submissions after reward fields moved (ccfddaf typegen).

Form submissions record answers only; credit rewards flow through POST /me/bounty.
Guards clients from reading removed reward fields on forms and from confusing
409 already_claimed with form already_submitted conflicts.
"""

from typing import Any, get_type_hints

from inferencesh.types import (
    BountyProgramDTO,
    BountySubmissionDTO,
    ErrorCode,
    FormDTO,
    FormStatus,
    FormSubmissionDTO,
    FormSubmitPolicy,
    SubmitBountyRequest,
    SubmitBountyResponse,
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

    response: SubmitFormResponse = {
        "submission": {
            "form_id": "form_1",
            "data": {"company": "Acme"},
            "source": "web",
            "agent": "acme/assistant@latest",
            "context": "onboarding",
        },
    }
    assert response["submission"]["data"] == {"company": "Acme"}


def test_survey_response_keeps_cli_reward_fields_as_compat_stubs():
    """Surveys still expose granted_amount for older CLIs; bounties use /me/bounty."""
    hints = get_type_hints(SubmitSurveyResponse)
    assert hints["granted_amount"] is int
    assert hints["reward_blocked_reason"] is str

    survey: SubmitSurveyResponse = {
        "response": {
            "question_id": "q_nps",
            "response": "9",
            "agent": "",
            "source": "cli",
            "context": "",
        },
        "granted_amount": 0,
        "reward_blocked_reason": "",
    }
    assert survey["granted_amount"] == 0
    assert survey["reward_blocked_reason"] == ""


def test_bounty_program_form_proof_type_names_proof_form():
    hints = get_type_hints(BountyProgramDTO)
    assert hints["proof_form"] is str
    assert hints["proof_type"] is str

    url_program: BountyProgramDTO = {
        "name": "share-on-social",
        "proof_type": "url",
        "proof_form": "",
        "requires_payment_method": False,
        "amount_microcents": 1_000_000,
    }
    form_program: BountyProgramDTO = {
        "name": "marketplace-launch",
        "proof_type": "form",
        "proof_form": "acme/marketplace-intake",
        "requires_payment_method": True,
        "amount_microcents": 5_000_000,
        "max_per_user": 1,
    }
    assert url_program["proof_form"] == ""
    assert form_program["proof_form"] == "acme/marketplace-intake"


def test_submit_bounty_proof_id_matches_program_proof_type():
    program_app: BountyProgramDTO = {
        "name": "publish-app",
        "proof_type": "app",
        "proof_form": "",
    }
    program_form: BountyProgramDTO = {
        "name": "marketplace-launch",
        "proof_type": "form",
        "proof_form": "acme/marketplace-intake",
    }
    program_text: BountyProgramDTO = {
        "name": "tweet-promo",
        "proof_type": "url",
        "proof_form": "",
    }

    app_claim: SubmitBountyRequest = {
        "bounty_id": "bounty_app",
        "proof_id": "acme/demo-app",
        "agent": "acme/assistant@latest",
        "source": "web",
    }
    form_claim: SubmitBountyRequest = {
        "bounty_id": "bounty_form",
        "proof_id": "sub_42",
        "agent": "acme/assistant@latest",
        "source": "web",
    }
    text_claim: SubmitBountyRequest = {
        "bounty_id": "bounty_url",
        "proof_id": "https://example.com/post/123",
        "source": "web",
    }

    assert program_app["proof_type"] == "app"
    assert "/" in app_claim["proof_id"]
    assert program_form["proof_form"].endswith("marketplace-intake")
    assert form_claim["proof_id"].startswith("sub_")
    assert program_text["proof_type"] == "url"
    assert text_claim["proof_id"].startswith("https://")

    response: SubmitBountyResponse = {
        "submission": {
            "bounty_id": form_claim["bounty_id"],
            "proof_id": form_claim["proof_id"],
            "proof_ref": "proof_ref_1",
            "agent": form_claim["agent"],
            "source": form_claim["source"],
        },
        "granted_amount": program_form.get("amount_microcents", 0),
    }
    submission_hints = get_type_hints(BountySubmissionDTO)
    assert submission_hints["proof_ref"] is str
    assert response["submission"]["proof_id"] == "sub_42"


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
