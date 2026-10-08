"""The decision contract: validation, the shared question form, and building the output."""

import pytest
from pydantic import ValidationError

from inferencesh.models import DecisionInput, DecisionOutput, DecisionVisionInput

CHOICE = {"id": "team", "instructions": "Which team?", "options": [{"name": "billing", "description": "Charges"}, {"name": "other"}]}
SCORE = {"id": "urgency", "instructions": "How urgent?", "levels": ["Can wait", "Today", "Now"]}
NOUL = {"id": "refund", "instructions": "Refund request?", "criteria": {"true": "Asks for money back"}}


def test_questions_use_the_shared_form():
    data = DecisionInput(state="charged twice", choices=[CHOICE], scores=[SCORE], nouls=[NOUL, {"id": "rude", "instructions": "Is it rude?"}])
    assert data.questions() == {
        "team": {"type": "choice", "instructions": "Which team?", "criteria": {"billing": "Charges", "other": None}},
        "urgency": {"type": "score", "instructions": "How urgent?", "criteria": ["Can wait", "Today", "Now"]},
        "refund": {"type": "noul", "instructions": "Refund request?", "criteria": {"true": "Asks for money back"}},
        "rude": {"type": "noul", "instructions": "Is it rude?"},
    }


def test_state_and_instructions_may_be_structured():
    data = DecisionInput(state={"messages": ["hi"]}, nouls=[{"id": "q", "instructions": {"question": "Greeting?"}}])
    assert data.questions()["q"]["instructions"] == {"question": "Greeting?"}


@pytest.mark.parametrize("state", [{}, [], {"records": []}])
def test_structured_state_counts_as_content(state):
    """Only the empty string is rejected; JSON state may be an empty container."""
    data = DecisionInput(state=state, nouls=[NOUL])
    assert data.has_content()
    assert "refund" in data.questions()


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"state": "x"}, "at least one question"),
        ({"state": "x", "choices": [CHOICE], "nouls": [{"id": "team", "instructions": "y"}]}, "repeated: \\['team'\\]"),
        ({"state": "x", "nouls": [{"id": "q", "instructions": ""}]}, "empty instructions"),
        ({"state": "x", "choices": [{"id": "c", "instructions": "y", "options": [{"name": "a"}, {"name": "a"}]}]}, "repeated option names"),
        ({"state": "", "nouls": [NOUL]}, "nothing to evaluate: send a `state` \\["),
    ],
)
def test_validation(kwargs, message):
    with pytest.raises(ValidationError, match=message):
        DecisionInput(**kwargs)


def test_limits():
    with pytest.raises(ValidationError):
        DecisionInput(state="x", choices=[{"id": "c", "instructions": "y", "options": [{"name": "only"}]}])
    with pytest.raises(ValidationError):
        DecisionInput(state="x", scores=[{"id": "s", "instructions": "y", "levels": [str(i) for i in range(11)]}])


def test_vision_input_accepts_images_alone(tmp_path):
    image = tmp_path / "a.png"
    image.write_bytes(b"\x89PNG")
    data = DecisionVisionInput(images=[str(image)], nouls=[NOUL])
    assert len(data.images) == 1
    with pytest.raises(ValidationError, match="send a `state`, `images`, or both"):
        DecisionVisionInput(nouls=[NOUL])
    assert "images" not in DecisionInput.model_fields


def test_from_answers_types_normalizes_and_meters():
    data = DecisionInput(state="x", choices=[CHOICE], scores=[SCORE], nouls=[NOUL])
    answers = {
        "team": {"choice": "billing", "confidence": 0.9, "probabilities": {"billing": 0.9, "other": 0.1}},
        "urgency": {"score": 1.5, "confidence": 0.5, "probabilities": {"0": 0.0, "1": 0.5, "2": 0.5}, "legend": {"0": "Can wait", "1": "Today", "2": "Now"}},
        "refund": {"noul": 0.97},
    }
    out = DecisionOutput.from_answers(answers, data, model="some/model", input_tokens=42)
    assert out.choices["team"].choice == "billing"
    assert out.scores["urgency"].normalized == 0.75
    assert out.nouls["refund"].noul == 0.97
    assert out.model == "some/model"
    assert out.input_tokens == 42
    assert out.output_meta.inputs[0].tokens == 42
    assert out.output_meta.outputs[0].tokens == 0


def test_from_answers_names_a_missing_answer():
    data = DecisionInput(state="x", nouls=[NOUL])
    with pytest.raises(RuntimeError, match="no answer for: \\['refund'\\]"):
        DecisionOutput.from_answers({}, data, model="m", input_tokens=0)


def test_from_answers_ignores_unasked_ids():
    data = DecisionInput(state="x", nouls=[NOUL])
    out = DecisionOutput.from_answers(
        {"refund": {"noul": 0.2}, "extra": {"noul": 0.99}},
        data,
        model="m",
        input_tokens=0,
    )
    assert set(out.nouls) == {"refund"}


def test_from_answers_sets_subclass_fields():
    class Output(DecisionOutput):
        state_truncated: bool = False

    data = DecisionInput(state="x", nouls=[NOUL])
    out = Output.from_answers({"refund": {"noul": 0.1}}, data, model="m", input_tokens=1, state_truncated=True)
    assert out.state_truncated is True
