"""Forms, entitlement requests, and MCP Apps A2UI (336291f typegen).

Covers the API shapes clients use to submit forms, queue entitlement requests
(with optional form submissions), render MCP App tool pages in chat, and handle
new 409 conflict codes without confusing them with billing entitlement errors.
"""

from typing import Any, Dict, List, get_type_hints

from inferencesh.types import (
    A2UIComponent,
    A2UIComponentType,
    A2UIMcpToolResult,
    AppUIRef,
    AppVersionDTO,
    CreateEntitlementRequestRequest,
    DecideEntitlementRequestRequest,
    EntitlementErrorMeta,
    EntitlementRequestDTO,
    EntitlementRequestState,
    EntitlementResource,
    ErrorCode,
    FormDTO,
    FormStatus,
    FormSubmissionDTO,
    FormSubmitPolicy,
    MCPUICSP,
    NotificationType,
    ResourceContent,
    SubmitFormRequest,
    SubmitFormResponse,
)


def test_form_status_and_submit_policy_wire_values():
    assert {s.value for s in FormStatus} == {"draft", "open", "closed"}
    assert {p.value for p in FormSubmitPolicy} == {
        "once_per_user",
        "once_per_team",
        "many",
    }


def test_form_dto_and_submission_carry_policy_fields():
    form_hints = get_type_hints(FormDTO)
    assert form_hints["status"] is FormStatus
    assert form_hints["submit_policy"] is FormSubmitPolicy
    assert form_hints["schema"] is Any

    submission_hints = get_type_hints(FormSubmissionDTO)
    assert submission_hints["form_id"] is str
    assert submission_hints["data"] is Any


def test_submit_form_request_and_response_shapes():
    req_hints = get_type_hints(SubmitFormRequest)
    assert req_hints["data"] is Any
    assert req_hints["source"] is str

    resp_hints = get_type_hints(SubmitFormResponse)
    assert resp_hints["submission"] is FormSubmissionDTO


def test_entitlement_request_dto_links_form_submission():
    hints = get_type_hints(EntitlementRequestDTO)
    assert hints["resource"] is EntitlementResource
    assert hints["state"] is EntitlementRequestState
    assert hints["submission"] == FormSubmissionDTO | None
    assert hints["submission_id"] is str

    create_hints = get_type_hints(CreateEntitlementRequestRequest)
    assert create_hints["resource"] is EntitlementResource
    assert create_hints["form"] is str
    assert create_hints["data"] is Any

    assert get_type_hints(DecideEntitlementRequestRequest)["note"] is str


def test_entitlement_error_meta_exposes_request_flow_fields():
    hints = get_type_hints(EntitlementErrorMeta)
    assert hints["requestable"] is bool
    assert hints["request_state"] is str


def test_form_and_entitlement_conflict_codes_are_distinct():
    assert ErrorCode.FORM_CLOSED.value == "form_closed"
    assert ErrorCode.ALREADY_SUBMITTED.value == "already_submitted"
    assert ErrorCode.ALREADY_ENTITLED.value == "already_entitled"
    assert ErrorCode.REQUEST_OPEN.value == "request_open"
    billing = {
        ErrorCode.LIMIT_EXCEEDED.value,
        ErrorCode.FEATURE_NOT_AVAILABLE.value,
        ErrorCode.ENTITLEMENT_UNAVAILABLE.value,
    }
    conflicts = {
        ErrorCode.FORM_CLOSED.value,
        ErrorCode.ALREADY_SUBMITTED.value,
        ErrorCode.ALREADY_ENTITLED.value,
        ErrorCode.REQUEST_OPEN.value,
    }
    assert billing.isdisjoint(conflicts)


def test_entitlement_request_state_and_notification_type():
    assert {s.value for s in EntitlementRequestState} == {
        "open",
        "accepted",
        "declined",
        "withdrawn",
    }
    assert NotificationType.ENTITLEMENT_REQUEST.value == "entitlement_request"
    assert EntitlementResource.RESOURCE_FEATURE_FORMS.value == "feature:forms"


def test_app_version_ui_ref_mirrors_metadata_ui():
    hints = get_type_hints(AppVersionDTO)
    assert hints["ui"] == AppUIRef | None


def test_a2ui_mcp_app_component_carries_host_routing_fields():
    assert A2UIComponentType.A2UI_MCP_APP.value == "McpApp"

    hints = get_type_hints(A2UIComponent)
    for field in (
        "mcpHtml",
        "mcpResourceUri",
        "mcpServerSlug",
        "mcpCredentialId",
        "mcpToolName",
        "mcpArtifactId",
    ):
        assert hints[field] is str, field
    assert hints["mcpPrefersBorder"] is bool
    assert hints["mcpToolInput"] == Dict[str, Any]
    assert hints["mcpCsp"] == MCPUICSP | None
    assert hints["mcpToolResult"] == A2UIMcpToolResult | None

    assert get_type_hints(MCPUICSP)["connectDomains"] == List[str]
    result_hints = get_type_hints(A2UIMcpToolResult)
    assert result_hints["isError"] is bool
    assert result_hints["_meta"] == Dict[str, Any]


def test_resource_content_accepts_meta_for_mcp_pages():
    hints = get_type_hints(ResourceContent)
    assert hints["_meta"] == Dict[str, Any]
