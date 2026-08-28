"""Delta accumulator for streaming LLM token deltas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from .llm_types_gen import LLMDelta, LLMOutput, ToolCallDelta


@dataclass
class DeltaAccumulator:
    """Accumulates streaming LLMDelta events into a complete LLMOutput.

    Each call to ``apply()`` merges one delta using append semantics:
    - ``response`` / ``reasoning``: string concatenation.
    - ``tool_calls``: index-keyed; ``arguments`` fragments concatenate.
    """

    response: str = ""
    reasoning: str = ""
    _tool_calls: Dict[int, dict] = field(default_factory=dict)

    def apply(self, delta: LLMDelta) -> None:
        """Merge a single delta into accumulated state."""
        self.response += delta.response or ""
        if delta.reasoning:
            self.reasoning += delta.reasoning
        if delta.tool_calls:
            for tc in delta.tool_calls:
                existing = self._tool_calls.get(tc.index, {"arguments": ""})
                if tc.id:
                    existing["id"] = tc.id
                if tc.type:
                    existing["type"] = tc.type
                if tc.function and tc.function.name:
                    existing["name"] = tc.function.name
                if tc.function and tc.function.arguments:
                    existing["arguments"] += tc.function.arguments
                self._tool_calls[tc.index] = existing

    def to_output(self) -> LLMOutput:
        """Build a complete ``LLMOutput`` from accumulated state."""
        output = LLMOutput(response=self.response)
        if self.reasoning:
            output.reasoning = self.reasoning
        if self._tool_calls:
            output.tool_calls = [
                {
                    "id": tc.get("id", ""),
                    "type": tc.get("type", "function"),
                    "function": {
                        "name": tc.get("name", ""),
                        "arguments": tc.get("arguments", ""),
                    },
                }
                for _, tc in sorted(self._tool_calls.items())
            ]
        return output
