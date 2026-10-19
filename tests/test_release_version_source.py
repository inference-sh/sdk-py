"""Release tooling must treat pyproject.toml as the version source of truth.

Commit eeb64f8 dropped git-describe/svu-based bumps because nearest tags can
belong to other packages or stale releases. These tests lock that contract.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BUMP_SH = REPO_ROOT / "scripts" / "bump.sh"
PYPROJECT_VERSION_RE = re.compile(r'^version = "(.*)"', re.MULTILINE)


def _write_pyproject(directory: Path, version: str) -> None:
    directory.joinpath("pyproject.toml").write_text(
        f'[project]\nname = "release-test"\nversion = "{version}"\n',
        encoding="utf-8",
    )


def _read_pyproject_version(directory: Path) -> str:
    text = directory.joinpath("pyproject.toml").read_text(encoding="utf-8")
    match = PYPROJECT_VERSION_RE.search(text)
    assert match, f"no version line in pyproject under {directory}"
    return match.group(1)


def _init_git_repo(directory: Path) -> None:
    subprocess.run(["git", "init"], cwd=directory, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "release-test@inference.sh"],
        cwd=directory,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "release-test"],
        cwd=directory,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "pyproject.toml"], cwd=directory, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=directory,
        check=True,
        capture_output=True,
    )


def _run_bump(directory: Path, kind: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(BUMP_SH), kind],
        cwd=directory,
        check=False,
        capture_output=True,
        text=True,
    )


def _makefile_release_version(pyproject: Path) -> str:
    """Mirror Makefile ``release`` target VERSION= extraction."""
    result = subprocess.run(
        ["sed", "-n", r's/^version = "\(.*\)"/\1/p', str(pyproject)],
        check=True,
        capture_output=True,
        text=True,
    )
    return f"v{result.stdout.strip()}"


def _tag_points_at_head(repo: Path, tag: str) -> bool:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tagged = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"{tag}^{{commit}}"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    if tagged.returncode != 0:
        return False
    return head == tagged.stdout.strip()


def _release_version_is_tagged_at_head(repo: Path) -> bool:
    """Mirror Makefile ``release`` guard: VERSION from pyproject must tag HEAD."""
    version = _makefile_release_version(repo / "pyproject.toml")
    return _tag_points_at_head(repo, version)


@pytest.mark.parametrize(
    ("kind", "start", "expected"),
    [
        ("patch", "2.3.4", "2.3.5"),
        ("minor", "2.3.4", "2.4.0"),
        ("major", "2.3.4", "3.0.0"),
    ],
)
def test_bump_increments_from_pyproject_not_nearest_git_tag(
    tmp_path: Path, kind: str, start: str, expected: str
) -> None:
    _write_pyproject(tmp_path, start)
    _init_git_repo(tmp_path)
    # Misleading nearest tag: old bump.sh / svu would follow this instead.
    subprocess.run(["git", "tag", "v99.0.0"], cwd=tmp_path, check=True, capture_output=True)

    result = _run_bump(tmp_path, kind)
    assert result.returncode == 0, result.stderr or result.stdout
    assert _read_pyproject_version(tmp_path) == expected


def test_bump_rejects_unknown_kind(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "1.0.0")
    _init_git_repo(tmp_path)

    result = _run_bump(tmp_path, "nope")
    assert result.returncode != 0
    assert "Usage" in (result.stderr or result.stdout)


def test_makefile_release_version_reads_pyproject(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "0.33.0")
    assert _makefile_release_version(tmp_path / "pyproject.toml") == "v0.33.0"


def test_release_tag_must_match_head(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "1.2.3")
    _init_git_repo(tmp_path)
    version = _makefile_release_version(tmp_path / "pyproject.toml")

    subprocess.run(["git", "tag", version], cwd=tmp_path, check=True, capture_output=True)
    assert _release_version_is_tagged_at_head(tmp_path)

    _write_pyproject(tmp_path, "1.2.4")
    subprocess.run(["git", "add", "pyproject.toml"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "bump pyproject without tag"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    assert not _release_version_is_tagged_at_head(tmp_path)
