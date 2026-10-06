"""Forms, entitlement requests, and MCP Apps A2UI (336291f typegen).

Covers the API shapes clients use to submit forms, queue entitlement requests
(with optional form submissions), render MCP App tool pages in chat, and handle
new 409 conflict codes without confusing them with billing entitlement errors.
"""

from typing import Any, Dict, get_type_hints

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
    EntitlementRequested,
    EntitlementType,
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


def test_form_dto_and_submission_carry_policy_and_reward_fields():
    form_hints = get_type_hints(FormDTO)
    assert form_hints["status"] is FormStatus
    assert form_hints["submit_policy"] is FormSubmitPolicy
    assert form_hints["schema"] is Any

    submission_hints = get_type_hints(FormSubmissionDTO)
    assert submission_hints["reward_amount"] is int
    assert submission_hints["reward_blocked_reason"] is str

    form: FormDTO = {
        "namespace": "acme",
        "name": "marketplace-intake",
        "title": "Marketplace intake",
        "status": FormStatus.OPEN,
        "submit_policy": FormSubmitPolicy.FORM_SUBMIT_ONCE_PER_TEAM,
        "schema": {"type": "object", "properties": {"company": {"type": "string"}}},
    }
    assert form["submit_policy"] is FormSubmitPolicy.FORM_SUBMIT_ONCE_PER_TEAM


def test_submit_form_request_and_response_shapes():
    req_hints = get_type_hints(SubmitFormRequest)
    assert req_hints["data"] is Any
    assert req_hints["source"] is str

    resp_hints = get_type_hints(SubmitFormResponse)
    assert resp_hints["submission"] is FormSubmissionDTO
    assert resp_hints["granted_amount"] is int
    assert resp_hints["reward_blocked_reason"] is str

    payload: SubmitFormRequest = {
        "data": {"company": "Acme"},
        "source": "web",
        "agent": "acme/assistant@latest",
        "context": "onboarding",
    }
    response: SubmitFormResponse = {
        "submission": {
            "form_id": "form_1",
            "data": payload["data"],
            "reward_amount": 0,
            "reward_blocked_reason": "",
        },
        "granted_amount": 1_000_000,
        "reward_blocked_reason": "",
    }
    assert response["submission"]["data"] == {"company": "Acme"}
    assert response["granted_amount"] == 1_000_000


def test_entitlement_request_dto_links_form_submission():
    hints = get_type_hints(EntitlementRequestDTO)
    assert hints["resource"] is EntitlementResource
    assert hints["state"] is EntitlementRequestState
    assert hints["submission"] == FormSubmissionDTO | None

    requested: EntitlementRequested = {
        "type": EntitlementType.BOOLEAN,
        "enabled": True,
    }
    create: CreateEntitlementRequestRequest = {
        "resource": EntitlementResource.RESOURCE_FEATURE_FORMS,
        "requested": requested,
        "form": "acme/marketplace-intake",
        "data": {"company": "Acme"},
    }
    queue_item: EntitlementRequestDTO = {
        "resource": EntitlementResource.RESOURCE_FEATURE_FORMS,
        "resource_label": "Forms",
        "requested": requested,
        "submission_id": "sub_1",
        "submission": {
            "form_id": "form_1",
            "data": create["data"],
            "reward_amount": 0,
        },
        "state": EntitlementRequestState.ENTITLEMENT_REQUEST_OPEN,
        "note": "",
    }
    assert create["form"] == "acme/marketplace-intake"
    assert queue_item["submission"]["data"] == {"company": "Acme"}
    assert queue_item["state"] is EntitlementRequestState.ENTITLEMENT_REQUEST_OPEN

    decide: DecideEntitlementRequestRequest = {"note": "Approved for pilot"}
    assert decide["note"] == "Approved for pilot"


def test_entitlement_error_meta_exposes_request_flow_fields():
    hints = get_type_hints(EntitlementErrorMeta)
    assert hints["requestable"] is bool
    assert hints["request_state"] is str

    meta: EntitlementErrorMeta = {
        "resource": EntitlementResource.RESOURCE_FEATURE_FORMS,
        "resource_label": "Forms",
        "upgrade_available": False,
        "requestable": True,
        "request_state": "open",
    }
    assert meta["requestable"] is True
    assert meta["request_state"] == "open"


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

    ui: AppUIRef = {"artifact": "acme/dialogue-ui@3"}
    version: AppVersionDTO = {
        "metadata": {"ui": ui},
        "ui": ui,
        "default_function": "chat",
        "functions": {},
    }
    assert version["ui"]["artifact"] == version["metadata"]["ui"]["artifact"]


def test_a2ui_mcp_app_component_carries_host_routing_fields():
    assert A2UIComponentType.A2UI_MCP_APP.value == "McpApp"

    csp: MCPUICSP = {
        "connectDomains": ["https://api.example.com"],
        "resourceDomains": ["https://cdn.example.com"],
        "frameDomains": [],
        "baseUriDomains": ["https://app.example.com"],
    }
    tool_result: A2UIMcpToolResult = {
        "content": [{"type": "text", "text": "ok"}],
        "structuredContent": {"rows": []},
        "isError": False,
        "_meta": {"ui": {"csp": csp}},
    }
    component: A2UIComponent = {
        "component": A2UIComponentType.A2UI_MCP_APP,
        "mcpHtml": "<html></html>",
        "mcpCsp": csp,
        "mcpResourceUri": "ui://dashboard",
        "mcpServerSlug": "analytics",
        "mcpCredentialId": "cred_1",
        "mcpToolName": "show_dashboard",
        "mcpToolInput": {"range": "7d"},
        "mcpToolResult": tool_result,
        "mcpPrefersBorder": True,
        "mcpArtifactId": "",
    }
    assert component["component"] is A2UIComponentType.A2UI_MCP_APP
    assert component["mcpToolResult"]["content"][0]["text"] == "ok"
    assert component["mcpCsp"]["connectDomains"][0].startswith("https://")


def test_resource_content_accepts_meta_for_mcp_pages():
    hints = get_type_hints(ResourceContent)
    assert hints["_meta"] == Dict[str, Any]

    block: ResourceContent = {
        "uri": "ui://page",
        "mimeType": "text/html",
        "text": "<html></html>",
        "_meta": {"ui": {"csp": {"connectDomains": ["https://api.example.com"]}}},
    }
    assert block["_meta"]["ui"]["csp"]["connectDomains"] == ["https://api.example.com"]
