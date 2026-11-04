"""Optional-dependency pins in pyproject.toml (cc65411 / v0.38.10).

The ``images`` extra backs ``inferencesh.images.fit_image``; Pillow 13+ is
required after provider/format handling moved off older APIs. The ``async``
extra targets the same ``requires-python >= 3.11`` floor as the package, so
environment markers on aiohttp/aiofiles were removed as dead weight.
"""

from pathlib import Path

import tomllib

from packaging.requirements import Requirement

_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _optional_deps() -> dict[str, list[str]]:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    return data["project"]["optional-dependencies"]


def _requirement_name(spec: str) -> str:
    return Requirement(spec.split(";", 1)[0].strip()).name.lower()


def test_images_extra_requires_pillow_at_least_13():
    specs = _optional_deps()["images"]
    pillow_lines = [s for s in specs if _requirement_name(s) == "pillow"]
    assert len(pillow_lines) == 1, f"expected one pillow pin, got {pillow_lines!r}"
    req = Requirement(pillow_lines[0])
    assert req.name.lower() == "pillow"
    assert req.specifier.contains("13.0.0", prereleases=False)
    assert not req.specifier.contains("12.9.9", prereleases=False)


def test_async_extra_drops_python_version_markers():
    """Async deps ship only for Python versions we still support (>=3.11)."""
    specs = _optional_deps()["async"]
    assert specs == ["aiohttp>=3.14.3", "aiofiles>=23.2.1"]
    for line in specs:
        assert "python_version" not in line.lower()
        assert ";" not in line


def test_images_extra_is_single_pillow_dependency():
    """fit_image is the sole consumer; keep the extra minimal for installs."""
    specs = _optional_deps()["images"]
    assert len(specs) == 1
    assert _requirement_name(specs[0]) == "pillow"
