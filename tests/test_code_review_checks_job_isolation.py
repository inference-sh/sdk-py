"""Pin code-review workflow: lint/tests in an isolated job, digest-locked actions.

Commit d5dff1bb moves pip install / flake8 / mypy / pytest out of the agent job
(Anthropic + MCP secrets) into a separate ``checks`` job with ``contents: read`` only.
Commit 7a50dd9 pins gh-aw container images and GitHub Actions via actions-lock.json.
"""

import json
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LOCK_YML = _REPO_ROOT / ".github" / "workflows" / "code-review.lock.yml"
_MD = _REPO_ROOT / ".github" / "workflows" / "code-review.md"
_ACTIONS_LOCK = _REPO_ROOT / ".github" / "aw" / "actions-lock.json"

_JOB_HEAD = re.compile(r"^  (\w+):\s*$", re.MULTILINE)
_ARTIFACT_NAME = "code-review-check-results"
_USES_SHA = re.compile(r"uses:\s*([\w./-]+)@([0-9a-f]{40})\b")


def _jobs_section(lock_text: str) -> str:
    m = re.search(r"^jobs:\n", lock_text, re.MULTILINE)
    assert m, "jobs: section missing from code-review.lock.yml"
    return lock_text[m.start():]


def _job_blocks(lock_text: str) -> dict[str, str]:
    section = _jobs_section(lock_text)
    matches = list(_JOB_HEAD.finditer(section))
    blocks: dict[str, str] = {}
    for i, match in enumerate(matches):
        name = match.group(1)
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(section)
        blocks[name] = section[start:end]
    return blocks


def _frontmatter(md_text: str) -> str:
    if not md_text.startswith("---\n"):
        return ""
    end = md_text.find("\n---\n", 4)
    assert end != -1, "code-review.md frontmatter not closed"
    return md_text[4:end]


class TestCodeReviewChecksJobIsolation:
    def test_source_declares_checks_job_before_agent_steps(self):
        fm = _frontmatter(_MD.read_text(encoding="utf-8"))
        assert "jobs:" in fm
        assert re.search(r"^\s{2}checks:\s*$", fm, re.MULTILINE), (
            "code-review.md must declare jobs.checks (source for gh aw compile)"
        )
        assert "persist-credentials: false" in fm
        assert _ARTIFACT_NAME in fm
        assert "pip install" in fm and "pytest" in fm

    def test_lock_checks_job_is_read_only_and_uploads_results(self):
        jobs = _job_blocks(_LOCK_YML.read_text(encoding="utf-8"))
        assert "checks" in jobs
        checks = jobs["checks"]
        assert re.search(r"permissions:\s*\n\s+contents:\s+read\b", checks)
        assert checks.count("permissions:") == 1
        assert _ARTIFACT_NAME in checks
        assert "upload-artifact@" in checks
        assert re.search(r"flake8", checks)
        assert re.search(r"pytest", checks)

    def test_lock_agent_downloads_checks_artifact_not_reruns_pytest(self):
        jobs = _job_blocks(_LOCK_YML.read_text(encoding="utf-8"))
        assert "agent" in jobs
        agent = jobs["agent"]
        assert re.search(r"needs:\s*\n(?:\s+- \w+\n)*\s+- checks\b", agent)
        assert _ARTIFACT_NAME in agent
        assert "download-artifact@" in agent
        assert "pytest" not in agent
        assert "flake8" not in agent
        assert "pip install" not in agent

    def test_checks_job_only_place_runs_dependency_checks(self):
        jobs = _job_blocks(_LOCK_YML.read_text(encoding="utf-8"))
        pytest_jobs = [name for name, block in jobs.items() if re.search(r"\bpytest\b", block)]
        flake_jobs = [name for name, block in jobs.items() if re.search(r"\bflake8\b", block)]
        assert pytest_jobs == ["checks"]
        assert flake_jobs == ["checks"]


class TestGhAwActionsLock:
    def test_container_images_carry_matching_digest_pins(self):
        data = json.loads(_ACTIONS_LOCK.read_text(encoding="utf-8"))
        containers = data.get("containers") or {}
        assert containers, "actions-lock.json must list gh-aw container images"
        for key, meta in containers.items():
            digest = meta.get("digest")
            pinned = meta.get("pinned_image")
            assert digest and digest.startswith("sha256:"), key
            assert pinned and f"@{digest}" in pinned, key
            assert key in pinned or meta.get("image") in pinned

    def test_lock_yml_action_uses_match_actions_lock_entries(self):
        lock_entries = json.loads(_ACTIONS_LOCK.read_text(encoding="utf-8"))["entries"]
        key_to_sha = {k.split("@", 1)[0]: v["sha"] for k, v in lock_entries.items()}
        mismatches: list[str] = []
        for ref, sha in _USES_SHA.findall(_LOCK_YML.read_text(encoding="utf-8")):
            if ref not in key_to_sha:
                continue
            if key_to_sha[ref] != sha:
                mismatches.append(f"{ref}: lock yml {sha[:12]}.. != actions-lock {key_to_sha[ref][:12]}..")
        assert mismatches == []