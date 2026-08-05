"""Regression guards for GitHub Actions workflow safety."""

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
