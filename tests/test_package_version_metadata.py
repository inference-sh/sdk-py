"""Guards editable-install version metadata vs pyproject (905d987).

Release bumps rewrite pyproject.toml but editable installs freeze importlib
metadata until reinstall; the skip decision must not mask real mismatches on
wheel/sdist installs.
"""

import json

import pytest


def should_skip_stale_editable_install(
    installed_version: str,
    expected_version: str,
    direct_url_json: str | None,
) -> bool:
    """True when a stale editable install explains a version mismatch."""
    if installed_version == expected_version:
        return False
    editable = bool(direct_url_json) and json.loads(direct_url_json).get(
        "dir_info", {}
    ).get("editable", False)
    return bool(editable)


@pytest.mark.parametrize(
    ("installed", "expected", "direct_url_json", "should_skip"),
    [
        ("0.28.0", "0.28.0", '{"dir_info": {"editable": true}}', False),
        ("0.27.4", "0.28.0", '{"dir_info": {"editable": true}}', True),
        ("0.27.4", "0.28.0", None, False),
        ("0.27.4", "0.28.0", "", False),
        ("0.27.4", "0.28.0", '{"dir_info": {"editable": false}}', False),
        ("0.27.4", "0.28.0", '{"dir_info": {"editable": false}}', False),
        ("0.27.4", "0.28.0", "{}", False),
    ],
)
def test_should_skip_stale_editable_install(
    installed, expected, direct_url_json, should_skip
):
    assert (
        should_skip_stale_editable_install(installed, expected, direct_url_json)
        is should_skip
    )


def test_bump_script_reinstalls_editable_after_pyproject_rewrite():
    """bump.sh must refresh metadata between sed and git add (905d987)."""
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / "scripts" / "bump.sh"
    text = script.read_text(encoding="utf-8")
    sed_marker = 'sed -i "s/^version ='
    git_add_marker = "git add pyproject.toml"
    start = text.index(sed_marker)
    end = text.index(git_add_marker, start)
    block = text[start:end]
    assert ".venv/bin/python" in block
    assert "-e ." in block and "pip install" in block
