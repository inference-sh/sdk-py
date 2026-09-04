"""Guard: inferencesh.openai types track the OpenAI Chat Completions spec.

The reference is the installed ``openai`` package (its types are generated
from OpenAI's OpenAPI spec). Every request parameter OpenAI defines must be
declared on ChatCompletionInput — honoured, accepted-and-ignored, or
rejected — never silently absent. Response models must not invent fields
the spec does not have, except for documented extensions.
"""

import typing

import pytest

openai = pytest.importorskip("openai")

from openai.types import CompletionUsage as SpecUsage  # noqa: E402
from openai.types.chat import ChatCompletion as SpecCompletion  # noqa: E402
from openai.types.chat import ChatCompletionChunk as SpecChunk  # noqa: E402
from openai.types.chat import completion_create_params as spec_params  # noqa: E402
from openai.types.chat.chat_completion import Choice as SpecChoice  # noqa: E402
from openai.types.chat.chat_completion import ChatCompletionMessage as SpecMessage  # noqa: E402
from openai.types.chat.chat_completion_chunk import Choice as SpecChunkChoice  # noqa: E402
from openai.types.chat.chat_completion_chunk import ChoiceDelta as SpecChoiceDelta  # noqa: E402

from inferencesh.openai import types as ours  # noqa: E402

# Fields we add on top of the spec, on purpose. Anything else extra is drift.
RESPONSE_EXTENSIONS = {
    "reasoning",    # OpenRouter / DeepSeek reasoning extension
    "output_meta",  # inference.sh billing metadata (BaseAppOutput); stripped at the HTTP edge
}


def _spec_request_params() -> set:
    return set(typing.get_type_hints(spec_params.CompletionCreateParamsBase)) | set(
        typing.get_type_hints(spec_params.CompletionCreateParamsStreaming)
    )


def test_every_spec_request_param_is_declared():
    missing = _spec_request_params() - set(ours.ChatCompletionInput.model_fields)
    assert not missing, f"OpenAI request params not declared on ChatCompletionInput: {sorted(missing)}"


@pytest.mark.parametrize("ours_cls,spec_cls", [
    (ours.ChatCompletion, SpecCompletion),
    (ours.Choice, SpecChoice),
    (ours.ChatCompletionMessage, SpecMessage),
    (ours.ChatCompletionChunk, SpecChunk),
    (ours.ChunkChoice, SpecChunkChoice),
    (ours.ChoiceDelta, SpecChoiceDelta),
    (ours.CompletionUsage, SpecUsage),
])
def test_response_models_do_not_invent_fields(ours_cls, spec_cls):
    extra = set(ours_cls.model_fields) - set(spec_cls.model_fields) - RESPONSE_EXTENSIONS
    assert not extra, f"{ours_cls.__name__} has fields the spec does not: {sorted(extra)}"
