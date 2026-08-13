"""Regression guards for GitHub Actions workflow safety."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UPDATE_TYPES_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "update-types.yml"


def test_update_types_workflow_exists():
    assert UPDATE_TYPES_WORKFLOW.is_file()


def test_update_types_workflow_serializes_concurrent_runs():
    """Commit a9afec1: models may dispatch two type updates simultaneously.

    Without a concurrency group, parallel update-types runs can race on dev
    and produce conflicting commits.
    """
    text = UPDATE_TYPES_WORKFLOW.read_text(encoding="utf-8")
    assert "concurrency:" in text
    assert "group: update-types" in text
    assert "cancel-in-progress: false" in text


def test_update_types_workflow_avoids_inline_input_interpolation():
    """Commit a0116de: workflow_dispatch inputs must not be interpolated into run scripts.

    Inline ${{ inputs.* }} in shell blocks allows template injection from malicious
    dispatch payloads. Inputs must be passed through step env vars instead.
    """
    text = UPDATE_TYPES_WORKFLOW.read_text(encoding="utf-8")

    assert "FILE: ${{ inputs.file }}" in text
    assert "VERSION: ${{ inputs.version }}" in text
    assert "DEST: ${{ inputs.dest }}" in text

    run_scripts = re.findall(r"run: \|\n((?:      .+\n)+)", text)
    assert run_scripts, "expected at least one run script block"
    for script in run_scripts:
        assert "${{ inputs." not in script
    assert '"repos/inference-sh/models/contents/${FILE}?ref=${VERSION}"' in text
    assert 'git diff --quiet -- "$DEST"' in text
