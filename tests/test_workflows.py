"""Regression guards for GitHub Actions workflow shell safety."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
UPDATE_TYPES_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "update-types.yml"


def _run_blocks(workflow_text: str) -> list[str]:
    """Return shell script bodies from ``run: |`` blocks in a workflow file."""
    blocks: list[str] = []
    lines = workflow_text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() == "run: |":
            i += 1
            script_lines: list[str] = []
            while i < len(lines) and (lines[i].startswith("          ") or lines[i].strip() == ""):
                script_lines.append(lines[i][10:] if lines[i].startswith("          ") else "")
                i += 1
            blocks.append("\n".join(script_lines).strip())
            continue
        i += 1
    return blocks


@pytest.fixture
def update_types_workflow_text() -> str:
    return UPDATE_TYPES_WORKFLOW.read_text(encoding="utf-8")


def test_update_types_workflow_exists():
    assert UPDATE_TYPES_WORKFLOW.is_file()


def test_update_types_run_blocks_avoid_input_template_injection(update_types_workflow_text):
    """Shell scripts must not interpolate workflow inputs via ${{ inputs.* }} (a3c44ac).

    GitHub Actions expands ${{ }} before the shell runs, so attacker-controlled
    dispatch inputs can inject arbitrary shell when referenced inside ``run:``.
    Inputs must be passed through ``env:`` and referenced as ``$VAR`` instead.
    """
    for block in _run_blocks(update_types_workflow_text):
        assert "${{ inputs." not in block, (
            "run script must not embed ${{ inputs.* }}; pass values through env: instead"
        )


def test_update_types_fetch_step_maps_inputs_to_env(update_types_workflow_text):
    """Fetch step binds dispatch inputs to FILE/VERSION/DEST env vars."""
    text = update_types_workflow_text
    fetch_section = text.split("- name: Fetch types from models", 1)[1].split(
        "- name: Commit if changed", 1
    )[0]
    assert "FILE: ${{ inputs.file }}" in fetch_section
    assert "VERSION: ${{ inputs.version }}" in fetch_section
    assert "DEST: ${{ inputs.dest }}" in fetch_section

    fetch_script = _run_blocks(fetch_section)[0]
    assert "${FILE}" in fetch_script or "$FILE" in fetch_script
    assert "${VERSION}" in fetch_script or "$VERSION" in fetch_script
    assert '"$DEST"' in fetch_script or "$DEST" in fetch_script


def test_update_types_commit_step_uses_env_dest_and_version(update_types_workflow_text):
    """Commit step references $DEST/$VERSION from env, not raw workflow inputs."""
    commit_section = update_types_workflow_text.split("- name: Commit if changed", 1)[1]
    assert "VERSION: ${{ inputs.version }}" in commit_section
    assert "DEST: ${{ inputs.dest }}" in commit_section

    commit_script = _run_blocks(commit_section)[0]
    assert '"$DEST"' in commit_script
    assert "models $VERSION" in commit_script
