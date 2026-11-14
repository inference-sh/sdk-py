"""GitHub Actions checkout steps must not persist the runner git credential."""

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW_DIR = _REPO_ROOT / ".github" / "workflows"

_CHECKOUT_USE = re.compile(r"^\s*(?:-\s+)?uses:\s*actions/checkout@", re.MULTILINE)
_STEP_START = re.compile(r"^(\s*)-\s")
_PERSIST_FALSE = re.compile(r"persist-credentials:\s*false\b")

# Copilot setup still uses default checkout persist behavior; tighten when fixed.
_CHECKOUT_PERSIST_ALLOWLIST = frozenset({"copilot-setup-steps.yml"})


def _step_blocks(text: str) -> list[tuple[int, str]]:
    """Return (1-based start line, block text) for each actions/checkout step."""
    lines = text.splitlines()
    blocks: list[tuple[int, str]] = []
    i = 0
    while i < len(lines):
        if "actions/checkout@" not in lines[i] or "uses:" not in lines[i]:
            i += 1
            continue
        start = i
        while start >= 0 and not _STEP_START.match(lines[start]):
            start -= 1
        if start < 0:
            i += 1
            continue
        step_indent = len(_STEP_START.match(lines[start]).group(1))
        end = start + 1
        while end < len(lines):
            line = lines[end]
            if not line.strip():
                end += 1
                continue
            m = _STEP_START.match(line)
            if m and len(m.group(1)) == step_indent and end > start:
                break
            end += 1
        block = "\n".join(lines[start:end])
        blocks.append((start + 1, block))
        i = end
    return blocks


def _workflow_files() -> list[Path]:
    return sorted(_WORKFLOW_DIR.glob("*.yml"))


@pytest.mark.parametrize("workflow", _workflow_files(), ids=lambda p: p.name)
def test_actions_checkout_disables_persist_credentials(workflow: Path):
    if workflow.name in _CHECKOUT_PERSIST_ALLOWLIST:
        pytest.skip("workflow allowlisted until checkout persist-credentials is set")
    text = workflow.read_text(encoding="utf-8")
    if not _CHECKOUT_USE.search(text):
        pytest.skip("no actions/checkout in workflow")
    offenders = [
        f"{workflow.relative_to(_REPO_ROOT)}:{line}"
        for line, block in _step_blocks(text)
        if not _PERSIST_FALSE.search(block)
    ]
    assert offenders == []


def test_publish_and_bot_test_policy_disable_checkout_credentials():
    """Pin workflows touched by sec c763e6b (aikido 834731745, 834731749)."""
    for name in ("publish.yml", "bot-test-policy.yml"):
        path = _WORKFLOW_DIR / name
        text = path.read_text(encoding="utf-8")
        offenders = [
            line
            for line, block in _step_blocks(text)
            if not _PERSIST_FALSE.search(block)
        ]
        assert offenders == [], f"{name} checkout steps: {offenders}"