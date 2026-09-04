"""OpenAI Chat Completions compatibility for chat apps.

    from inferencesh.openai import OpenAIChatMixin

    class App(OpenAIChatMixin, BaseApp):
        ...
"""

from .adapter import OpenAIChatMixin, UnsupportedParameterError, to_llm_input
from .types import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionInput,
    ChatCompletionMessage,
    ChatMessage,
    Choice,
    ChoiceDelta,
    ChoiceDeltaFunctionCall,
    ChoiceDeltaToolCall,
    ChunkChoice,
    CompletionUsage,
    ToolDefinition,
)

__all__ = [
    "OpenAIChatMixin",
    "UnsupportedParameterError",
    "to_llm_input",
    "ChatCompletion",
    "ChatCompletionChunk",
    "ChatCompletionInput",
    "ChatCompletionMessage",
    "ChatMessage",
    "Choice",
    "ChoiceDelta",
    "ChoiceDeltaFunctionCall",
    "ChoiceDeltaToolCall",
    "ChunkChoice",
    "CompletionUsage",
    "ToolDefinition",
]
