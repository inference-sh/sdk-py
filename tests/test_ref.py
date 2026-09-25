"""Ref.parse mirrors Go apitypes.Ref.Parse — regressions break catalog routing."""

import pytest

from inferencesh import Ref


@pytest.mark.parametrize(
    "raw, type_, namespace, name, version_id, function",
    [
        ("my-app", "", "", "my-app", "", ""),
        ("acme/widget", "", "acme", "widget", "", ""),
        ("app/acme/widget", "app", "acme", "widget", "", ""),
        ("skill/acme/search", "skill", "acme", "search", "", ""),
        ("knowledge/acme/docs", "knowledge", "acme", "docs", "", ""),
        ("agent/acme/helper", "agent", "acme", "helper", "", ""),
        ("acme/widget@abc123", "", "acme", "widget", "abc123", ""),
        ("app/acme/widget@latest", "app", "acme", "widget", "", ""),
        ("acme/widget:stream", "", "acme", "widget", "", "stream"),
        ("app/acme/widget@v2:run", "app", "acme", "widget", "v2", "run"),
        # Colon before @ is part of the name, not a function suffix.
        ("acme/weird:name@ver", "", "acme", "weird:name", "ver", ""),
    ],
)
def test_ref_parse_components(raw, type_, namespace, name, version_id, function):
    ref = Ref.parse(raw)
    assert ref.type == type_
    assert ref.namespace == namespace
    assert ref.name == name
    assert ref.version_id == version_id
    assert ref.function == function


def test_ref_parse_three_segments_without_known_type_is_opaque_name():
    """Unknown first segments are not treated as a type prefix — the path stays one name."""
    ref = Ref.parse("not-a-type/acme/widget")
    assert ref.type == ""
    assert ref.namespace == ""
    assert ref.name == "not-a-type/acme/widget"


@pytest.mark.parametrize(
    "raw, has_namespace",
    [
        ("solo", False),
        ("acme/widget", True),
        ("app/acme/widget", True),
    ],
)
def test_ref_try_parse_reports_namespace_presence(raw, has_namespace):
    ref, ok = Ref.try_parse(raw)
    assert ok is has_namespace
    assert ref.namespace == ("acme" if has_namespace else "")


def test_ref_formatting_helpers_and_str_roundtrip():
    ref = Ref.parse("app/acme/voice-loop@v3:stream")
    assert ref.is_typed() is True
    assert ref.full_name() == "acme/voice-loop"
    assert ref.qualified_name() == "app/acme/voice-loop"
    assert str(ref) == "app/acme/voice-loop@v3:stream"

    plain = Ref.parse("acme/widget")
    assert plain.is_typed() is False
    assert plain.qualified_name() == "acme/widget"
    assert str(plain) == "acme/widget"
