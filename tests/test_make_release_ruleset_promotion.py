"""Pin ``make release`` ruleset-safe dev → main promotion (3dcfa7c).

GitHub branch rulesets block direct pushes to ``main``. The release recipe must
push ``dev`` and the version tag first, open (or tolerate an existing) promote
PR, then fast-forward ``main`` with retries—not a single ``git push`` that
includes ``HEAD:main`` alongside the tag.
"""

from pathlib import Path
import re

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MAKEFILE = _REPO_ROOT / "Makefile"


def _release_recipe(makefile_text: str) -> str:
    m = re.search(
        r"^release:\n((?:\t[^\n]+\n?)+)",
        makefile_text,
        re.MULTILINE,
    )
    assert m, "release: target missing from Makefile"
    return m.group(1)


def test_release_comments_document_pr_promotion_for_main():
    text = _MAKEFILE.read_text(encoding="utf-8")
    assert "main only moves through a PR" in text
    release = _release_recipe(text)
    assert "gh pr create" in release
    assert "--base main" in release
    assert "--head dev" in release


def test_release_no_longer_pushes_main_in_same_git_push_as_dev_and_tag():
    release = _release_recipe(_MAKEFILE.read_text(encoding="utf-8"))
    assert "HEAD:dev HEAD:main" not in release
    dev_push_lines = [line for line in release.splitlines() if "git push" in line]
    assert len(dev_push_lines) >= 2, "expect dev push and separate main promotion push"
    assert all("HEAD:main" not in line or "HEAD:dev" not in line for line in dev_push_lines)


def test_release_retries_main_fast_forward_after_pr_create():
    release = _release_recipe(_MAKEFILE.read_text(encoding="utf-8"))
    assert re.search(r"for i in 1 2 3 4 5 6", release)
    assert "git push origin HEAD:main" in release
    assert "sleep 5" in release


def test_release_still_requires_dev_branch_and_version_tag_at_head():
    release = _release_recipe(_MAKEFILE.read_text(encoding="utf-8"))
    assert 'git branch --show-current)" = dev' in release
    assert "pyproject.toml" in release
    assert "git rev-parse HEAD" in release
    assert 'git push origin HEAD:dev "$$VERSION"' in release
    assert "gh release create" in release