"""Team variables, sandbox infra, and agent run infra (v0.41.0 / 1bc8579 typegen).

Pins wire shapes clients use for team env vars (INF-1345), infra placement on
agent runs/chats/sandboxes, and setup/requirements flows for missing variables.
"""

from typing import get_type_hints

from inferencesh.types import (
    ApiAgentRunRequest,
    AppVersionDTO,
    AppVersionInput,
    ChatData,
    ChatSettingsRequest,
    CreateSandboxRequest,
    EngineCapability,
    Infra,
    RequirementError,
    RequirementType,
    SandboxDTO,
    SetupActionType,
    VarRequirement,
    VariableDTO,
    VariableListResponse,
    VariableSetRequest,
)


def test_var_requirement_declares_key_default_and_optional():
    hints = get_type_hints(VarRequirement)
    assert set(hints) >= {"key", "description", "optional", "default"}

    entry: VarRequirement = {
        "key": "LOG_LEVEL",
        "description": "verbosity for worker logs",
        "optional": True,
        "default": "info",
    }
    assert entry["default"] == "info"


def test_variable_dto_and_set_request_shapes():
    dto_hints = get_type_hints(VariableDTO)
    assert set(dto_hints) >= {"id", "team_id", "key", "value", "description"}
    assert dto_hints["value"] is str

    set_hints = get_type_hints(VariableSetRequest)
    assert set_hints["value"] is str
    assert set_hints["description"] == str | None

    row: VariableDTO = {
        "team_id": "team_1",
        "key": "REGION",
        "value": "us-west-2",
    }
    req: VariableSetRequest = {"value": "eu-west-1", "description": "Primary region"}
    assert req["value"] == "eu-west-1"


def test_variable_list_response_pagination_fields():
    hints = get_type_hints(VariableListResponse)
    assert "items" in hints
    assert "has_next" in hints
    assert hints["has_next"] is bool

    page: VariableListResponse = {
        "items": [{"key": "A", "value": "1"}],
        "has_next": False,
        "items_per_page": 50,
    }
    assert page["items"][0]["key"] == "A"


def test_app_version_carries_required_vars():
    for cls in (AppVersionInput, AppVersionDTO):
        hints = get_type_hints(cls)
        assert "required_vars" in hints

    version: AppVersionDTO = {
        "id": "ver_1",
        "required_vars": [{"key": "API_BASE", "optional": False}],
    }
    assert version["required_vars"][0]["key"] == "API_BASE"


def test_requirement_and_setup_enums_for_missing_variables():
    assert RequirementType.VARIABLE.value == "variable"
    assert SetupActionType.SETUP_ACTION_ADD_VARIABLE.value == "add_variable"

    err: RequirementError = {
        "type": RequirementType.VARIABLE,
        "key": "API_BASE",
        "message": "team has not set API_BASE",
        "action": {"type": SetupActionType.SETUP_ACTION_ADD_VARIABLE},
    }
    assert err["type"] is RequirementType.VARIABLE
    assert err["action"]["type"] is SetupActionType.SETUP_ACTION_ADD_VARIABLE


def test_engine_capability_task_env_documents_per_task_app_env():
    assert EngineCapability.TASK_ENV.value == "task_env"
    assert "task_env" in {c.value for c in EngineCapability}


def test_infra_enum_wire_values():
    assert Infra.CLOUD.value == "cloud"
    assert Infra.PRIVATE.value == "private"
    assert Infra.PRIVATE_FIRST.value == "private_first"


def test_agent_run_chat_and_sandbox_requests_carry_infra():
    hints = get_type_hints(ApiAgentRunRequest)
    assert hints["infra"] is Infra

    run: ApiAgentRunRequest = {
        "input": {"text": "hello"},
        "infra": Infra.PRIVATE_FIRST,
    }
    assert run["infra"] is Infra.PRIVATE_FIRST

    settings: ChatSettingsRequest = {"infra": Infra.PRIVATE}
    assert get_type_hints(ChatSettingsRequest)["infra"] == Infra | None
    assert settings["infra"] is Infra.PRIVATE

    sandbox_req: CreateSandboxRequest = {"infra": Infra.CLOUD}
    assert get_type_hints(CreateSandboxRequest)["infra"] is Infra
    assert sandbox_req["infra"] is Infra.CLOUD


def test_chat_data_and_sandbox_dto_expose_infra():
    chat: ChatData = {"id": "chat_1", "infra": Infra.CLOUD}
    assert get_type_hints(ChatData)["infra"] is Infra
    assert chat["infra"] is Infra.CLOUD

    sandbox: SandboxDTO = {"id": "sbx_1", "infra": Infra.PRIVATE}
    assert get_type_hints(SandboxDTO)["infra"] is Infra
    assert sandbox["infra"] is Infra.PRIVATE