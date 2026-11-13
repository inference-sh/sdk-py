"""Shipped SDK code must not rely on `assert` (stripped under `python -O`)."""

import ast
from pathlib import Path

import pytest

import inferencesh
from inferencesh import File


def test_no_assert_statements_in_package():
    root = Path(inferencesh.__file__).parent
    offenders = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        offenders += [f"{path.relative_to(root)}:{n.lineno}" for n in ast.walk(tree) if isinstance(n, ast.Assert)]
    assert offenders == []


def test_file_internal_helpers_raise_runtime_error_without_uri(tmp_path):
    path = tmp_path / "a.txt"
    path.write_text("x")
    f = File(uri=str(path))
    f.uri = None
    with pytest.raises(RuntimeError):
        f._decode_data_uri()
    with pytest.raises(RuntimeError):
        f._download_url()
