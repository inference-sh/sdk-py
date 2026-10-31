"""Wire contracts from 143b0f5 typegen (beyond TaskStatus.REJECTED client tests).

Pins 412 requirements_not_met, interrupt resource typing, platform-app credential
catalog fields, and secret field validation patterns so regen cannot drop them.
"""

from typing import get_type_hints

from inferencesh.types import (
    CredentialConfigDTO,
    CredentialRequirement,
    CredentialScope,
    ErrorCode,
    InterruptDTO,
    InterruptResourceType,
    SecretField,
    SecretFieldConfig,
    SetupAction,
)


def test_error_code_requirements_not_met_wire_value():
    assert ErrorCode.REQUIREMENTS_NOT_MET.value == "requirements_not_met"


def test_interrupt_resource_type_wire_values():
    assert InterruptResourceType.INTERRUPT_RESOURCE_TURN.value == "turn"
    assert InterruptResourceType.INTERRUPT_RESOURCE_TOOL_INVOCATION.value == "tool_invocation"
    assert InterruptResourceType.INTERRUPT_RESOURCE_HOOK_EVENT.value == "hook_event"


def test_interrupt_dto_declares_resource_type():
    hints = get_type_hints(InterruptDTO)
    assert hints["resource_type"] is InterruptResourceType


def test_credential_requirement_platform_api_key_catalog_fields():
    hints = get_type_hints(CredentialRequirement)
    for field in (
        "display_name",
        "connection_scope",
        "instructions",
        "docs_url",
        "expires_after_days",
    ):
        assert field in hints

    req: CredentialRequirement = {
        "slug": "claude-code",
        "display_name": "Claude Code",
        "connection_scope": CredentialScope.USER,
        "instructions": "Create an API key in the Claude console.",
        "docs_url": "https://docs.example/claude-code",
        "expires_after_days": 90,
    }
    assert req["connection_scope"] is CredentialScope.USER
    assert req["expires_after_days"] == 90


def test_credential_config_dto_instructions_and_expiry():
    hints = get_type_hints(CredentialConfigDTO)
    assert hints["instructions"] is str
    assert hints["expires_after_days"] is int

    cfg: CredentialConfigDTO = {
        "slug": "acme-api",
        "instructions": "Paste your **Acme** API key.",
        "expires_after_days": 0,
    }
    assert cfg["expires_after_days"] == 0


def test_secret_field_and_config_pattern():
    assert "pattern" in get_type_hints(SecretField)
    assert "pattern" in get_type_hints(SecretFieldConfig)

    field: SecretField = {
        "key": "api_key",
        "pattern": r"^sk-ant-oat01-",
    }
    ui_field: SecretFieldConfig = {
        "key": "api_key",
        "pattern": r"^sk-ant-oat01-",
    }
    assert field["pattern"].startswith("^sk-ant")


def test_setup_action_typed_dict_includes_instructions():
    assert "instructions" in get_type_hints(SetupAction)
    action: SetupAction = {
        "type": "add_secret",
        "provider": "acme",
        "instructions": "Find the key under Settings → API.",
    }
    assert "API" in action["instructions"]
