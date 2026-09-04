"""Guard: app-layer LLM types derive from the generated Go contract.

The contract (llm_types_gen.py) is generated from go/api shared types.
App-layer classes in models/llm.py must inherit from it and override only
the documented app/wire boundary fields. This test failed to exist when a
batch merge of bot PRs (cc0d2be) silently replaced the inheritance with
hand-copied field lists; it is here so that cannot happen again.
"""

from typing import get_type_hints

from inferencesh import llm_types_gen as contract
from inferencesh.models import llm


# Fields whose app-layer type/default legitimately differs from the wire
# contract. Adding an override means adding it here, deliberately.
LLM_INPUT_OVERRIDES = {
    # File objects instead of wire strings / refs
    "context", "images", "files", "attachments",
    # Dict for backward compat with build_openai_messages / build_tools
    "tools",
    # App defaults and validation Go cannot express
    "system_prompt", "text", "role", "temperature", "top_p",
    "context_size", "max_tokens", "stop", "reasoning_effort",
}

CONTEXT_MESSAGE_OVERRIDES = {"images", "files", "tool_calls"}

LLM_OUTPUT_OVERRIDES = {"tool_calls"}


def _overridden_fields(app_cls, base_cls) -> set:
    app_hints = get_type_hints(app_cls)
    base_hints = get_type_hints(base_cls)
    overridden = set()
    for name in base_cls.model_fields:
        if app_hints.get(name) != base_hints.get(name):
            overridden.add(name)
        elif app_cls.model_fields[name].default != base_cls.model_fields[name].default:
            overridden.add(name)
    return overridden


class TestInheritsGeneratedContract:
    def test_llm_input(self):
        assert issubclass(llm.LLMInput, contract.LLMInput)

    def test_context_message(self):
        assert issubclass(llm.ContextMessage, contract.LLMContextMessage)

    def test_llm_output(self):
        assert issubclass(llm.BaseLLMOutput, contract.LLMOutput)
        assert issubclass(llm.LLMOutput, contract.LLMOutput)

    def test_usage_and_role_are_the_generated_types(self):
        assert llm.LLMUsage is contract.LLMUsage
        assert llm.ContextMessageRole is contract.ChatMessageRole


class TestGeneratedFieldsFlowThrough:
    """A new field on the Go struct must appear on the app class untouched."""

    def test_llm_input_has_every_contract_field(self):
        assert set(contract.LLMInput.model_fields) <= set(llm.LLMInput.model_fields)

    def test_context_message_has_every_contract_field(self):
        assert set(contract.LLMContextMessage.model_fields) <= set(llm.ContextMessage.model_fields)

    def test_llm_output_has_every_contract_field(self):
        assert set(contract.LLMOutput.model_fields) <= set(llm.BaseLLMOutput.model_fields)


class TestOverridesAreDocumented:
    def test_llm_input_overrides(self):
        assert _overridden_fields(llm.LLMInput, contract.LLMInput) == LLM_INPUT_OVERRIDES

    def test_context_message_overrides(self):
        assert _overridden_fields(llm.ContextMessage, contract.LLMContextMessage) == CONTEXT_MESSAGE_OVERRIDES

    def test_llm_output_overrides(self):
        assert _overridden_fields(llm.BaseLLMOutput, contract.LLMOutput) == LLM_OUTPUT_OVERRIDES
