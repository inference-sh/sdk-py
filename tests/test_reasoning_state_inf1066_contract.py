"""ReasoningState on LLMOutput and LLMContextMessage (models INF-1066, v0.27.0).

Opaque per-provider reasoning carry-over must appear only on final output and
assistant context messages, not on streaming LLMDelta fragments.
"""

from typing import Any, Dict, get_type_hints

from inferencesh import llm_types_gen as wire
from inferencesh.models.llm import ContextMessage, LLMOutput
from inferencesh.types import LLMContextMessage, LLMOutput as LLMOutputTD


def _sample_reasoning_state() -> Dict[str, Any]:
    return {
        "anthropic": {"signature": "sig-abc", "type": "thinking"},
        "openai": {"encrypted": "blob"},
        "gemini": {"thought_signature": "gem-sig"},
    }


class TestReasoningStateWireContract:
    def test_llm_output_exposes_reasoning_state(self):
        fields = set(wire.LLMOutput.model_fields)
        assert "reasoning_state" in fields
        assert "reasoning" in fields

    def test_llm_context_message_exposes_reasoning_state(self):
        fields = set(wire.LLMContextMessage.model_fields)
        assert "reasoning_state" in fields

    def test_llm_delta_does_not_carry_reasoning_state(self):
        """State is whole only on the final output, not on streaming deltas."""
        fields = set(wire.LLMDelta.model_fields)
        assert "reasoning_state" not in fields

    def test_llm_output_json_round_trip_preserves_opaque_state(self):
        state = _sample_reasoning_state()
        original = wire.LLMOutput(
            response="done",
            reasoning="visible trace",
            reasoning_state=state,
        )
        restored = wire.LLMOutput.model_validate_json(original.model_dump_json())
        assert restored.reasoning_state == state

    def test_assistant_context_message_carries_reasoning_state(self):
        state = {"anthropic": {"signature": "only-mine"}}
        msg = wire.LLMContextMessage(
            role=wire.ChatMessageRole.ASSISTANT,
            text="answer",
            reasoning_state=state,
        )
        dumped = msg.model_dump(exclude_none=True)
        assert dumped["reasoning_state"] == state


class TestReasoningStateTypedDictParity:
    def test_types_typed_dict_includes_reasoning_state(self):
        out_hints = get_type_hints(LLMOutputTD)
        ctx_hints = get_type_hints(LLMContextMessage)
        assert out_hints["reasoning_state"] == DictType[str, Any]
        assert ctx_hints["reasoning_state"] == DictType[str, Any]


class TestReasoningStateAppLayer:
    def test_app_llm_output_inherits_reasoning_state_from_contract(self):
        state = _sample_reasoning_state()
        out = LLMOutput(response="ok", reasoning_state=state)
        assert out.reasoning_state == state

    def test_app_context_message_inherits_reasoning_state_from_contract(self):
        from inferencesh.models.llm import ContextMessageRole

        state = {"openai": {"encrypted": "x"}}
        msg = ContextMessage(
            role=ContextMessageRole.ASSISTANT,
            text="hi",
            reasoning_state=state,
        )
        assert msg.reasoning_state == state
