"""The decision contract for apps that wrap a decision model.

A decision model reads a state and answers typed questions about it with
probabilities, without generating text. Every decision app takes
``DecisionInput`` (or ``DecisionVisionInput`` when its model sees images) and
returns ``DecisionOutput``, so a caller can move between them by changing the
app name.

    from inferencesh.models.decision import DecisionVisionInput, DecisionOutput

    class AppInput(DecisionVisionInput):
        images: List[File] = Field(default_factory=list, max_length=4)

    async def run(self, input_data: AppInput) -> DecisionOutput:
        answers, tokens = self.model.answer(input_data.state, input_data.questions())
        return DecisionOutput.from_answers(answers, input_data, model=MODEL_ID, input_tokens=tokens)

The wire shape is generated from go/api (llm_types_gen.py); the classes here
add descriptions, limits and validation, and take images as File objects.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import Field, model_validator

from inferencesh import llm_types_gen as contract

from .base import BaseAppInput, BaseAppOutput
from .file import File
from .output_meta import OutputMeta, TextMeta

# Plain text, or JSON structure the model reads by key.
Structured = Union[str, Dict[str, Any], List[Any]]


# ── Questions ────────────────────────────────────────────────────────────────

class ChoiceOption(contract.DecisionChoiceOption):
    name: str = Field(min_length=1, description="Option name. Returned as `choice` and used as the key in `probabilities`. Sent to the model.")
    description: Optional[Structured] = Field(
        default=None,
        description="What this option covers. Omit when the name is clear on its own.",
    )


class ChoiceQuestion(contract.DecisionChoiceQuestion):
    """Which of these options? For a fixed set of unordered options."""
    id: str = Field(min_length=1, description="Your key for this question; the answer comes back under it. Not sent to the model.")
    instructions: Structured = Field(description="What the model should decide, written as a complete question.")
    options: List[ChoiceOption] = Field(
        min_length=2,
        max_length=255,
        description="The answer options (2 to 255). Give the full list, and add an `other` option when the list might not cover every input.",
    )


class ScoreQuestion(contract.DecisionScoreQuestion):
    """Which level? For a position on a spectrum you can describe."""
    id: str = Field(min_length=1, description="Your key for this question; the answer comes back under it. Not sent to the model.")
    instructions: Structured = Field(description="What the model should rate, written as a complete question.")
    levels: List[Structured] = Field(
        min_length=2,
        max_length=10,
        description="Ordered level descriptions, low end to high end (2 to 10). A level's number is its index, starting at 0.",
    )


class NoulCriteria(contract.DecisionNoulCriteria):
    true: Optional[Structured] = Field(default=None, description="What a yes (value near 1) means.")
    false: Optional[Structured] = Field(default=None, description="What a no (value near 0) means.")


class NoulQuestion(contract.DecisionNoulQuestion):
    """Is this true? For a clean yes/no where the probability itself is the signal."""
    id: str = Field(min_length=1, description="Your key for this question; the answer comes back under it. Not sent to the model.")
    instructions: Structured = Field(description="The yes/no question, or a statement to judge. Make the boundary between yes and no unambiguous.")
    criteria: Optional[NoulCriteria] = Field(default=None, description="Optional. Pins down a subtle yes/no boundary.")


class DecisionInput(contract.DecisionInput, BaseAppInput):
    """One state and the typed questions asked of it."""
    state: Structured = Field(
        default="",
        description="The text to evaluate: a string, or a JSON object / array of related context (messages, records, a policy). Every question sees the same state.",
    )
    choices: List[ChoiceQuestion] = Field(default_factory=list, description="Choice questions: pick one option from a set.")
    scores: List[ScoreQuestion] = Field(default_factory=list, description="Score questions: place the state on ordered levels.")
    nouls: List[NoulQuestion] = Field(default_factory=list, description="Noul questions: probability that the answer is yes.")

    def has_content(self) -> bool:
        """Whether there is anything to ask about. An input with another medium (audio, ...) extends this."""
        return self.state != ""

    @model_validator(mode="after")
    def _check_decision_input(self):
        questions = (*self.choices, *self.scores, *self.nouls)
        ids = [q.id for q in questions]
        if not ids:
            raise ValueError("ask at least one question in `choices`, `scores` or `nouls`")
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"question ids must be unique across choices, scores and nouls; repeated: {dupes}")
        for q in questions:
            if q.instructions == "":
                raise ValueError(f"question '{q.id}' has empty instructions")
        for q in self.choices:
            names = [o.name for o in q.options]
            if len(set(names)) != len(names):
                raise ValueError(f"choice '{q.id}' has repeated option names")
        if not self.has_content():
            raise ValueError("there is nothing to evaluate: send a `state`" + (", `images`, or both" if "images" in type(self).model_fields else ""))
        return self

    def questions(self) -> Dict[str, Dict[str, Any]]:
        """The questions keyed by id, in the form decision models share:
        ``{"type": "choice" | "score" | "noul", "instructions": ..., "criteria": ...}``.
        Criteria are ``{name: description}`` for a choice, the list of levels for a
        score, and ``{"true": ..., "false": ...}`` for a noul that gives any."""
        out: Dict[str, Dict[str, Any]] = {}
        for q in self.choices:
            out[q.id] = {
                "type": "choice",
                "instructions": q.instructions,
                "criteria": {o.name: o.description for o in q.options},
            }
        for q in self.scores:
            out[q.id] = {"type": "score", "instructions": q.instructions, "criteria": list(q.levels)}
        for q in self.nouls:
            question: Dict[str, Any] = {"type": "noul", "instructions": q.instructions}
            criteria = q.criteria.model_dump(exclude_none=True) if q.criteria is not None else {}
            if criteria:
                question["criteria"] = criteria
            out[q.id] = question
        return out


class DecisionVisionInput(DecisionInput, contract.DecisionVisionInput):
    """A state, images, and the typed questions asked of them."""
    images: List[File] = Field(
        default_factory=list,
        description="Images the questions are about. Every question sees them, placed before the state. The state may be empty when the images carry the content.",
    )

    def has_content(self) -> bool:
        return super().has_content() or bool(self.images)


# ── Answers ──────────────────────────────────────────────────────────────────

class ChoiceAnswer(contract.DecisionChoiceAnswer):
    choice: str = Field(description="The highest-probability option.")
    confidence: float = Field(description="0 to 1: how sure the model is of `choice`. Gate actions on it; thresholds scale with risk.")
    probabilities: Dict[str, float] = Field(description="Every option mapped to its probability.")


class ScoreAnswer(contract.DecisionScoreAnswer):
    score: float = Field(description="Probability-weighted position on the levels, 0 to the top level number. Can land between levels.")
    normalized: float = Field(description="`score` divided by the top level number: 0 to 1, comparable across scales of different length.")
    confidence: float = Field(description="0 to 1: how sure the model is of the most likely level.")
    probabilities: Dict[str, float] = Field(description="Each level number (as a string) mapped to its probability.")
    legend: Dict[str, Any] = Field(description="Each level number mapped back to its description.")


class NoulAnswer(contract.DecisionNoulAnswer):
    noul: float = Field(description="Probability the answer is yes. Near 1 strong yes, near 0 strong no, near 0.5 uncertain. Threshold it in code.")


class DecisionOutput(contract.DecisionOutput, BaseAppOutput):
    """The answers, keyed by question id within each kind."""
    choices: Dict[str, ChoiceAnswer] = Field(default_factory=dict, description="Choice answers by question id.")
    scores: Dict[str, ScoreAnswer] = Field(default_factory=dict, description="Score answers by question id.")
    nouls: Dict[str, NoulAnswer] = Field(default_factory=dict, description="Noul answers by question id.")
    model: str = Field(description="The model that answered.")
    input_tokens: int = Field(default=0, description="Input tokens the model read. Image tokens are included. Decision models write no output tokens.")

    @classmethod
    def from_answers(cls, answers: Dict[str, Dict[str, Any]], input_data: DecisionInput, *, model: str, input_tokens: int, **extra: Any) -> "DecisionOutput":
        """Build the output from answers in the form decision models share, keyed by
        question id: ``{"choice", "confidence", "probabilities"}`` for a choice,
        ``{"score", "confidence", "probabilities", "legend"}`` for a score and
        ``{"noul"}`` for a noul. Fails if a question has no answer. Meters the input
        tokens; ``extra`` sets fields a subclass adds."""
        asked = input_data.questions()
        missing = sorted(set(asked) - set(answers))
        if missing:
            raise RuntimeError(f"the model returned no answer for: {missing}")
        choices: Dict[str, ChoiceAnswer] = {}
        scores: Dict[str, ScoreAnswer] = {}
        nouls: Dict[str, NoulAnswer] = {}
        for qid, question in asked.items():
            answer = answers[qid]
            if question["type"] == "choice":
                choices[qid] = ChoiceAnswer(choice=answer["choice"], confidence=answer["confidence"], probabilities=answer["probabilities"])
            elif question["type"] == "score":
                scores[qid] = ScoreAnswer(
                    score=answer["score"],
                    normalized=answer["score"] / (len(question["criteria"]) - 1),
                    confidence=answer["confidence"],
                    probabilities=answer["probabilities"],
                    legend=answer["legend"],
                )
            else:
                nouls[qid] = NoulAnswer(noul=answer["noul"])
        return cls(
            choices=choices,
            scores=scores,
            nouls=nouls,
            model=model,
            input_tokens=input_tokens,
            output_meta=OutputMeta(inputs=[TextMeta(tokens=input_tokens)], outputs=[TextMeta(tokens=0)]),
            **extra,
        )
