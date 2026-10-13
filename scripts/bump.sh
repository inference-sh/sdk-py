#!/bin/sh
set -e

# Get new version via svu or manual bump
if command -v svu >/dev/null 2>&1; then
  new_tag=$(svu "$1")
else
  version=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' || echo "0.0.0")
  major=$(echo "$version" | cut -d. -f1)
  minor=$(echo "$version" | cut -d. -f2)
  patch=$(echo "$version" | cut -d. -f3)
  case "$1" in
    major) major=$((major + 1)); minor=0; patch=0 ;;
    minor) minor=$((minor + 1)); patch=0 ;;
    patch) patch=$((patch + 1)) ;;
    *) echo "Usage: $0 {major|minor|patch}"; exit 1 ;;
  esac
  new_tag="v$major.$minor.$patch"
fi

new_version="${new_tag#v}"

# Update pyproject.toml
sed -i "s/^version = \".*\"/version = \"${new_version}\"/" pyproject.toml

# Refresh the editable install so importlib metadata (User-Agent, version test)
# reports the new version without a manual `make install`.
if [ -x .venv/bin/python ]; then
  if command -v uv >/dev/null 2>&1; then
    uv pip install -q --python .venv/bin/python -e . --no-deps
  else
    .venv/bin/python -m pip install -q -e . --no-deps
  fi
fi

git add pyproject.toml
git commit -m "chore: bump version to $new_tag"
git tag "$new_tag"
echo "Tagged $new_tag (run make release to publish)"
